c-----------------------------------------------------------------------
      program nekbone
      
      include 'SIZE'
      include 'TOTAL'
      include 'mpif.h'

      parameter (lxyz = lx1*ly1*lz1)
      parameter (lt=lxyz*lelt)


      call iniproc(mpi_comm_world)    ! has nekmpi common block

c     GET PLATFORM CHARACTERISTICS
      iverbose = 1
      call platform_timer(iverbose)   ! iverbose=0 or 1

      call exitt0

      end
c--------------------------------------------------------------
