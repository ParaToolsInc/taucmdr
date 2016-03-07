#!/bin/bash
#set -o pipefail
#set -o errexit
#set -o verbose

# Install pyenv to globally manage python versions
# See https://github.com/yyuu/pyenv for further details
echo "$PYENV_ROOT"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"

if [ ! -x "$PYENV_ROOT/bin/pyenv" ]; then
    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
fi

if [ ! -d "$PYENV_ROOT/.git" ]; then # pyenv install script failed, try manual install
    git clone --no-checkout -v https://github.com/yyuu/pyenv.git "$HOME/tmp"
    mv "$HOME/tmp/.git" "$PYENV_ROOT/"
    rmdir "$HOME/tmp"
    cd "$PYENV_ROOT"
    git reset --hard HEAD
    cd -
fi

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
