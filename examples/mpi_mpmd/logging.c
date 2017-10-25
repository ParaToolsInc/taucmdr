#include <stdio.h>
#include <mpi.h>
#include "logging.h"

int WORLD_RANK;
int WORLD_SIZE;

void init_logging()
{
  MPI_Comm_rank(MPI_COMM_WORLD, &WORLD_RANK);
  MPI_Comm_size(MPI_COMM_WORLD, &WORLD_SIZE);
}

