###############################################################################
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
###############################################################################

# TAU configuration level:
#   minimal: Install just enough to support the default project (`tau initialize` without any args).
#   full   : Install as many TAU configurations as possible for the current environment.
#   <path> : Use the TAU installation provided at <path>.
TAU ?= minimal

# If set to "true" then show commands as they are executed.
# Otherwise only the command's output will be shown.
VERBOSE = true
DOCKER_IMG_NAME = cmdr-dev-0.1.0
DOCKER_TAG = latest

# Shell utilities
RM = rm -f
MV = mv -f
MKDIR = mkdir -p

VERSION = $(shell cat VERSION 2>/dev/null || ./.version.sh || echo "0.0.0")

# Get build system locations from configuration file or command line
ifneq ("$(wildcard setup.cfg)","")
	BUILDDIR = $(shell grep '^build-base =' setup.cfg | sed 's/build-base = //')
	INSTALLDIR = $(shell grep '^prefix =' setup.cfg | sed 's/prefix = //')
endif
ifeq ($(BUILDDIR),)
	BUILDDIR=build
endif
ifeq ($(INSTALLDIR),)
	INSTALLDIR=$(HOME)/taucmdr-$(VERSION)
endif

# Get target OS and architecture
ifeq ($(HOST_OS),)
	HOST_OS = $(shell uname -s)
endif
ifeq ($(HOST_ARCH),)
	HOST_ARCH = $(shell uname -m)
endif

ifeq ($(VERBOSE),false)
	ECHO=@
	CURL_FLAGS=-s
	WGET_FLAGS=--quiet
else
	ECHO=
	CURL_FLAGS=
	WGET_FLAGS=
endif

# Build download macro
# Usage: $(call download,source,dest)
WGET = $(shell command -pv wget || type -P wget || which wget)
ifneq ($(WGET),)
	download = $(WGET) --no-check-certificate $(WGET_FLAGS) -O "$(2)" "$(1)"
else
	CURL = $(shell command -pv curl || type -P curl || which curl)
	ifneq ($(CURL),)
		download = $(CURL) --insecure $(CURL_FLAGS) -L "$(1)" > "$(2)"
	else
		$(warning Either curl or wget must be in PATH to download packages)
	endif
endif

# Miniconda configuration
USE_MINICONDA = true
ifeq ($(HOST_OS),Darwin)
ifeq ($(HOST_ARCH),i386)
	USE_MINICONDA = false
endif
endif
ifeq ($(HOST_OS),Darwin)
	CONDA_OS = MacOSX
else
	ifeq ($(HOST_OS),Linux)
		CONDA_OS = Linux
	else
		USE_MINICONDA = false
	endif
endif
ifeq ($(HOST_ARCH),x86_64)
	CONDA_ARCH = x86_64
else
	ifeq ($(HOST_ARCH),i386)
		CONDA_ARCH = x86
	else
		ifeq ($(HOST_ARCH),ppc64le)
			CONDA_ARCH = ppc64le
		else
			USE_MINICONDA = false
		endif
	endif
endif
CONDA_VERSION = latest
CONDA_REPO = https://repo.continuum.io/miniconda
CONDA_PKG = Miniconda2-$(CONDA_VERSION)-$(CONDA_OS)-$(CONDA_ARCH).sh
CONDA_URL = $(CONDA_REPO)/$(CONDA_PKG)
CONDA_SRC = system/src/$(CONDA_PKG)
CONDA_DEST = $(INSTALLDIR)/conda
CONDA = $(CONDA_DEST)/bin/python

ifeq ($(USE_MINICONDA),true)
	PYTHON_EXE = $(CONDA)
	PYTHON_FLAGS = -EOu
