#include <stdio.h>
#include <stddef.h>
#include <mpi.h>
#include "logging.h"

int main(int argc, char * argv[])
{
  MPI_Init(&argc, &argv);
  init_logging();

  msg("Hello!\n");

  MPI_Finalize();
  return 0;
}
