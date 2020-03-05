!**********************************************************************
!     matmult.f90 - simple matrix multiply implementation
!************************************************************************

program main
  implicit none

  include 'mpif.h'

  integer, parameter :: MATSIZE = 1000
  integer, parameter :: MASTER = 0

  real(kind=8), dimension(:,:),ALLOCATABLE :: a,b,c
  real(kind=8), dimension(:), ALLOCATABLE :: buffer, answer

  integer :: myid, maxpe, ierr, provided
  integer, dimension(MPI_STATUS_SIZE) :: stat

  integer :: i, j, numsent, sender
  integer :: answertype, row, flag
  integer :: nthreads, tid, omp_get_num_threads, omp_get_thread_num

  continue

  allocate(a(MATSIZE,MATSIZE),b(MATSIZE,MATSIZE),c(MATSIZE,MATSIZE))
  allocate(buffer(MATSIZE),answer(MATSIZE))

  call MPI_Init_thread(MPI_THREAD_FUNNELED, provided, ierr)
  call MPI_Comm_rank(MPI_COMM_WORLD, myid, ierr)
  call MPI_Comm_size(MPI_COMM_WORLD, maxpe, ierr)
  write(*,'("Process ",I0," of ",I0," is active")') myid, maxpe

  !$omp parallel private(tid,nthreads) default(shared)
  tid = omp_get_thread_num()
  write(*,'("hello world from thread ",I0)') tid
  if (tid == 0) then
    nthreads = omp_get_num_threads()
    write(*, '("number of threads = ",I0)') nthreads
  end if
  !$omp end parallel

  if ( myid == master ) then
    ! master initializes and then dispatches
    ! initialize a and b
    call initialize(MATSIZE, a, b)
    numsent = 0

    ! send b to each other process
    do i = 1,MATSIZE
      call MPI_Bcast(b(1,i), MATSIZE, MPI_DOUBLE_PRECISION, master, &
                     MPI_COMM_WORLD, ierr)
    end do

    ! send a row of a to each other process; tag with row number
    do i = 1,maxpe-1
      do j = 1,MATSIZE
        buffer(j) = a(i,j)
      end do
      call MPI_Send(buffer, MATSIZE, MPI_DOUBLE_PRECISION, i, i, &
                    MPI_COMM_WORLD, ierr)
      numsent = numsent+1
    end do

    do i = 1,MATSIZE
      call MPI_Recv(answer, MATSIZE, MPI_DOUBLE_PRECISION, &
                    MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &
                    stat, ierr)
      sender = stat(MPI_SOURCE)
      answertype = stat(MPI_TAG)
      c(answertype,:) = answer(:)

      if (numsent < MATSIZE) then
        buffer(:) = a(numsent+1,:)
        call MPI_Send(buffer, MATSIZE, MPI_DOUBLE_PRECISION, sender, &
                      numsent+1, MPI_COMM_WORLD, ierr)
        numsent = numsent+1
      else
        call MPI_Send(1.0, 1, MPI_DOUBLE_PRECISION, sender, 0, &
                      MPI_COMM_WORLD, ierr)
      endif
    end do

    ! print out one element of the answer
    write(*, '("c(",I0,",",I0,") = ",ES24.14)') MATSIZE, MATSIZE, c(MATSIZE,MATSIZE)
  else
    ! workers receive B, then compute rows of C until done message
    do i = 1,MATSIZE
      call MPI_Bcast(b(1,i), MATSIZE, MPI_DOUBLE_PRECISION, master, &
                     MPI_COMM_WORLD, ierr)
    end do
    flag = 1
    do while (flag /= 0)
      call MPI_Recv(buffer, MATSIZE, MPI_DOUBLE_PRECISION, master,  &
                    MPI_ANY_TAG, MPI_COMM_WORLD, stat, ierr)
      row = stat(MPI_TAG)
      flag = row
      if (flag /= 0) then
        ! multiply the matrices here using C(i,j) += sum (A(i,k)* B(k,j))
        call multiply_matrices(MATSIZE, answer, buffer, b)
        call MPI_Send(answer, MATSIZE, MPI_DOUBLE_PRECISION, master, &
                      row, MPI_COMM_WORLD, ierr)
      endif
    end do
  endif

  call MPI_FINALIZE(ierr)

!--------------------------------------------------------------------------------
contains
!--------------------------------------------------------------------------------

  subroutine initialize(n, a, b)
    implicit none
    integer, intent(in) :: n
    real(kind=8), dimension(n,n), intent(out) :: a, b
    integer :: i, j

    !$omp parallel private(i,j) default(shared)
    !$omp do
    do i = 1,n
      do j = 1,n
        a(j,i) = i
      end do
    end do
    !$omp end do nowait
    !$omp do
    do i = 1,n
      do j = 1,n
        b(j,i) = i
      end do
    end do
    !$omp end do nowait
    !$omp end parallel
  end subroutine initialize


  subroutine multiply_matrices(n, answer, buffer, b)
    implicit none
    integer, intent(in) :: n
    real(kind=8), dimension(n), intent(inout) :: answer
    real(kind=8), dimension(n), intent(in) :: buffer
    real(kind=8), dimension(n,n) :: b
    integer :: i, j

    !$omp parallel do private(i,j) default(shared)
    do i=1,n
      answer(i) = 0
      do j=1,MATSIZE
        answer(i) = answer(i) + buffer(j)*b(j,i)
      end do
    end do
    !$omp end parallel do
  end subroutine multiply_matrices

end program main
