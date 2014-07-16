#!/bin/sh
if [ $# != 1 ] ; then
  echo "Usage: $0 <path/to/eclipse/root>"
  echo ""
  echo "Please enter the location of your Eclipse 3.5.0+ installation."
  echo "Note that you must have the CDT and PTP plugins installed"
  echo "for the TAU plugins to function properly."
  exit 1
fi

if [ ! -d "$1" ] ; then
    echo "Invalid eclipse directory"
    exit 1
fi

if [ ! -d "$1"/dropins/ ] ; then
    echo "Warning: No dropins directory in eclipse root.  Creating directory"
    mkdir $1/dropins/
fi

CURRENT_DIR=`pwd`

cd $1/dropins/
PLUG_DIR=`pwd`
cd $CURRENT_DIR

cd `dirname $0`
echo "Installing to $1/dropins"
echo "..."

tar -zxf ./plugins.tgz
cp -r ./plugins/* $PLUG_DIR
rm -r ./plugins
#cp -r ./plugins/org.eclipse.ptp.perf.tau.jars_1.0.0/ $PLUG_DIR

#for JAR_DIR in $PLUG_DIR/org.eclipse.ptp.perf.tau.jars_*
#do

#cp ../contrib/batik-combined.jar $JAR_DIR
#cp ../contrib/jargs.jar $JAR_DIR
#cp ../contrib/jcommon-1.0.15.jar $JAR_DIR
#cp ../contrib/jfreechart-1.0.12.jar $JAR_DIR
#cp ../contrib/jgraph.jar $JAR_DIR
#cp ../contrib/jogl/jogl.jar $JAR_DIR
#cp ../contrib/jython.jar $JAR_DIR
#cp ../contrib/xerces.jar $JAR_DIR

#cp ../paraprof/bin/paraprof.jar $JAR_DIR
#cp ../perfdmf/bin/perfdmf.jar $JAR_DIR
#cp ../common/bin/tau-common.jar $JAR_DIR
#cp ../vis/bin/vis.jar $JAR_DIR


#done


cd $CURRENT_DIR
echo "Eclipse plugins installed!"
