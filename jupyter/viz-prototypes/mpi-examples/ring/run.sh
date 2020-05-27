#! /bin/bash
#
tau mpicc -c -Wall ring_mpi.c
if [ $? -ne 0 ]; then
  echo "Compile error."
  exit
fi
#
tau mpicc ring_mpi.o
if [ $? -ne 0 ]; then
  echo "Load error."
  exit
fi
mv a.out ring_mpi
#
tau mpirun -np 8 ./ring_mpi 2>&1 | tee output.txt
if [ $? -ne 0 ]; then
  echo "Run error."
  exit
fi
rm ring_mpi
#
echo "Normal end of execution."

