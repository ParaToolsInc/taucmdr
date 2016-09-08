# -*- coding: utf-8 -*-
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
"""Binutils software installation management.

PAPI is used to measure hardware performance counters.
"""

import os
import sys
import fileinput
from tau import logger
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE

LOGGER = logger.get_logger(__name__)

SOURCES = {None: 'http://icl.cs.utk.edu/projects/papi/downloads/papi-5.4.3.tar.gz'}

LIBRARIES = {None: ['libpapi.a']}


class PapiInstallation(AutotoolsInstallation):
    """Encapsulates a PAPI installation."""

    def __init__(self, prefix, src, target_arch, target_os, compilers, shmem, dependencies, URL):
        dst = os.path.join(target_arch, compilers[CC_ROLE].info.family.name)
        super(PapiInstallation, self).__init__('PAPI', prefix, src, dst, 
                                               target_arch, target_os, compilers, shmem,
                                               dependencies, SOURCES, None, LIBRARIES)

    def _prepare_src(self, reuse=True):
        super(PapiInstallation, self)._prepare_src(reuse)
        self.src_prefix = os.path.join(self.src_prefix, 'src')

    def make(self, flags, env, parallel=True):
        # PAPI's tests often fail to compile, so disable them.
        for line in fileinput.input(os.path.join(self.src_prefix, 'Makefile'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('TESTS =', '#TESTS ='))
        super(PapiInstallation, self).make(flags, env, parallel)


