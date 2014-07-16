#!/bin/bash

myhost=`hostname`
cached=$HOME/.ParaProf/tau_javamax-$myhost
if [ -f $cached ] ; then
	cat $cached
	exit
else
	mkdir -p $HOME/.ParaProf
	echo "failed" > $cached
fi

# don't want the user to see glibc errors (on Franklin)
export MALLOC_CHECK_=0

# check that we're on linux
if [ $(uname) != "Linux" ]; then
	if [ $(uname) != "Darwin" ]; then
    	echo "failed"
    	exit
	fi
fi

# first, check that this is sun java
ver=`java -version 2>&1 | tail -1 | awk '{print $1 $2}'`

if [ "x$ver" != "xJavaHotSpot(TM)" ] ; then
    GCJ=`java -showversion 2>&1 | grep -i OpenJDK` 
    if [ "x$GCJ" = "x" ] ; then
       echo "failed"
       exit
    fi
fi

if [ $(uname) = "Darwin" ]; then
    # memtotal=`java -XX:+PrintFlagsFinal -version 2>&1 | grep MaxHeapSize | awk '{print $4}'`
    memtotal=`sysctl -a | grep "hw.memsize:" | awk '{print $2}'`
    trymem=$(($memtotal/(1024*1024)))
#	echo "$trymem" > $cached
#	echo $trymem
#	exit
else
	memtotal=`cat /proc/meminfo | head -1 | awk '{print $2}'`
        if [ $(uname -m) = "i686" ]; then
          if [ $memtotal -gt 2300000 ] ; then
	     memtotal="2300000"
          fi
        fi
fi

trymem=$(($memtotal/1000*7/8))
while [ $trymem -gt 250 ] ; do
    oldmem=$trymem
    trymem=$(($trymem*3/4))

    java -Xmx${oldmem}m -version > /dev/null 2>&1
    if [ $? != 0  ] ; then
       continue;
    fi    

    check=`java -Xmx${oldmem}m foobar 2>&1 | head -2`
    check1=`echo "$check" | head -1`
    check2=`echo "$check" | tail -1`
    # echo "check1=$check1"
    # echo "check2=$check2"

    case $check1 in 
	"Invalid maximum heap size"* ) 
	continue;
    esac

    if [ "x$check2" = "xCould not reserve enough space for object heap" ] ; then
	continue;
    fi
    if [ "x$check2" = "xThe specified size exceeds the maximum representable size." ] ; then
	continue;
    fi

    echo "$oldmem"
	echo "$oldmem" > $cached
    exit
done

echo "failed"
