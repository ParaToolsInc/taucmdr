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

# Example applications
tau application create "ex-mm-serial"
tau application create "ex-mm-openmp" --openmp
tau application create "ex-mm-openmp-mpi" --openmp --mpi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --profile=F --sample=T

# Set up example project 
tau project create "ex-mm" \
  $target_name \
  ex-mm-serial ex-mm-openmp ex-mm-openmp-mpi \
  ex-profile ex-trace ex-sample

