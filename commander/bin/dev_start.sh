#!/bin/bash
HERE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd "$HERE/.."
export PATH=$PWD/node_modules/.bin:$PATH

export NODE_ENV="development"
#rm -rf .tmp
sails lift $@

