#!/bin/bash
#
# Script to deploy Sphinx documentation to gh-pages branch automatically with Travis-CI
#
#set -o pipefail
#set -o errexit
#set -o nounset
set -o verbose

function dieInFlames {
  echo "ERROR: $1"
  exit 255
}

function configRepo {
  git config user.name "Travis-CI-bot"
  git config user.email "info@paratools.com"

  git remote -v
  git remote rm origin
  git remote add origin https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git
  git remote -v | sed 's#\(https://\)\(.*\)\(@github\.com/[^ ]*\)#\1SECRET\3#g'

  git fetch origin gh-pages > /dev/null 2>&1 || dieInFlames "git fetch origin gh-pages"
  git branch -a -vvv || echo "git branch fails if on detatched head"
}

function buildDocs {
  python setup.py build_sphinx
}

function updateDocs {
  git checkout --force gh-pages
  tar -C build/sphinx/html -cf - . | tar xf -
  git add -A .
  git commit -m "Updated documentation on Travis-CI job $TRAVIS_JOB_NUMBER at commit $TRAVIS_COMMIT"
  git push --quiet --force origin gh-pages > /dev/null 2>&1
}

configRepo && buildDocs && updateDocs

