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
# 1. Configure installation
#
#
# Location for package sources and build files.
BUILD_PREFIX = build
#
#
# If set to "true" then missing packages will be downloaded automatically.
# Otherwise, the packages must be present in BUILD_PREFIX
ALLOW_DOWNLOAD = true
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
MKDIR = mkdir -p
#
#
# Miniconda
MINICONDA_VERSION = Miniconda2-4.0.5
MINICONDA_REPO = https://repo.continuum.io/miniconda
MINICONDA_PREFIX = miniconda
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

# 32-bit OS X isn't supported
ifeq ($(OS),Darwin)
ifeq ($(ARCH),i386)
  $(error Target not supported: $(OS) $(ARCH))
endif
endif

# Build download macro
# Usage: $(call download,source,dest)
ifeq ($(ALLOW_DOWNLOAD),true)
  CURL = $(shell which curl)
  WGET = $(shell which wget)
  ifneq ($(WGET),)
    download = wget -O "$(2)" "$(1)"
  else
    ifneq ($(CURL),)
      download = curl -L "$(1)" > "$(2)"
    else
      $(error Either curl or wget must be in PATH to download packages)
    endif
  endif
else
  download = $(error: Download disabled: $(1) $(2))
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

ifeq ($(VERBOSE),false)
  VERBOSE=@
else
  VERBOSE=
endif

MINICONDA_PKG = $(MINICONDA_VERSION)-$(MINICONDA_OS)-$(MINICONDA_ARCH).sh
MINICONDA_URL = $(MINICONDA_REPO)/$(MINICONDA_PKG)
MINICONDA_PYTHON = $(MINICONDA_PREFIX)/bin/python

#.PHONY: all clean miniconda

all:

$(BUILD_PREFIX):
	$(VERBOSE)$(MKDIR) $(BUILD_PREFIX)

miniconda: $(MINICONDA_PYTHON)
	ls -l $(MINICONDA_PYTHON)

$(MINICONDA_PYTHON): $(BUILD_PREFIX)/$(MINICONDA_PKG)
	$(VERBOSE)bash $< -b -p $(MINICONDA_PREFIX)

$(BUILD_PREFIX)/$(MINICONDA_PKG): $(BUILD_PREFIX)
	@echo "Downloading $(MINICONDA_URL) to $@"
	$(call download,$(MINICONDA_URL),$@)
	$(VERBOSE)touch $@

clean:
	$(RM) $(MINICONDA_PKG)

realclean: clean
	$(RM) -r $(BUILD_PREFIX) $(MINICONDA_PREFIX)

