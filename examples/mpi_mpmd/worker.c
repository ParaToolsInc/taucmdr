#include <stdio.h>
#include <mpi.h>
#include <unistd.h>
#include "logging.h"

static void bar()
{
  msg("In bar()\n");
  usleep(10);
}

static void foo()
{
  msg("In foo()\n");
  usleep(100);
  bar();
  usleep(100);
}

int main(int argc, char * argv[])
{
  MPI_Init(&argc, &argv);
  init_logging();
  msg("Hello!\n");

  foo();

  msg("Goodbye!\n");
  return MPI_Finalize();
}
