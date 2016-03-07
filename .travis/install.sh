#!/bin/bash

set -o pipefail
set -o errexit
set -o verbose

# Install pyenv to globally manage python versions
# See https://github.com/yyuu/pyenv for further details
if [ ! -d "$HOME/.pyenv" ]; then
    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
fi

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
pyenv init -
pyenv virtualenv-init -

pyenv update ||true

export PYENV_VERSION="${PYENV_VERSION:-2.7.9}"
pyenv install -s ${PYENV_VERSION}
pyenv rehash
pyenv versions
pyenv which pip

# Install development requirements enumerated in requirements.txt
pip install -r requirements.txt

export PATH="/path/to/taucmdr/bin:$PATH"
