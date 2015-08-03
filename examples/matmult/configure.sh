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
user_name="`users`"

# Example applications
tau application create "ex-matmult-serial"
tau application create "ex-matmult-mpi" --mpi
tau application create "ex-matmult-openmp" --openmp
tau application create "ex-matmult-openmp-mpi" --openmp --mpi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --sample=T
tau measurement create "p-keep" --keep-inst-files=T

# Set up example project
tau project create "ex-mm" \
  $target_name \
  ex-matmult-serial ex-matmult-openmp ex-matmult-openmp-mpi \
  ex-profile ex-trace ex-sample

tau dashboard
