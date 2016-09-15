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

# If set to "true" then show commands as they are executed.
# Otherwise only the command's output will be shown.
VERBOSE = true

# Shell utilities
RM = rm -f
MKDIR = mkdir -p

# Get build system locations from configuration file or command line
ifneq ("$(wildcard setup.cfg)","")
  BUILDDIR = $(shell grep '^build-base =' setup.cfg | sed 's/build-base = //')
  INSTALLDIR = $(shell grep '^prefix =' setup.cfg | sed 's/prefix = //')
else
  ifeq ($(INSTALLDIR),)
    $(error INSTALLDIR not set)
  endif
  # Bootstrap setup.cfg
  $(shell cp .bootstrap.cfg setup.cfg && echo "prefix = $(INSTALLDIR)" >> "setup.cfg")
endif
ifeq ($(BUILDDIR),)
  BUILDDIR=build
endif

TAU = $(INSTALLDIR)/bin/tau

# Get target OS and architecture
OS = $(shell uname -s)
ARCH = $(shell uname -m)
HOSTNAME = $(shell hostname | cut -d. -f1)

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
WGET = $(shell which wget)
ifneq ($(WGET),)
  download = $(WGET) $(WGET_FLAGS) -O "$(2)" "$(1)"
else
  CURL = $(shell which curl)
  ifneq ($(CURL),)
    download = $(CURL) $(CURL_FLAGS) -L "$(1)" > "$(2)"
  else
    $(warning Either curl or wget must be in PATH to download packages)
  endif
endif

# Miniconda configuration
USE_MINICONDA = true
ifeq ($(OS),Darwin)
ifeq ($(ARCH),i386)
  USE_MINICONDA = false
endif
endif
ifeq ($(OS),Darwin)
  CONDA_OS = MacOSX
else 
  ifeq ($(OS),Linux)
    CONDA_OS = Linux
  else
    USE_MINICONDA = false
  endif
endif
ifeq ($(ARCH),x86_64)
  CONDA_ARCH = x86_64
else 
  ifeq ($(ARCH),i386)
    CONDA_ARCH = x86
  else
    USE_MINICONDA = false
  endif
endif
CONDA_VERSION = 4.0.5
CONDA_REPO = https://repo.continuum.io/miniconda
CONDA_PKG = Miniconda2-$(CONDA_VERSION)-$(CONDA_OS)-$(CONDA_ARCH).sh
CONDA_URL = $(CONDA_REPO)/$(CONDA_PKG)
CONDA_SRC = $(BUILDDIR)/$(CONDA_PKG)
CONDA_DEST = $(INSTALLDIR)/conda
CONDA_LIBRARY_PATH = $(CONDA_DEST)/lib:$(CONDA_DEST)/lib64
CONDA = $(CONDA_DEST)/bin/python

ifeq ($(USE_MINICONDA),true)
	PYTHON = $(CONDA) -E
else
  $(warning WARNING: There are no miniconda packages for this system: $(OS), $(ARCH).)
  PYTHON = $(shell which python)
  ifeq ($(PYTHON),)
    $(error python not found in PATH.)
  else
    $(warning WARNING: I'll try to use '$(PYTHON)' instead.)
  endif
endif

.PHONY: build install clean python_check

.DEFAULT: build

build: python_check
	$(ECHO)$(PYTHON) setup.py build

install: build
	$(ECHO)$(PYTHON) setup.py install --force
	@echo
	@echo "-------------------------------------------------------------------------------"
	@echo "TAU Commander is installed at \"$(INSTALLDIR)\""
	@echo "Rememember to add \"$(INSTALLDIR)/bin\" to your PATH"
	@echo "-------------------------------------------------------------------------------"
	@echo

python_check: $(PYTHON)
	@echo "Checking '$(PYTHON)'"
	@echo "$$LD_LIBRARY_PATH"
	@$(PYTHON) -c "import sys; print sys.path ; import setuptools;" || (echo "ERROR: setuptools is required." && false)
	@echo "'$(PYTHON)' appears to work."

$(CONDA): $(CONDA_SRC)
	$(ECHO)bash $< -b -p $(CONDA_DEST)
	$(ECHO)touch $(CONDA_DEST)/bin/*

$(CONDA_SRC):
	$(ECHO)$(MKDIR) $(BUILDDIR)
	$(call download,$(CONDA_URL),$(CONDA_SRC))

clean: 
	$(ECHO)$(RM) -r $(BUILDDIR)

