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

git remote set-url origin https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git

git fetch origin gh-pages > /dev/null 2>&1 && echo success || echo failure
git fetch --unshallow ||true
git branch -a -vvv

export PUSH_FLAGS='--quiet --force'
export HIDE_TOKEN='> /dev/null 2>&1'
export COMMIT_MSG="Updated documentation on Travis-CI job $TRAVIS_JOB_NUMBER at commit $TRAVIS_COMMIT"
make -C docs update-github-pages
