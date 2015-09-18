	PROGRAM REDUCTION
               INCLUDE 'shmem.fh'
               REAL VALUES, SUM
               COMMON /C/ VALUES
               REAL WORK
               INTEGER MYPE, NPES
               CALL START_PES(0)
               NPES = SHMEM_N_PES()
               MYPE = SHMEM_MY_PE()
               VALUES = SHMEM_MY_PE()
               CALL SHMEM_BARRIER_ALL                  ! Synchronize all PEs
               SUM = 0.0
               DO I = 0,NPES-1
                  CALL SHMEM_GET(WORK, VALUES, 1, I)   ! Get next value
                  SUM = SUM + WORK                     ! Sum it
               ENDDO
               CALL SHMEM_BARRIER_ALL
               PRINT*,'PE ',MYPE,' COMPUTED       SUM=',SUM
       END

