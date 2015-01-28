#!/bin/bash

if [ !$NODE_LAUNCH_SCRIPT ]; then
  export NODE_LAUNCH_SCRIPT="$PWD/taucmdr.js"
fi

forever stop $NODE_LAUNCH_SCRIPT
