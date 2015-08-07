      subroutine rzeroi(a,n,start,fin)
        implicit none
  
        real a(n)
        integer n, i, start, fin

        do i = start, fin
          a(i) = 0.0
        end do 

        return
      end subroutine

c----------------------------------------------------------

      subroutine copyi(a,b,n, start, fin)
        implicit none

        real a(n),b(n)
        integer n, i, start, fin

        do i=start,fin
          a(i)=b(i)
        enddo

        return
      end subroutine

c----------------------------------------------------------

      subroutine glsc3i(val,a,b,mult,n,find,lind)
      implicit none

      real val,a(n),b(n),mult(n)
      real tsum,psum,work(1)
      integer n,find,lind
      integer i

      save psum

      tsum = 0.0
      do i=find, lind
         tsum = tsum + a(i)*b(i)*mult(i)
      end do

      if (find == 1) psum = 0.0

c$OMP BARRIER
c$OMP CRITICAL
      psum = psum + tsum
c$OMP END CRITICAL

c$OMP BARRIER
c$OMP MASTER
      call gop(psum,work,'+  ',1)
      val = psum
c$OMP END MASTER
c$OMP BARRIER

      return
      end subroutine

c----------------------------------------------------------

      subroutine solveMi(z,r,n,start,fin)
      implicit none

      real z(n),r(n)
      integer n,start,fin

      call copyi(z,r,n,start,fin) 

      return
      end

c----------------------------------------------------------

      subroutine add2s1i(a,b,c1,n,start,fin)
      implicit none

      real a(n),b(n),c1
      integer n,start,fin
      integer i

      do i= start, fin
        a(i)=c1*a(i)+b(i)
      end do

      return
      end subroutine

c----------------------------------------------------------

      subroutine add2s2i(a,b,c1,n,start,fin)
      implicit none
 
      real a(n),b(n),c1
      integer n,start,fin
      integer i

      do i= start,fin
        a(i)=a(i)+c1*b(i)
      end do

      return
      end subroutine
