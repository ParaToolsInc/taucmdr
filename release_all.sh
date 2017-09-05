#!/bin/bash
#
# Build release packages for all known TAU targets.
#
# This script is a hack to work around setuptools' stateful
# implementation of sdist.  It should be removed someday.
#
# Author: John C. Linford (jlinford@paratools.com)
#


release="python setup.py release"

$release --web
python setup.py release --all | grep '^(' | (while read line ; do
  line=`echo $line | tr -d '()'`
  arch=`echo $line | cut -d, -f1`
  os=`echo $line | cut -d, -f2`
  $release --target-arch $arch --target-os $os
done)

