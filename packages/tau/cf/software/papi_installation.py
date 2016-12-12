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
from tau.cf.compiler.host import CC, CXX
from tau.cf.software.installation import AutotoolsInstallation

LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://icl.utk.edu/projects/papi/downloads/papi-5.5.1.tar.gz'}

LIBRARIES = {None: ['libpapi.a']}


class PapiInstallation(AutotoolsInstallation):
    """Encapsulates a PAPI installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        super(PapiInstallation, self).__init__('papi', 'PAPI', sources, target_arch, target_os, 
                                               compilers, REPOS, None, LIBRARIES, None)

    def _calculate_uid(self):
        # PAPI only cares about changes in C/C++ compilers
        uid = util.new_uid()
        uid.update(self.src)
        uid.update(self.target_arch.name)
        uid.update(self.target_os.name)
        for role in CC, CXX:
            uid.update(self.compilers[role].uid)
        return uid.hexdigest()

    def _prepare_src(self, *args, **kwargs):
        # PAPI's source lives in a 'src' directory instead of the usual top level location
        src_prefix = super(PapiInstallation, self)._prepare_src(*args, **kwargs)
        if os.path.basename(src_prefix) != 'src':
            src_prefix = os.path.join(src_prefix, 'src')
        return src_prefix

    def make(self, flags, env, parallel=True):
        # PAPI's tests often fail to compile, so disable them.
        for line in fileinput.input(os.path.join(self.src_prefix, 'Makefile'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('TESTS =', '#TESTS ='))
        super(PapiInstallation, self).make(flags, env, parallel)


