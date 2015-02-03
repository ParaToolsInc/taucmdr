#!/bin/bash
HERE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

export NODE_ENV="production"

export PATH=$HERE/../node_modules/.bin:$PATH
sails lift --prod $@

