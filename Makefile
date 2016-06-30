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

###############################################################################
# 1. Configuration
#
#
# TAU Commander version
VERSION = $(shell cat VERSION)
#
#
# Installation location
DESTDIR = $(HOME)/taucmdr-$(VERSION)
#
#
# Location for package sources and build files.
BUILDDIR = build
#
#
# If set to "true" then missing packages will be downloaded automatically.
# Otherwise, the packages must be present in BUILDDIR
DOWNLOAD = true
#
#
# If set to "true" then show commands as they are executed.
# Otherwise only the command's output will be shown.
VERBOSE = true
#
#
# END Configure installation
###############################################################################

###############################################################################
# 2. Advanced configuration (probably best left as is)
#
#
# Shell utilities
RM = rm -f
MV = mv -f
CP = cp -f
MKDIR = mkdir -p
#
#
# TAU
TAU_VERSION = 2.25.1
TAU_REPO = https://www.cs.uoregon.edu/research/tau/tau_releases
#
#
# PDT
PDT_VERSION = 3.22
PDT_REPO = https://www.cs.uoregon.edu/research/tau/pdt_releases
#
#
# Miniconda
MINICONDA_VERSION = 4.0.5
MINICONDA_REPO = https://repo.continuum.io/miniconda
#
#
# END Advanced configuration
###############################################################################


###############################################################################
# ---------------------------- END CONFIGURATION ---------------------------- #
###############################################################################

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

# 32-bit OS X isn't supported
ifeq ($(OS),Darwin)
ifeq ($(ARCH),i386)
  $(error Target not supported: $(OS) $(ARCH))
endif
endif

# Build download macro
# Usage: $(call download,source,dest)
ifeq ($(DOWNLOAD),true)
  CURL = $(shell which curl)
  WGET = $(shell which wget)
  ifneq ($(WGET),)
    download = wget $(WGET_FLAGS) -O "$(2)" "$(1)"
  else
    ifneq ($(CURL),)
      download = curl $(CURL_FLAGS) -L "$(1)" > "$(2)"
    else
      $(error Either curl or wget must be in PATH to download packages)
    endif
  endif
else
  download = @echo "ERROR: $(2) is missing and download is disabled" && false
endif

# Configure packages to match target OS
ifeq ($(OS),Darwin)
  MINICONDA_OS = MacOSX
else 
  ifeq ($(OS),Linux)
    MINICONDA_OS = Linux  
  else
    $(error OS not supported: $(OS))
  endif
endif

# Configure packages to match target architecture
ifeq ($(ARCH),x86_64)
  MINICONDA_ARCH = x86_64
else 
  ifeq ($(ARCH),i386)
    MINICONDA_ARCH = x86
  else
    $(error Architecture not supported: $(ARCH))
  endif
endif

SYSTEM_SRC = $(DESTDIR)/.system/src

TAUCMDR_PKG = taucmdr-$(VERSION).tar.gz
TAUCMDR_SRC = $(BUILDDIR)/$(TAUCMDR_PKG)
TAUCMDR_DEST = $(DESTDIR)

TAU_PKG = tau-$(TAU_VERSION).tar.gz
TAU_URL = $(TAU_REPO)/$(TAU_PKG)
TAU_SRC = $(BUILDDIR)/$(TAU_PKG)
TAU_DEST = $(SYSTEM_SRC)
TAU_SYSTEM_SRC = $(TAU_DEST)/$(TAU_PKG)

PDT_PKG = pdt-$(PDT_VERSION).tar.gz
PDT_URL = $(PDT_REPO)/$(PDT_PKG)
PDT_SRC = $(BUILDDIR)/$(PDT_PKG)
PDT_DEST = $(SYSTEM_SRC)
PDT_SYSTEM_SRC = $(PDT_DEST)/$(PDT_PKG)

MINICONDA_PKG = Miniconda2-$(MINICONDA_VERSION)-$(MINICONDA_OS)-$(MINICONDA_ARCH).sh
MINICONDA_URL = $(MINICONDA_REPO)/$(MINICONDA_PKG)
MINICONDA_SRC = $(BUILDDIR)/$(MINICONDA_PKG)
MINICONDA_DEST = $(DESTDIR)/miniconda

TAU = $(TAUCMDR_DEST)/bin/tau
PYTHON = $(MINICONDA_DEST)/bin/python

.PHONY: all install clean

.DEFAULT: all

all: $(MINICONDA_SRC) $(TAU_SRC) $(PDT_SRC)
	@touch $(BUILDDIR)/*
	@echo "Type \`make install\` to install TAU Commander."

install: system_target
	$(ECHO)$(TAU) --version
	@echo "TAU Commander installed at $(DESTDIR)"
	@echo "Rememember to add $(DESTDIR)/bin to your PATH"

system_target: $(TAU) $(TAU_SYSTEM_SRC) $(PDT_SYSTEM_SRC)
	$(ECHO)$(TAU) target create $(HOSTNAME) -@ system --tau=$(TAU_SYSTEM_SRC) --pdt=$(PDT_SYSTEM_SRC)

$(TAU): $(TAUCMDR_SRC)
	$(ECHO)tar xvzf $(TAUCMDR_SRC) -C "$(DESTDIR)" --strip-components=1
	@echo "Compiling python files..."
	$(ECHO)$(PYTHON) -m compileall $(DESTDIR) || true

$(TAUCMDR_SRC): $(PYTHON)
	$(ECHO)$(PYTHON) setup.py sdist -d $(BUILDDIR)
	@touch $(BUILDDIR)/*

$(PYTHON): $(MINICONDA_SRC)
	$(ECHO)bash $< -b -p $(MINICONDA_DEST)
# Update timestamps on miniconda python files or Make will think miniconda
# is always out of date since the source file will have a newer timestamp
	@echo "Updating miniconda time stamps..."
	$(ECHO)find $(MINICONDA_DEST) -name python -exec touch {} \;

$(TAU_SYSTEM_SRC): $(TAU_SRC) $(TAU_DEST) 
	$(ECHO)$(CP) $(TAU_SRC) $@

$(PDT_SYSTEM_SRC): $(PDT_SRC) $(PDT_DEST)
	$(ECHO)$(CP) $(PDT_SRC) $@

$(TAU_SRC): $(BUILDDIR)
	$(call download,$(TAU_URL),$@)

$(PDT_SRC): $(BUILDDIR)
	$(call download,$(PDT_URL),$@)

$(MINICONDA_SRC): $(BUILDDIR)
	$(call download,$(MINICONDA_URL),$@)

$(SYSTEM_SRC):
	$(ECHO)$(MKDIR) $(SYSTEM_SRC)

$(BUILDDIR):
	$(ECHO)$(MKDIR) $(BUILDDIR)

clean: 
ifeq ($(DOWNLOAD),true)
	$(ECHO)$(RM) -r $(BUILDDIR)
else
	@echo "Refusing to make clean since DOWNLOAD=$(DOWNLOAD) so we might not be able to recover."
	@echo "If you still want to make clean execute:"
	@echo "  $(RM) -r $(BUILDDIR)"
endif

