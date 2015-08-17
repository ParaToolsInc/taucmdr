#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

import os
from tau import logger
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE

LOGGER = logger.getLogger(__name__)

SOURCES = {None: 'http://icl.cs.utk.edu/projects/papi/downloads/papi-5.4.1.tar.gz'}

LIBS = {None: ['libpapi.a']}


class PapiInstallation(AutotoolsInstallation):
    """Encapsulates a PAPI installation.
    
    PAPI is used to measure hardware performance counters.
    """

    def __init__(self, prefix, src, arch, compilers):
#         try:
#             cc_family = compilers.CC.wrapped.family
#         except AttributeError:
#             cc_family = compilers.CC.family
        dst = os.path.join(arch, compilers[CC_ROLE].info.family.name)
        LOGGER.debug("src=%s, dst=%s" % (src, dst))
        super(PapiInstallation,self).__init__('PAPI', prefix, src, dst, arch, compilers, SOURCES)

    def _verify(self):
        libraries = LIBS.get(self.arch, LIBS[None])
        return super(PapiInstallation,self)._verify(libraries=libraries)
    
    def _prepare_src(self):
        # PAPI keeps its source in a subdirectory
        prefix = super(PapiInstallation,self)._prepare_src()
        return os.path.join(prefix, 'src')
