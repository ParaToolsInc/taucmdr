#!/bin/bash
#set -o pipefail
#set -o errexit
#set -o verbose

# Install pyenv to globally manage python versions
# See https://github.com/yyuu/pyenv for further details
echo "$PYENV_ROOT"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

if [ ! -x "$HOME/.pyenv/bin/pyenv" ]; then
    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
fi

# cd "$HOME/.pyenv"
# git pull origin master || git clone -v https://github.com/yyuu/pyenv.git "$HOME/.pyenv"
# cd -

ls -a ~/.pyenv
ls ~/.pyenv/bin

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv update ||true

export PYENV_VERSION="${PYENV_VERSION:-2.7.9}"
pyenv install -s ${PYENV_VERSION}
pyenv global ${PYENV_VERSION}
pyenv rehash
pyenv versions
pyenv which pip

# Create a clean virtualenv to isolate the environment from Travis-CI defaults
python -m pip install --user virtualenv

python -m virtualenv "$HOME/.venv"
source "$HOME/.venv/bin/activate"

# Install development requirements enumerated in requirements.txt
pip install -r requirements.txt

export PATH="/path/to/taucmdr/bin:$PATH"
