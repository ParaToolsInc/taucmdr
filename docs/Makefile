#
# TAU Commander Documentation
#
# Copyright (c) ParaTools, Inc.
#
# May, 2015
#
# Srinath Vadlamani (srinathv@paratools.com)
# John C. Linford (jlinford@paratools.com)
#
HERE := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Travis-CI tests pushed commits in a detatched head state. As a result,
# `git rev-parse --abbrev-ref HEAD` won't always be meaningful. If the
# environment variable TRAVIS_COMMIT is defined, then use this. If not,
# then use `git rev-parse` (and assume we're on master).
TRAVIS_COMMIT ?= $(shell git rev-parse --abbrev-ref HEAD)
LOCAL_BRANCH := $(TRAVIS_COMMIT)
DOCS_BRANCH = gh-pages

SPHINX_BUILDER = html
PROJECT_PACKAGE = tau

PROJECT_DIR = $(HERE)/../packages/$(PROJECT_PACKAGE)/
BUILD_DIR = $(HERE)/developer/
SOURCE_DIR = $(HERE)/source/
STATIC_DIR = $(SOURCE_DIR)/_static/

CONF_FILES = conf.py
REST_FILES = index.rst design.rst style.rst
IMAGE_FILES = favicon.ico taulogo-large.png


SOURCE_FILES = $(addprefix $(SOURCE_DIR), $(CONF_FILES) $(REST_FILES))
STATIC_FILES = $(addprefix $(STATIC_DIR), $(IMAGE_FILES))
PACKAGE_REST_FILE = $(PROJECT_PACKAGE).rst


.PHONY: all clean update-github-pages

all: $(PACKAGE_REST_FILE) $(STATIC_FILES)
	sphinx-build -b $(SPHINX_BUILDER) $(SOURCE_DIR) $(BUILD_DIR)

$(PACKAGE_REST_FILE): $(SOURCE_FILES)
	sphinx-apidoc -M -P -f -o $(SOURCE_DIR) $(PROJECT_DIR)

update-github-pages: 
	git checkout $(DOCS_BRANCH)
	git checkout $(LOCAL_BRANCH) $(PROJECT_DIR) $(HERE)
	-git rm -f .gitignore
	$(MAKE) all
	git add $(HERE)
	git add -u $(HERE)
	git commit -m "Update documentation on $(DOCS_BRANCH) via Makefile"
	git push
	git checkout $(LOCAL_BRANCH)

clean:
	rm -rf $(BUILD_DIR)

