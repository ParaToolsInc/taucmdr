###############################################################################
#
# Copyright (c) 2015-2026, ParaTools, Inc.
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
DOCKER_IMG_NAME = taucmdr-dev
UBUNTU_VERSION = 24.04
PYTHON_VERSION = 3.15
DOCKER_TAG = ubuntu$(UBUNTU_VERSION)-py$(PYTHON_VERSION)
# Use distinct system volume names for different distro releases
DOCKER_SYSTEM_VOLUME = taucmdr-system-ubuntu$(UBUNTU_VERSION)

# Shell utilities
RM = rm -f

ifeq ($(VERBOSE),false)
	ECHO=@
else
	ECHO=
endif

.PHONY: help clean dev-container run-container test-container

.DEFAULT: help

help:
	@echo "Usage: make (dev-container|run-container|test-container|clean) [ARGS=...]"

clean:
	$(ECHO)$(RM) -r build dist

# Allocate a terminal only when make is runnning in one so that this works from a script
DOCKER_RUN = docker run -i $$(test -t 0 && echo -t) --rm --tmpfs=/dev/shm:rw,nosuid,nodev,exec --cap-add PERFMON \
	-v ${PWD}:/home/tau/src

dev-container:
	$(ECHO)docker build --pull --build-arg TAU_UID=$$(id -u) --build-arg UBUNTU_VERSION=$(UBUNTU_VERSION) \
	    --build-arg PYTHON_VERSION=$(PYTHON_VERSION) -t $(DOCKER_IMG_NAME):$(DOCKER_TAG) .

run-container:
	$(ECHO)$(DOCKER_RUN) $(DOCKER_IMG_NAME):$(DOCKER_TAG) $(ARGS)

test-container: dev-container
	$(ECHO)$(DOCKER_RUN) -v $(DOCKER_SYSTEM_VOLUME):/home/tau/system -e TAUCMDR_SYSTEM_PREFIX=/home/tau/system \
	    $(DOCKER_IMG_NAME):$(DOCKER_TAG) sh -c '"$$(uv tool dir)/taucmdr/bin/python" scripts/run_tests.py -U $(ARGS)'
