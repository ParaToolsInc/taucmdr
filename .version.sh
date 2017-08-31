#!/bin/bash
if ! [ -f VERSION ] ; then
  version=`git describe --tags 2>/dev/null || echo "v0.0.0"`
  echo ${version:1} > VERSION
fi
cat VERSION

