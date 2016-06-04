#!/usr/bin/env bash
#set -o pipefail
#set -o errexit
#set -o verbose

shopt -s checkwinsize # ensure that the shell updates the window size...

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
    cd "$PYENV_ROOT" || exit 1
    git reset --hard HEAD
    cd - || exit 1
fi

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv update ||true

export PYENV_VERSION="${PYENV_VERSION:-2.7.9}"
pyenv install -s "${PYENV_VERSION}"
pyenv global "${PYENV_VERSION}"
pyenv rehash
pyenv versions
pyenv which pip

if [[ "X${USE_VENV:-No}" == X[yY]* ]]; then
  # Create a clean virtualenv to isolate the environment from Travis-CI defaults
  python -m pip install --user virtualenv
  python -m virtualenv "$HOME/.venv"

  # shellcheck source=~/.venv/bin/activate disable=SC1090
  source "$HOME/.venv/bin/activate"
fi

resize # make sure pyenv or venv didn't do anything strange

# Install development requirements enumerated in requirements.txt
pip install -r requirements.txt

export PATH="$PWD/bin:$PATH"


### Determine the files changed in the commit range being tested
if [[ "X$(uname -s)" == "XDarwin" ]]; then
  this_os=osx
else
  this_os=linux
fi

export MY_OS=${TRAVIS_OS_NAME:-${this_os}}
export REPO_SLUG=${TRAVIS_REPO_SLUG:-ParaToolsInc/taucmdr}
export GIT_COMMIT=${TRAVIS_COMMIT:-"$(git rev-parse HEAD)"}
export COMMIT_RANGE=${TRAVIS_COMMIT_RANGE:-"$(git rev-parse HEAD)^..$(git rev-parse HEAD)"}
export PR=${TRAVIS_PULL_REQUEST:-false}

# Be carefull here; pull requests with forced pushes can potentially
# cause issues
_diff_range="${COMMIT_RANGE/.../..}" # use bash parameter expansion rather than sed
if [ "$PR" != "false" ]; then # Use github API to get changed files
  [ "X$MY_OS" = "Xosx" ] && (brew update > /dev/null || true ; brew install jq || true)
  _files_changed=($(curl "https://api.github.com/repos/$REPO_SLUG/pulls/$PR/files" 2> /dev/null | \
			 jq '.[] | .filename' | tr '"' ' '))
  if [[ ${#_files_changed[@]} -eq 0 || -z ${_files_changed[@]} ]]; then
    echo "Using git to determine changed files"
    # no files detected, try using git instead
    # This approach may only pick up files from the most recent commit, but that's
    # better than nothing
    _files_changed=($(git diff --name-only "$_diff_range" | sort -u || \
                      git diff --name-only "${GIT_COMMIT}^..${GIT_COMMIT}" | sort -u ))
  else
    echo "Using Github API to determine changed files"
  fi
else
  echo "Using git to determine changed files"
  # We should be ok using git, see https://github.com/travis-ci/travis-ci/issues/2668
  _files_changed=($(git diff --name-only "$_diff_range" | sort -u || \
                    git diff --name-only "${GIT_COMMIT}^..${GIT_COMMIT}" | sort -u ))
fi

FILES_CHANGED=()
TAU_PY_CHANGED_FILES=()
for file in "${_files_changed[@]}"; do
  if [[ ! -f "$file" ]]; then
      echo "File $file no longer exists, removing from list of changed files"
  else
      FILES_CHANGED+=("$file")
      if [[ "$file" == *packages/tau* ]]; then
	  if head -n 1 "$file" | grep '^#!/usr/bin/env python' > /dev/null ; then
	      TAU_PY_CHANGED_FILES+=("$file")
	  elif [[ "$file" == *.py ]]; then
	      TAU_PY_CHANGED_FILES+=("$file")
	  fi
      fi
  fi
done

echo "Files changed in $COMMIT_RANGE:"
for f in "${FILES_CHANGED[@]}"; do
    echo "    $f"
done
echo "TAU commander Python files changed:"
for f in "${TAU_PY_CHANGED_FILES[@]}"; do
    echo "    $f"
done

tmp=${FILES_CHANGED[*]}
unset FILES_CHANGED
# can't export arrays...
FILES_CHANGED=$(sort -u <<< "${tmp}") # shellcheck disable=SC2178
export FILES_CHANGED
echo "Files changed: ${FILES_CHANGED:-<none>}"
tmp=${TAU_PY_CHANGED_FILES[*]}
unset TAU_PY_CHANGED_FILES
TAU_PY_CHANGED_FILES=$(sort -u <<< "${tmp}") # shellcheck disable=SC2178
export TAU_PY_CHANGED_FILES
echo "TAU Commander changed python files: ${TAU_PY_CHANGED_FILES:-<none>}"