#	PYTHON_FLAGS = -EOu3
else
	$(warning WARNING: There are no miniconda packages for this system: $(HOST_OS), $(HOST_ARCH).)
	CONDA_SRC =
	PYTHON_EXE = $(shell command -pv python || type -P python || which python)
	PYTHON_FLAGS = -O
	ifeq ($(PYTHON_EXE),)
		$(error python not found in PATH.)
	else
		$(warning WARNING: Trying to use '$(PYTHON_EXE)' instead.)
	endif
endif
PYTHON = $(PYTHON_EXE) $(PYTHON_FLAGS)

.PHONY: help build install clean python_check python_download dev-container run-container

.DEFAULT: help

help:
	@echo "-------------------------------------------------------------------------------"
	@echo "TAU Commander installation"
	@echo
	@echo "Usage: make install [INSTALLDIR=$(INSTALLDIR)] [TAU=(minimal|full|<path>)]"
	@echo "-------------------------------------------------------------------------------"

build: python_check
	$(ECHO)$(PYTHON) -m pip install -U -r requirements-dev.txt
	$(ECHO)$(PYTHON) setup.py build_scripts --executable "$(PYTHON)"
	$(ECHO)$(PYTHON) setup.py build

install: build
	$(ECHO)$(PYTHON) setup.py install --prefix $(INSTALLDIR)
	$(ECHO)$(INSTALLDIR)/system/configure --tau-config=$(TAU)
	@chmod -R a+rX,g+w $(INSTALLDIR)
	@echo
	@echo "-------------------------------------------------------------------------------"
	@echo "Hooray! TAU Commander is installed!"
	@echo
	@echo "INSTALLDIR=\"$(INSTALLDIR)\""
	@echo
	@echo "What's next?"
	@echo
	@echo "TAU Commander will automatically generate new TAU configurations for each new"
	@echo "experiment, so if you're just trying to get some performance data then go add"
	@echo "TAU Commander's \"bin\" directory to your path and maybe have a look at"
	@echo "the quick start guide at http://www.taucommander.com/guide."
	@echo
	@echo "If you'd like to pre-configure TAU for a particular experiment then go use"
	@echo "the \"$(INSTALLDIR)/system/configure\" script to generate TAU configurations."
	@echo "This is especially a good idea if you are a system administrator installing"
	@echo "TAU Commander so that someone else can use it.  Without arguments, the"
	@echo "\"configure\" script will generate as many TAU configurations as it can."
	@echo
	@echo "In short:"
	@echo "  If you are a sysadmin then go run \"$(INSTALLDIR)/system/configure\"."
	@echo "  Otherwise just add \"$(INSTALLDIR)/bin\" to your PATH and get to work."
	@echo "-------------------------------------------------------------------------------"
	@echo

python_check: $(PYTHON_EXE)
	@$(PYTHON) -c "import sys; import setuptools;" || (echo "ERROR: setuptools is required." && false)

python_download: $(CONDA_SRC)

$(CONDA): $(CONDA_SRC)
	$(ECHO)bash $< -b -u -p $(CONDA_DEST)
	$(ECHO)touch $(CONDA_DEST)/bin/*

$(CONDA_SRC):
	@$(ECHO)$(MKDIR) `dirname "$(CONDA_SRC)"`
	@$(call download,$(CONDA_URL),$(CONDA_SRC)) || \
						(rm -f "$(CONDA_SRC)" ; \
						echo "**************************************************************************" ; \
						echo "*" ; \
						echo "* ERROR" ; \
						echo "*" ; \
						echo "* Unable to download $(CONDA_URL)." ; \
						echo "* Please use an all-in-one package from www.taucommander.com" ; \
						echo "*" ; \
						echo "**************************************************************************" ; \
						false)

clean:
	$(ECHO)$(RM) -r $(BUILDDIR) VERSION

dev-container:
	$(ECHO)docker build --pull --rm -t $(DOCKER_IMG_NAME) .

run-container:
	$(ECHO)docker run -i -t -v ${PWD}:/home/tau/src $(DOCKER_IMG_NAME):$(DOCKER_TAG)
