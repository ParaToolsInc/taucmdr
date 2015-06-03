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

#if on srinath systems:
if $sv_sys; then
  echo "** making gcc5 a target with now bfd and libunwind"
  tau target create gcc5 --compilers=GNU --with-bfd=False --with-libunwind=False
fi

# Example applications
tau application create "ex-mm-serial"
tau application create "ex-mm-openmp" --openmp
tau application create "ex-mm-openmp-mpi" --openmp --mpi

# Example measurements
tau measurement create "ex-profile"
tau measurement create "ex-trace" --profile=F --trace=T
tau measurement create "ex-sample" --profile=F --sample=T
tau measurement create "p-keep" --keep-inst-files=T
tau measurement create ex-io --io-wrapper=T

# Set up example project
tau project create "ex-mm" \
  $target_name \
  ex-mm-serial ex-mm-openmp ex-mm-openmp-mpi \
  ex-profile ex-trace ex-sample ex-io

if $sv_sys; then
  echo "** making gcc target part of project"
  tau project edit ex-mm --add-targets gcc5
  tau project edit ex-mm --add-measurement p-keep
fi

tau dashboard
