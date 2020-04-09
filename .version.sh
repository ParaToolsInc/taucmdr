#!/bin/bash
if ! [ -f VERSION ]; then
  version=$(git describe --tags 2> /dev/null || echo "v0.0.0")
  if [ "$version" != "v0.0.0" ]; then
    #PEP 440 compliance
    version=$(echo "$version" | cut -d- -f1,2 | sed -e 's/-/./')
  fi
  echo "${version:1}" > VERSION
fi
cat VERSION
