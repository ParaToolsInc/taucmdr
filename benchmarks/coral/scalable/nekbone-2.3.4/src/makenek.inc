# This include file is used by the makenek script
# to automatically create a makefile for Nek5000 
# (c) 2008,2009,2010 UCHICAGO ARGONNE, LLC
# ------------------------------------------------

echo "makenek - automatic build tool for Nek5000"

if [ "$PPLIST" == "?" ]; then
  echo "available pre-processor symbols:" 
  echo "  BG        enable Blue Gene optimizations (BG/L and BG/P)"
  echo "  K10_MXM   use optimized MxM kernel for AMD Family 10h processors" 
  exit 1
fi


if [ "$1" = "clean" ]; then
  make clean
  exit 0
fi

NOCOMPILE=0
if [ "$2" == "-nocompile" ]; then
  NOCOMPILE=1
fi 

CASENAME=$1
CASEDIR=`pwd`
APATH_SRC=`cd $SOURCE_ROOT; pwd`
SOURCE_ROOT=$APATH_SRC

# do some basic checks
if [ "$CASEDIR" == "$SOURCE_ROOT" ]; then
   echo "FATAL ERROR: Working directory has to be different from the source!"
   exit 1
fi

if [ ! -f SIZE ]; then
   echo "FATAL ERROR: Cannot find SIZE!"
   exit 1
fi

if [ ! -f ./makefile.template ]; then
  echo "FATAL ERROR: Cannot find ./makefile.template!"
  exit 1
fi

# test F77 compiler
which `echo $F77 | awk '{print $1}'` 1>/dev/null
if [ $? -ne 0 ]; then
  echo "FATAL ERROR: Cannot find $F77!"
  exit 1
fi
\rm test_f77.o 2>/dev/null
# basic compiler test
cat > test_f77.f << _ACEOF
      subroutine test
      end
_ACEOF
$F77 -c test_f77.f >/dev/null
if [ ! -f test_f77.o ]; then
  echo "FATAL ERROR: Basic compiler test for $F77 failed!"
  exit 1
fi
\rm test_f77.* 2>/dev/null

# test C compiler
which `echo $CC | awk '{print $1}'` 1>/dev/null
if [ $? -ne 0 ]; then
  echo "FATAL ERROR: Cannot find $CC!"
  exit 1
fi
\rm test_cc.o 2>/dev/null
cat > test_cc.c << _ACEOF
      void function(){}
_ACEOF
$CC -c test_cc.c 1>/dev/null
if [ ! -f test_cc.o ]; then
  echo "FATAL ERROR: Basic compiler test for $CC failed!"
  exit 1
fi
\rm test_cc.* 2>/dev/null

# initial clean-up
rm -f nekbone 2>/dev/null

# Check ptr size
cat > tmp.c << _ACEOF
#include <stdlib.h>
#include <stdio.h>
int main()
{
  int *p;printf("%li\n",sizeof(p));
}
_ACEOF
$CC tmp.c 2>&1>/dev/null
ptrSize=`./a.out`
rm tmp.c a.out
if [ "$ptrSize" == "8" ]
then
  PPLIST="${PPLIST} PTRSIZE8"
fi

# Check if the compiler adds an underscore to external functions
UNDERSCORE=false
cat > test_underscore.f << _ACEOF
      subroutine underscore_test
        call byte_write
      end
_ACEOF
$F77 -c test_underscore.f 2>&1 >/dev/null 
nm test_underscore.o | grep byte_write_ 1>/dev/null
if [ $? -eq 0 ] 
then
  UNDERSCORE=true
fi
\rm test_underscore.* 2>/dev/null

F77comp=$F77
# mpi-wrappers?
echo $F77comp | grep -i mp >/dev/null
if [ $? -eq 0 ]; then   
# trying to figure out which compiler we're using 
  F77ok=0
  F77comp_=`$F77 -showme 2>/dev/null 1>.tmp` 
  F77comp=`cat .tmp | awk '{print $1}' | awk -F/ '{print $NF}'`
  if [ -f "`which $F77comp 2>/dev/null`" ]; then
    F77ok=1
  else
    F77comp_=`$F77 -show 2>/dev/null 1>.tmp`
    F77comp=`cat .tmp | awk '{print $1}' | awk -F/ '{print $NF}'`
    if [ -f "`which $F77comp 2>/dev/null`" ]; then
      F77ok=1
    fi
  fi
else
  F77comp=`echo $F77 | awk '{print $1}'`
  if [ -f "`which $F77comp 2>/dev/null`" ]; then
    F77ok=1
  fi
fi
\rm -f .tmp
if [ $F77ok -eq 0 ]; then
  F77comp="unknown"
fi

# assign F77 compiler specific flags
case $F77comp in
  *pgf*)        P="-r8 -Mpreprocess"
               ;;
  *gfortran*)   P="-fcray-pointer -fdefault-real-8 -x f77-cpp-input"
               ;;
  *ifort*)      P="-r8 -fpconstant -fpp"
               ;;
  *pathf*)      P="-r8 -cpp -fno-second-underscore"
               ;;
  *xlf*)       P="-qrealsize=8 -qdpc=e -qsuffix=cpp=f"
               PPPO="-WF,"
               F77="${F77} -qsuppress=cmpmsg"
               ;;
  *ftn*)        P="-r8 -Mpreprocess"
               ;;
  *sunf*)       P="-r8const -xtypemap=real:64 -fpp"
               ;;
  *open*)       P="-r8 -cpp -fno-second-underscore"
               ;;
  *)  echo "ERROR: Unable to detect compiler!"
      echo "        - don't know how to promote datatype REAL to 8 bytes"
      echo "        - don't know how to invoke the C pre-processor (CPP) before compilation"
      echo "       Please edit the makefile and specify the requested compiler flags using the P variable."
      echo ""
      P="<specify your compiler flags here>"
      NOCOMPILE=1
      read;;
