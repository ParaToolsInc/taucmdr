#!/bin/bash 

declare -i numpass
declare -i numfail
declare -i numrun

declare testfail
numpass=0;
numfail=0;
numrun=0;
if [ `uname -s` = Darwin ] ; then
  extralib=-ldl
else
  extralib=-lrt
fi

CC=gcc
CXX=g++


cleanup()
{
    /bin/rm -rf simple profile.* *.o
}

check_output()
{
#    pprof
#    cp profile.0.0.0 $i.profile
#    cat profile.0.0.0
    testfail=no

    cat $i.check | while read line; do
#	echo "checking for $line"
	grep -c "$line" profile.0.0.0 &> /dev/null
	if [ $? != 0 ] ; then
	    exit 1
	fi
    done

    testfail=$?

    if [ $testfail = 0 ] ; then
	echo "pass"
	numpass=$numpass+1
    else
	echo "fail"
	numfail=$numfail+1
    fi
    numrun=$numrun+1
    
}


export TAU_METRICS=TIME
unset TAU_VERBOSE

export TAU_OPTIONS="-optCompInst -optTrackIO -optVerbose"

for i in test_*.c ; do
#for i in test_multiple.c ; do
    echo "Testing $i..."

    echo -n "  default...  "
    cleanup
    $CC -o simple $i &> /dev/null
    tau_exec -io -T serial ./simple
    check_output


    echo -n "  link with $extralib -lpthread...  "
    cleanup
    $CC -o simple $i $extralib -lpthread &> /dev/null
    tau_exec -io -T serial ./simple
    check_output


    echo -n "  built with TAU...  "
    cleanup
    tau_cc.sh -o simple $i  &> /dev/null
    tau_exec -io -T serial ./simple
    check_output

    echo -n "  built with TAU and linked with $extralib -lpthread...  "
    cleanup
    tau_cc.sh -o simple $i $extralib -lpthread &> /dev/null
    tau_exec -io -T serial ./simple
    check_output

    echo -n "  built with TAU and not executed using tau_exec... "
    cleanup
    tau_cc.sh $i -o simple &> /dev/null
    ./simple
    check_output


done


cleanup

echo ""
echo "$numpass passed, $numfail failed, $numrun total"
