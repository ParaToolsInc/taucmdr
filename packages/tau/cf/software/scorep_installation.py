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
"""ScoreP software installation management.

ScoreP is a tool suite for profiling, event tracing, and online analysis of HPC
applications.
"""

import os
from tau import logger
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE

LOGGER = logger.get_logger(__name__)

SOURCES = {None: 'http://www.cs.uoregon.edu/research/tau/scorep.tgz'}


class ScorepInstallation(AutotoolsInstallation):
    """Downloads ScoreP."""

    def __init__(self, prefix, src, target_arch, target_os, compilers, URL):
        dst = os.path.join(target_arch, compilers[CC_ROLE].info.family.name)
        if URL is not None:
            SOURCES[None] = URL
        super(ScorepInstallation, self).__init__('SCOREP', prefix, src, dst, 
                                                 target_arch, target_os, compilers, SOURCES, None, None)

    def dl_src(self, reuse=True):
        """Downloads source code for installation.
        
        Acquires package source code archive file via download.
        """

        super(ScorepInstallation, self).dl_src(reuse)