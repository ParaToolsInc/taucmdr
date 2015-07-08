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

sv_sys=false
if [[ $target_name == *"Para"* ]] && [[ $user_name == *"srinath"* ]]
then
  sv_sys=true;
  echo "This is a srinathv Paratools system"
fi

has_mic=false
if [[ $MIC_ENV_PREFIX == *"MIC"* ]]
then
  has_mic=true;
  echo "This machine has MICs."
fi

#if on srinath systems:
if $sv_sys; then
  echo "** making gcc5 a target with no bfd and libunwind"
  tau target create gcc5 --compilers=GNU --with-bfd=False --with-libunwind=False
fi

if $has_mic; then
  echo "** making a mic target with no bfd and libunwind"
  tau target create intel-mic --compilers=Intel --with-bfd=False --with-libunwind=False --with-mic=True
fi

# Example applications
tau application create "ex-matmult-serial"
tau application create "ex-matmult-mpi" --mpi
tau application create "ex-matmult-openmp" --openmp
tau application create "ex-matmult-openmp-mpi" --openmp --mpi

if $has_mic; then
  tau application create "ex-matmult-mic-mpi" --mic --mpi
fi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --profile=F --sample=T
tau measurement create "p-keep" --keep-inst-files=T
tau measurement create ex-io --io-wrapper=T

# Set up example project
tau project create "ex-mm" \
  $target_name \
  ex-matmult-serial ex-matmult-openmp ex-matmult-openmp-mpi \
  ex-profile ex-trace ex-sample ex-io

if $sv_sys; then
  echo "** making gcc target part of project"
  tau project edit ex-mm --add-targets gcc5
  tau project edit ex-mm --add-measurement p-keep
fi

if $has_mic; then
  echo "** making a mic project"
  tau project create ex-mic-matmult intel-mic ex-matmult-mic-mpi ex-profile
fi

tau dashboard
