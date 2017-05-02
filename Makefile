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

# Conda configuration
USE_CONDA = true
ifeq ($(OS),Darwin)
ifeq ($(ARCH),i386)
  USE_CONDA = false
endif
endif
ifeq ($(OS),Darwin)
  CONDA_OS = MacOSX
else 
  ifeq ($(OS),Linux)
    CONDA_OS = Linux
  else
    USE_CONDA = false
  endif
endif
ifeq ($(ARCH),x86_64)
  CONDA_ARCH = x86_64
else 
  ifeq ($(ARCH),i386)
    CONDA_ARCH = x86
  else
    USE_CONDA = false
  endif
endif
CONDA_VERSION = 4.3.1
CONDA_REPO = https://repo.continuum.io/archive
CONDA_PKG = Anaconda2-$(CONDA_VERSION)-$(CONDA_OS)-$(CONDA_ARCH).sh
CONDA_URL = $(CONDA_REPO)/$(CONDA_PKG)
CONDA_SRC = packages/$(CONDA_PKG)
CONDA_DEST = $(INSTALLDIR)/conda
CONDA = $(CONDA_DEST)/bin/python

ifeq ($(USE_CONDA),true)
  PYTHON_EXE = $(CONDA)
  PYTHON_FLAGS = -E
else
  $(warning WARNING: There are no conda packages for this system: $(OS), $(ARCH).)
  PYTHON_EXE = $(shell which python)
  PYTHON_FLAGS =
  ifeq ($(PYTHON_EXE),)
    $(error python not found in PATH.)
  else
    $(warning WARNING: Trying to use '$(PYTHON_EXE)' instead.)
  endif
endif
PYTHON = $(PYTHON_EXE) $(PYTHON_FLAGS)

.PHONY: build install clean python_check

.DEFAULT: build

build: python_check
	$(ECHO)$(PYTHON) setup.py build

install: build
# Build python files and set system-level defaults
	$(ECHO)$(PYTHON) setup.py install --force
# Copy archive files to system-level src, if available
	@mkdir -p $(INSTALLDIR)/system/src
	@cp -v packages/*.tgz $(INSTALLDIR)/system/src 2>/dev/null || true
	@cp -v packages/*.tar.* $(INSTALLDIR)/system/src 2>/dev/null || true
	@cp -v packages/*.zip $(INSTALLDIR)/system/src 2>/dev/null || true
# Build dependencies using archives and system-level defaults
	$(ECHO)$(PYTHON) setup.py install --force --initialize
# Add PYTHON_FLAGS to python command line in bin/tau
	@tail -n +2 "$(TAU)" > "$(BUILDDIR)/tau.tail"
	@echo `head -1 "$(TAU)"` $(PYTHON_FLAGS) > "$(BUILDDIR)/tau.head"
	@cat "$(BUILDDIR)/tau.head" "$(BUILDDIR)/tau.tail" > "$(TAU)"
	@chmod -R a+rX,g+w $(INSTALLDIR)
	@echo
	@echo "-------------------------------------------------------------------------------"
	@echo "TAU Commander is installed at \"$(INSTALLDIR)\""
	@echo "Rememember to add \"$(INSTALLDIR)/bin\" to your PATH"
	@echo "-------------------------------------------------------------------------------"
	@echo

python_check: $(PYTHON_EXE)
	@$(PYTHON) -c "import sys; import setuptools;" || (echo "ERROR: setuptools is required." && false)

$(CONDA): $(CONDA_SRC)
	$(ECHO)bash $< -b -p $(CONDA_DEST)
	$(ECHO)touch $(CONDA_DEST)/bin/*

$(CONDA_SRC):
	$(ECHO)$(MKDIR) $(BUILDDIR)
	$(call download,$(CONDA_URL),$(CONDA_SRC))

clean: 
	$(ECHO)$(RM) -r $(BUILDDIR)
	$(ECHO)$(RM) defaults.cfg setup.cfg

