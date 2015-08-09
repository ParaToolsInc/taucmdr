#ifdef TIMERS
#define NBTIMER(a) a = dnekclock()
#define STIMER(a) a = dnekclock_sync()
#define ACCUMTIMER(b,a) b = b + (dnekclock()- a )
#else
#define NBTIMER(a)
#define STIMER(a)
#define ACCUMTIMER(a,b)
#endif


c-----------------------------------------------------------------------
      subroutine cg(x,f,g,c,r,w,p,z,n,niter,flop_cg)
      include 'SIZE'
      include 'TIMER'

c     Solve Ax=f where A is SPD and is invoked by ax()
c
c     Output:  x - vector of length n
c
c     Input:   f - vector of length n
c     Input:   g - geometric factors for SEM operator
c     Input:   c - inverse of the counting matrix
c
c     Work arrays:   r,w,p,z  - vectors of length n
c
c     User-provided ax(w,z,n) returns  w := Az,  
c
c     User-provided solveM(z,r,n) ) returns  z := M^-1 r,  
c
      parameter (lt=lx1*ly1*lz1*lelt)
c     real ur(lt),us(lt),ut(lt)

c     parameter (lxyz=lx1*ly1*lz1)
c     real ur(lxyz),us(lxyz),ut(lxyz),wk(lxyz)

      real x(n),f(n),r(n),w(n),p(n),z(n),g(1),c(n)
      real rnorminit, fbeta, fpap, falpha, frnorm

      integer thread, numth, find, lind, fel, lel
      integer omp_get_thread_num, omp_get_num_threads
      integer fiter, tmt

      pap = 0.0

c     set machine tolerances
      one = 1.
      eps = 1.e-20
      if (one+eps .eq. one) eps = 1.e-14
      if (one+eps .eq. one) eps = 1.e-7

      rtz1=1.0
      miter = niter

c$OMP PARALLEL DEFAULT(shared) PRIVATE(thread,numth,find,lind,iter,
c$OMP&  fel,lel,rtz2,beta,alpha,alphm,rlim2,rtr0)

      thread = 0
      numth = 1
#ifdef _OPENMP
      thread = omp_get_thread_num()
      numth = omp_get_num_threads()
#endif
      tmt = thread + 1

      if (numth < nelt) then
        fel = (thread*nelt)/numth + 1
        lel = ((thread+1)*nelt)/numth
      else
        if (thread < nelt) then
          fel = thread + 1
          lel = fel
        else
          fel = nelt+1
          lel = nelt
        end if
      end if

      find = (fel-1) *(nx1*ny1*nz1)+1
      lind = lel * (nx1*ny1*nz1)

      NBTIMER(ttemp1)
      call rzeroi(x,n,find,lind)
      call copyi(r,f,n,find,lind)
      ACCUMTIMER(tzc(tmt), ttemp1)

      if (thread == 0) call mask (r)   ! Zero out Dirichlet conditions

      NBTIMER(ttemp1)
      call glsc3i(rnorminit,r,c,r,n,find,lind)
      ACCUMTIMER(tglsc3(tmt), ttemp1)


      do iter=1,miter
         NBTIMER(ttemp1)
         call solveMi(z,r,n,find,lind)    ! preconditioner here
         ACCUMTIMER(tzc(tmt), ttemp1)

         rtz2=rtz1                                                       ! OPS
         NBTIMER(ttemp1)
         call glsc3i(rtz1,r,c,z,n,find,lind)
         ACCUMTIMER(tglsc3(tmt), ttemp1)

         beta = rtz1/rtz2
         if (iter.eq.1) beta=0.0

         NBTIMER(ttemp1)
         call add2s1i(p,z,beta,n,find,lind)                              ! 2n
         ACCUMTIMER(tadd2sx(tmt), ttemp1)

         NBTIMER(ttemp1)
         call axi(w,p,g,n,fel,lel,find,lind)                             ! flopa
         ACCUMTIMER(tax(tmt), ttemp1)

         NBTIMER(ttemp1)
         call glsc3i(pap, w,c,p,n,find,lind)                             ! 3n
         ACCUMTIMER(tglsc3(tmt), ttemp1)

         alpha=rtz1/pap
         alphm=-alpha

         NBTIMER(ttemp1)
         call add2s2i(x,p,alpha,n,find,lind)                             ! 2n
         call add2s2i(r,w,alphm,n,find,lind)                             ! 2n
         ACCUMTIMER(tadd2sx(tmt), ttemp1)

         NBTIMER(ttemp1)
         call  glsc3i(rtr, r,c,r,n,find,lind)                            ! 3n
         ACCUMTIMER(tglsc3(tmt), ttemp1)

         if (iter.eq.1) rlim2 = rtr*eps**2
         if (iter.eq.1) rtr0  = rtr
         rnorm = sqrt(rtr)

      enddo

      if (thread == 0) then
        fiter = iter
        fbeta = beta
        falpha= alpha
        fpap  = pap
        frnorm = rnorm
      end if

c$OMP END PARALLEL

    6    format('cg:',i4,1p4e12.4)

      if (nid.eq.0) then
        write(6,6) 0,sqrt(rnorminit)
        write(6,6) fiter,frnorm,falpha,fbeta,fpap
      end if

      flop_cg = flop_cg + (fiter-1)*15.0*n + 3.0*n

      return
      end
