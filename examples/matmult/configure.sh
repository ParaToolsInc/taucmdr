#!/bin/bash

if ! which tau >/dev/null 2>&1 ; then
  echo "ERROR: 'tau' not found in PATH"
  exit 1
fi

# Show commands as executed
set +x

# Example targets
target_name="ex-`echo $HOSTNAME | cut -d. -f1`"
tau target create "$target_name"
tau target create ${target_name}-mpi
user_name="`users`"


# Example applications
tau application create "ex-matmult-serial"
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
  $target_name \
  ${target_name}-mpi \
  ex-matmult-serial ex-matmult-openmp ex-matmult-openmp-mpi \
  ex-profile ex-trace ex-sample p-keep no-io

if [[ $target_name == *"Paratools-SV"* ]]; then
  echo "** making gcc target and part of project"
  source /Users/srinathv/gnu5Bin/linkGccs.source
  tau target create gcc5 --compilers MPI
  tau project edit ex-matmult --add-targets gcc5
fi


tau dashboard
