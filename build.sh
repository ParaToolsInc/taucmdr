#!/bin/bash

function abort {
  echo "FATAL ERROR"
  exit 1
}

VERSION=`cat VERSION`

here="`cd ${0%/*} && pwd -P`"
echo $here

export PYTHONPATH=$here/packages/tau:$here/packages:$PYTHONPATH
python setup.py build_exe || abort

pushd build || abort
bindir="`ls`"
cp -rv ../LICENSE ../examples .
mkdir bin
pushd bin
ln -s ../$bindir/tau .
popd
popd

if [ -d taucmdr-$VERSION ] ; then
  echo "ERROR: there is a directory named taucmdr-$bindir in $here"
  echo "ERROR: Delete \"build\" and \"taucmdr-$bindir\" and try again"
  exit 1
fi

mv build taucmdr-$VERSION
tar cvzf taucmdr-${VERSION}-$bindir.tgz taucmdr-$VERSION
rm -rf taucmdr-$VERSION

