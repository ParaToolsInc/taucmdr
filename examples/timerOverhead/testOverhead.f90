program testOverhead

  implicit none

  integer :: i,i_final

    i_final=5.*(10**7) ! 50million calls

  do i = 1, i_final, 1
    CALL TAU_START("in loop")
    CALL TAU_STOP("in loop")
  end do

    CALL TAU_START("out loop")
    CALL TAU_STOP("out loop")
end program