esac
export PPPO

# set preprocessor symbols
if [ "$IFMPI" == "false" -o "$IFMPI" == "no" ]; then
  IFMPI=false
else
  # default
  IFMPI=true
  PPLIST="${PPLIST} MPI"
fi
export IFMPI

# Check size of long int
cat > tmp.c << _ACEOF
#include <stdlib.h>
#include <stdio.h>
int main()
{
  int i;
  i=sizeof(long int);
  printf("%i\n",i);
}
_ACEOF
$CC tmp.c 2>&1>/dev/null
longIntTest=`./a.out`
rm tmp.c a.out
if [ "$longIntTest" == "8" ]
then
  PPLIST="${PPLIST} LONGINT8"
fi

if [ "$UNDERSCORE" == "true" ]; then
  PPLIST="${PPLIST} UNDERSCORE"
fi 

PPLIST="${PPLIST} GLOBAL_LONG_LONG"

MXM_USER="mxm_std.o blas.o"
echo $PPLIST | grep 'BG' >/dev/null 
if [ $? -eq 0 ]; then
   MXM_USER="mxm_std.o bg_aligned3.o bg_mxm44.o bg_mxm44_uneven.o bg_mxm3.o blas.o" 
   OPT_FLAGS_STD="-qarch=450 -qtune=450"
   OPT_FLAGS_MAG="-O5 -qarch=450d -qtune=450"
fi
echo $PPLIST | grep 'BLAS_MXM' >/dev/null 
if [ $? -eq 0 ]; then
   MXM_USER="mxm_std.o" 
fi

# set optimization flags
L0="\$(G) -O0"
L2="\$(G) -O2"
L3="\$(G) -O3" 
L4="\$(L3)"

# user specified opt flags
if [ "$OPT_FLAGS_STD" != "" ]; then
  echo $OPT_FLAGS_STD | grep "\-O." 1>/dev/null
  if [ $? -eq 0 ]; then
    L2="\$(G) $OPT_FLAGS_STD"
    L3="\$(G) $OPT_FLAGS_STD" 
  else
    L2="\$(G) -O2 $OPT_FLAGS_STD"
    L3="\$(G) -O3 $OPT_FLAGS_STD"
  fi
fi

if [ "$OPT_FLAGS_MAG" != "" ]; then
    L4="\$(G) $OPT_FLAGS_MAG"
fi

if [ "$USR_LIB" != "" ]; then
    USR_LFLAGS="${USR_LFLAGS} ${USR_LIB}"
fi

# tweak makefile template 
echo "generating makefile ..."
rm -rf makefile 2>/dev/null

sed -e "s:^F77[ ]*=.*:F77\:=$F77:" \
-e "s:^CC[ ]*=.*:CC\:=$CC:" \
-e "s:^G[ ]*=.*:G\:=$G:" \
-e "s:^OPT_FLAGS[ ]*=.*:OPT_FLAGS\:=$OPT_FLAGS:" \
-e "s/^P[ ]*=.*/P:=$P/" \
-e "s/^L0[ ]*=.*/L0=$L0/" \
-e "s/^L2[ ]*=.*/L2=$L2/" \
-e "s/^L3[ ]*=.*/L3=$L3/" \
-e "s/^L4[ ]*=.*/L4=$L4/" \
-e "s/^PPPO[ ]*=.*/PPPO=$PPPO/" \
-e "s/^PPS[ ]*=.*/PPS=$PPLIST/" \
-e "s:^MXM[ ]*=.*:MXM=$MXM_USER:" \
-e "s/^IFMPI[ ]*=.*/IFMPI:=$IFMPI/" \
-e "s:^USR[ ]*=.*:USR\:=$USR:" \
-e "s:^USR_LFLAGS[ ]*=.*:USR_LFLAGS\:=$USR_LFLAGS:" \
-e "s:^S[ ]*=.*:S\:=${SOURCE_ROOT}:" ./makefile.template >.makefile

echo $G | grep '\-g' 1>/dev/null
if [ $? -eq 0 ]; then
  sed 's/-O[1-4]/-O0/g' .makefile > .makefile.tmp
  mv .makefile.tmp .makefile
  echo "Activate DEBUG mode"
fi

if [ "$USR" != "" ]; then
  echo "###########################################################" >> makefile
  echo "include makefile_usr.inc" >> .makefile
fi

if [ -f .makefile ]; then
  sed -e "1i\\
### makefile automatically created by makenek `date +"%m/%d/%Y %T"` ###" \
-e "s:^CASEDIR[ ]*=.*:CASEDIR\:=${CASEDIR}:" \
-e "s:^CASENAME[ ]*=.*:CASENAME\:=${CASENAME}:" .makefile > makefile 
else
  echo "ERROR: Nek Makefile could not be created!"
  exit 1 
fi
\rm .makefile 2>/dev/null

# tweak SIZE file
if [ -f "./SIZE" ]; then
  cat SIZE | grep -i 'lxo' >/dev/null
else
  echo "FATAL ERROR: Cannot find SIZE"
  exit 1
fi

if [ $NOCOMPILE -eq 1 ]; then
  exit 0
fi 
