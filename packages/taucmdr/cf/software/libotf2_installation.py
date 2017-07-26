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
"""libotf2 software installation management.

The OTF2 library  provides an interface to write and read trace data.
"""

import sys
from taucmdr import logger
from taucmdr.error import ConfigurationError
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.platforms import DARWIN, HOST_ARCH, HOST_OS
from taucmdr.cf.compiler.host import CC, CXX, GNU, APPLE_LLVM
from taucmdr.cf.compiler import InstalledCompilerSet



LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://www.vi-hps.org/upload/packages/otf2/otf2-2.1-rc2.tar.gz'}

LIBRARIES = {None: ['libotf2.la', 'libotf2.a', 'python2.7/site-packages/_otf2/_otf2.la']}

HEADERS = {None: ['otf2/otf2.h']}


class Libotf2Installation(AutotoolsInstallation):
    """Encapsulates a libotf2 installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        super(Libotf2Installation, self).__init__('libotf2', 'libotf2', sources, 
                                                  target_arch, target_os, compilers, REPOS, None, LIBRARIES, HEADERS)

    def configure(self, flags, env):
        env['PYTHON'] = sys.executable
        return super(Libotf2Installation, self).configure(flags, env)

    @classmethod
    def minimal(cls):
        """Creates a minimal LibOTF2 configuration for working with legacy data analysis tools.

        Returns:
            Libotf2Installation: Object handle for the LibOTF2 installation.
        """
        sources = {'libotf2': 'download'}
        target_arch = HOST_ARCH
        target_os = HOST_OS
        target_family = APPLE_LLVM if HOST_OS is DARWIN else GNU
        try:
            target_compilers = target_family.installation()
        except ConfigurationError:
            raise SoftwarePackageError("%s compilers (required to build TAU) could not be found." % target_family)
        compilers = InstalledCompilerSet('minimal', Host_CC=target_compilers[CC], Host_CXX=target_compilers[CXX])
        inst = cls(sources, target_arch, target_os, compilers)
        return inst
