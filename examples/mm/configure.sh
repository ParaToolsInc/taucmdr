#!/bin/bash

if ! which tau >/dev/null 2>&1 ; then
  echo "ERROR: 'tau' not found in PATH"
  exit 1
fi

# Show commands as executed
set +x

# Example targets
tau target create localhost

# Example applications
tau application create "ex-mm-serial"
tau application create "ex-mm-openmp" --openmp
tau application create "ex-mm-openmp-mpi" --openmp --mpi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --source-inst=never --compiler-inst=never --sample=T

# Set up example project
tau project create "ex-mm" localhost ex-mm-serial ex-mm-openmp ex-mm-openmp-mpi ex-profile ex-trace ex-sample
tau project select ex-mm ex-mm-openmp ex-profile
  
tau dashboard
