#!/bin/bash
#
# Script to deploy Sphinx documentation to gh-pages branch automatically with Travis-CI
#
python setup.py build_sphinx \
        --update-gh-pages \
        --gh-user-name "Travis-CI-bot" \
        --gh-user-email "info@paratools.com" \
        --gh-commit-msg "Updated documentation on Travis-CI job $TRAVIS_JOB_NUMBER at commit $TRAVIS_COMMIT"