c-----------------------------------------------------------------------
      subroutine solveM(z,r,n)
      real z(n),r(n)

      call copy(z,r,n)

      return
      end
c-----------------------------------------------------------------------
      subroutine axi(w,u,gxyz,n,fel,lel,find,lind) ! Matrix-vector product: w=A*u

      include 'SIZE'
      include 'TOTAL'
      include 'TIMER'

      parameter (lxyz=lx1*ly1*lz1)
      real w(nx1*ny1*nz1,nelt),u(nx1*ny1*nz1,nelt)
      real gxyz(2*ldim,nx1*ny1*nz1,nelt)
      parameter (lt=lx1*ly1*lz1*lelt)

      integer fel, lel, find, lind
      integer e,thread, tmt, omp_get_thread_num

      thread = 0
#ifdef _OPENMP
      thread = omp_get_thread_num()
#endif
      tmt = thread + 1

      NBTIMER(ttemp2)
      do e= fel, lel
         call ax_e( w(1,e),u(1,e),gxyz(1,1,e))
      enddo
      ACCUMTIMER(taxe(tmt),ttemp2)

      NBTIMER(ttemp2)
      call gs_op(gsh,w,1,1,0)  ! Gather-scatter operation  ! w   = QQ  w
      ACCUMTIMER(tgsop(tmt),ttemp2)
                                                           !            L
      NBTIMER(ttemp2)
      call add2s2i(w,u,.1,n,find,lind)
      ACCUMTIMER(tadd2s2(tmt),ttemp2)

      if (find == 1) then
        call mask(w)             ! Zero out Dirichlet conditions
        nxyz=nx1*ny1*nz1
        flop_a = flop_a + (19*nxyz+12*nx1*nxyz)*nelt
      end if

      return
      end
c-------------------------------------------------------------------------
      subroutine ax1(w,u,n)
      include 'SIZE'
      real w(n),u(n)
      real h2i
  
      h2i = (n+1)*(n+1)  
      do i = 2,n-1
         w(i)=h2i*(2*u(i)-u(i-1)-u(i+1))
      enddo
      w(1)  = h2i*(2*u(1)-u(2  ))
      w(n)  = h2i*(2*u(n)-u(n-1))

      return
      end
c-------------------------------------------------------------------------
      subroutine ax_e(w,u,g) ! Local matrix-vector product

      include 'SIZE'
      include 'TOTAL'

      parameter (lxyz=lx1*ly1*lz1)
      real w(lxyz),u(lxyz),g(2*ldim,lxyz)

      real ur(nx1*ny1*nz1),us(nx1*ny1*nz1),ut(nx1*ny1*nz1)

      nxyz = nx1*ny1*nz1
      n    = nx1-1

      call local_grad3(ur,us,ut,u,n,dxm1,dxtm1)

      do i=1,nxyz
         wr = g(1,i)*ur(i) + g(2,i)*us(i) + g(3,i)*ut(i)
         ws = g(2,i)*ur(i) + g(4,i)*us(i) + g(5,i)*ut(i)
         wt = g(3,i)*ur(i) + g(5,i)*us(i) + g(6,i)*ut(i)
         ur(i) = wr
         us(i) = ws
         ut(i) = wt
      enddo

      call local_grad3_t(w,ur,us,ut,n,dxm1,dxtm1)

      return
      end
c-------------------------------------------------------------------------
      subroutine local_grad3(ur,us,ut,u,n,D,Dt)
c     Output: ur,us,ut         Input:u,n,D,Dt
      real ur(0:n,0:n,0:n),us(0:n,0:n,0:n),ut(0:n,0:n,0:n)
      real u (0:n,0:n,0:n)
      real D (0:n,0:n),Dt(0:n,0:n)
      integer e

      m1 = n+1
      m2 = m1*m1

      call mxm(D ,m1,u,m1,ur,m2)
      do k=0,n
         call mxm(u(0,0,k),m1,Dt,m1,us(0,0,k),m1)
      enddo
      call mxm(u,m2,Dt,m1,ut,m1)

      return
      end
c-----------------------------------------------------------------------
      subroutine local_grad3_t(u,ur,us,ut,N,D,Dt)
c     Output: ur,us,ut         Input:u,N,D,Dt
      real u (0:N,0:N,0:N)
      real ur(0:N,0:N,0:N),us(0:N,0:N,0:N),ut(0:N,0:N,0:N)
      real D (0:N,0:N),Dt(0:N,0:N)
      real w (0:N,0:N,0:N)
      integer e

      m1 = N+1
      m2 = m1*m1
      m3 = m1*m1*m1

      call mxm(Dt,m1,ur,m1,u,m2)

      do k=0,N
         call mxm(us(0,0,k),m1,D ,m1,w(0,0,k),m1)
      enddo
      call add2(u,w,m3)

      call mxm(ut,m2,D ,m1,w,m1)
      call add2(u,w,m3)

      return
      end
c-----------------------------------------------------------------------
      subroutine mask(w)   ! Zero out Dirichlet conditions
      include 'SIZE'
      real w(1)

      if (nid.eq.0) w(1) = 0.  ! suitable for solvability

      return
      end
c-----------------------------------------------------------------------
