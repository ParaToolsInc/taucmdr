#!/bin/bash

if ! which tau >/dev/null 2>&1 ; then
  echo "ERROR: 'tau' not found in PATH"
  exit 1
fi

# Show commands as executed
set +x

# Example targets
#tau target create stampede-mic --host-arch mic --compilers MPI
tau target create stampede-mic --host-arch KNL --compilers Intel

# Example applications
tau application create "ex-matmult-mpi" --mpi
tau application create "ex-matmult-openmp" --openmp
tau application create "ex-matmult-openmp-mpi" --openmp --mpi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --profile=T --sample=T
tau measurement create "p-keep" --keep-inst-files=T
tau measurement create "no-io" --io=F

# Set up example project
tau project create "ex-matmult" \
  stampede-mic \
  ex-matmult-openmp ex-matmult-openmp-mpi \
  ex-profile ex-trace ex-sample p-keep no-io

tau project edit ex-matmult --add-targets stampede-mic
tau dashboard

#tau project select ex-matmult stampede-mic ex-matmult-openmp-mpi ex-profile
tau project select ex-matmult stampede-mic ex-matmult-openmp ex-profile

