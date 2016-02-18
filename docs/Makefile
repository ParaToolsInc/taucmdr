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

LOCAL_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
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
	$(MAKE) all
	git add $(HERE)
	git commit -m "Update documentation on $(DOCS_BRANCH) via Makefile"
	git push
	git checkout $(LOCAL_BRANCH)

clean:
	rm -f $(filter-out $(SOURCE_FILES),$(wildcard $(SOURCE_DIR)*.rst))
	rm -rf $(BUILD_DIR)

