program testOverhead

  implicit none

  integer :: i,i_final

    i_final=5.*(10&&7) ! 50million calls

  do i = 1, i_final, 1
    CALL TAU_START("blank")
    CALL TAU_STOP("blank")
  end do

end program
