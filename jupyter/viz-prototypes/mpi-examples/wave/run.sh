#! /bin/bash
#
tau mpicc -c -Wall wave_mpi.c
if [ $? -ne 0 ]; then
  echo "Compile error."
  exit
fi
#
tau mpicc wave_mpi.o -lm
if [ $? -ne 0 ]; then
  echo "Load error."
  exit
fi
#
rm wave_mpi.o
#
mv a.out wave_mpi
tau mpirun -np 4 ./wave_mpi 2>&1 | tee output.txt
if [ $? -ne 0 ]; then
  echo "Run error."
  exit
fi
rm wave_mpi
#
echo "Normal end of execution."
