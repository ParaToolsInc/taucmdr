#!/bin/bash
#
# Script to deploy Sphinx documentation to gh-pages branch automatically with Travis-CI
#
#set -o pipefail
#set -o errexit
#set -o nounset
set -o verbose

git config user.name "Travis-CI-bot"
git config user.email "info@paratools.com"

git remote -v
git remote rm origin
git remote add origin "https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git"
git remote -v | sed 's#\(https://\)\(.*\)\(@github\.com/[^ ]*\)#\1SECRET\3#g'

git fetch origin gh-pages > /dev/null 2>&1 && echo success || echo failure
git branch -a -vvv || echo "git branch fails if on detatched head"

export PUSH_FLAGS='--quiet --force'
export CHECKOUT_FLAGS='--force'
export HIDE_TOKEN='> /dev/null 2>&1'
export COMMIT_MSG="Updated documentation on Travis-CI job $TRAVIS_JOB_NUMBER at commit $TRAVIS_COMMIT"
make -C docs update-github-pages
