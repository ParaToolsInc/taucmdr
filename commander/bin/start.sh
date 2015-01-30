#!/bin/bash
HERE=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

export PATH=$HERE/../node_modules/.bin:$PATH
sails lift $@

