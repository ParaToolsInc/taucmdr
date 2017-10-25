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
MV = mv -f
MKDIR = mkdir -p
CP = cp -fr

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

TAU = $(INSTALLDIR)/bin/tau

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

# Anaconda configuration
USE_ANACONDA = true
ifeq ($(HOST_OS),Darwin)
ifeq ($(HOST_ARCH),i386)
  USE_ANACONDA = false
endif
endif
ifeq ($(HOST_OS),Darwin)
  ANACONDA_OS = MacOSX
else
  ifeq ($(HOST_OS),Linux)
    ANACONDA_OS = Linux
  else
    USE_ANACONDA = false
  endif
endif
ifeq ($(HOST_ARCH),x86_64)
  ANACONDA_ARCH = x86_64
else
  ifeq ($(HOST_ARCH),i386)
    ANACONDA_ARCH = x86
  else
    USE_ANACONDA = false
  endif
endif
ifeq ($(PYTHON_VERSION),)
  PYTHON_VERSION=2
endif
ANACONDA_VERSION = 4.4.0
ANACONDA_REPO = https://repo.continuum.io/archive
ANACONDA_PKG = Anaconda$(PYTHON_VERSION)-$(ANACONDA_VERSION)-$(ANACONDA_OS)-$(ANACONDA_ARCH).sh
ANACONDA_URL = $(ANACONDA_REPO)/$(ANACONDA_PKG)
ANACONDA_SRC = packages/$(ANACONDA_PKG)
ANACONDA_DEST = $(INSTALLDIR)/anaconda-$(ANACONDA_VERSION)
ANACONDA_PYTHON = $(ANACONDA_DEST)/bin/python
JUPYTERLAB_BUILD = $(BUILDDIR)/jupyterlab
CONDA = $(ANACONDA_DEST)/bin/conda
PIP = $(ANACONDA_DEST)/bin/pip
JUPYTER = $(ANACONDA_DEST)/bin/jupyter
NPM = $(ANACONDA_DEST)/bin/npm

ifeq ($(USE_ANACONDA),true)
  PYTHON_EXE = $(ANACONDA_PYTHON)
  PYTHON_FLAGS = -E
else
  $(warning WARNING: There are no anaconda packages for this system: $(OS), $(ARCH).)
  PYTHON_EXE = $(shell which python)
  PYTHON_FLAGS =
  ifeq ($(PYTHON_EXE),)
    $(error python not found in PATH.)
  else
    $(warning WARNING: Trying to use '$(PYTHON_EXE)' instead.)
  endif
endif
PYTHON = $(PYTHON_EXE) $(PYTHON_FLAGS)

.PHONY: help build install clean python_check python_download jupyterlab-install jupyterlab-extensions-install

.DEFAULT: help

help:
	@echo "-------------------------------------------------------------------------------"
	@echo "TAU Commander installation"
	@echo
	@echo "Usage: make install [INSTALLDIR=$(INSTALLDIR)]"
	@echo "-------------------------------------------------------------------------------"

build: python_check
	$(ECHO)$(PYTHON) setup.py build_scripts --executable "$(PYTHON)"
	$(ECHO)$(PYTHON) setup.py build

install: build
	$(ECHO)$(PYTHON) setup.py install --prefix $(INSTALLDIR)
	$(ECHO)$(INSTALLDIR)/system/configure --minimal
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
	@echo "the \"INSTALLDIR/system/configure\" script to generate TAU configurations."
	@echo "This is especially a good idea if you are a system administrator installing"
	@echo "TAU Commander so that someone else can use it.  Without arguments, the"
	@echo "\"configure\" script will generate as many TAU configurations as it can."
	@echo
	@echo "In short:"
	@echo "  If you are a sysadmin then go run \"INSTALLDIR/system/configure\"."
	@echo "  Otherwise just add \"INSTALLDIR/bin\" to your PATH and get to work."
	@echo "-------------------------------------------------------------------------------"
	@echo

python_check: $(PYTHON_EXE) jupyterlab-install
	@$(PYTHON) -c "import sys; import setuptools;" || (echo "ERROR: setuptools is required." && false)

python_download: $(CONDA_SRC)

$(CONDA): $(ANACONDA_PYTHON)

$(ANACONDA_PYTHON): $(ANACONDA_SRC)
	$(ECHO)bash $< -b -p $(ANACONDA_DEST)
	$(ECHO)touch $(ANACONDA_DEST)/bin/*

$(ANACONDA_SRC):
	$(ECHO)$(MKDIR) $(BUILDDIR)
	$(call download,$(ANACONDA_URL),$(ANACONDA_SRC))

$(JUPYTERLAB_BUILD):
	$(ECHO)$(MKDIR) $(JUPYTERLAB_BUILD)
	$(ECHO)$(CP) jupyterlab $(dir $(JUPYTERLAB_BUILD))

jupyterlab-install: $(CONDA)
	$(ECHO)$(CONDA) list -f jupyterlab | grep jupyterlab | grep -q 0\.27\.0 2>&1 || $(ECHO)$(CONDA) install -y -c conda-forge jupyterlab=0.27.0
	$(ECHO)$(CONDA) list -f bokeh | grep bokeh | grep -q 0\.12\.9 2>&1 || $(ECHO)$(CONDA) install -y -c conda-forge bokeh
	$(ECHO)$(CONDA) list -f nodejs | grep -q nodejs 2>&1 || $(ECHO)$(CONDA) install -y -c conda-forge nodejs
	$(ECHO)$(PIP) list --format=columns | grep faststat 2>&1 || $(ECHO)$(PIP) install faststat

jupyterlab-extensions-install: jupyterlab-install $(JUPYTERLAB_BUILD)
	$(ECHO)$(JUPYTER) labextension list 2>&1 | grep -q jupyterlab-manager || $(ECHO)$(JUPYTER) labextension install @jupyter-widgets/jupyterlab-manager@0.27.0 
	$(ECHO)$(JUPYTER) labextension list 2>&1 | grep -q jupyterlab_bokeh || ($(ECHO)$(CD) $(JUPYTERLAB_BUILD)/jupyerlab_bokeh && $(ECHO)$(NPM) install && $(ECHO)$(JUPYTER) labextension link --no-build)
	$(ECHO)$(JUPYTER) labextension list 2>&1 | grep -q taucmdr_project_selector || ($(ECHO)$(CD) $(JUPYTERLAB_BUILD)/taucmdr_project_selector && $(ECHO)$(NPM) install && $(ECHO)$(JUPYTER) labextension link --no-build)
	$(ECHO)$(JUPYTER) labextension list 2>&1 | grep -q taucmdr_experiment_selector || ($(ECHO)$(CD) $(JUPYTERLAB_BUILD)/taucmdr_experiment_selector && $(ECHO)$(NPM) install && $(ECHO)$(JUPYTER) labextension link --no-build)
	$(ECHO)$(JUPYTER) labextension list 2>&1 | grep -q taucmdr_tam_pane || ($(ECHO)$(CD) $(JUPYTERLAB_BUILD)/taucmdr_tam_pane && $(ECHO)$(NPM) install && $(ECHO)$(JUPYTER) labextension link --no-build)
	$(ECHO)$(JUPYTER) lab build

clean:
	$(ECHO)$(RM) -r $(BUILDDIR) VERSION
