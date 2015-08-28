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
"""libunwind software installation management.

libunwind is used for symbol resolution during sampling, compiler-based 
instrumentation, and other measurement approaches. 
"""

import os
import glob
from tau import logger, util
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE


LOGGER = logger.get_logger(__name__)

SOURCES = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libunwind-1.1.tar.gz'}
 
LIBS = {None: ['libunwind.a']}


class LibunwindInstallation(AutotoolsInstallation):
    """Encapsulates a libunwind installation."""

    def __init__(self, prefix, src, arch, compilers):
        dst = os.path.join(arch, compilers[CC_ROLE].info.family.name)
        super(LibunwindInstallation, self).__init__('libunwind', prefix, src, dst, arch, compilers, SOURCES)

    def _verify(self, commands=None, libraries=None):
        try:
            libraries = LIBS[self.arch]
        except KeyError:
            libraries = LIBS[None]
        return super(LibunwindInstallation, self)._verify(commands, libraries)
    
    def configure(self, flags, env):
        
        # Handle special target architecture flags
        arch_flags = {'mic_linux': ['--host=x86_64-k1om-linux'], 
                      None: []}
        flags.extend(arch_flags.get(self.arch, arch_flags[None]))
                   
        # Add KNC GNU compilers to PATH if building for KNC
        if self.arch == 'mic_linux':
            k1om_ar = util.which('x86_64-k1om-linux-ar')
            if not k1om_ar:
                for path in glob.glob('/usr/linux-k1om-*'):
                    k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
                    if k1om_ar:
                        break
            env['PATH'] = os.pathsep.join([os.path.dirname(k1om_ar), env.get('PATH', os.environ['PATH'])])
        return super(LibunwindInstallation, self).configure(flags, env)

    def make(self, flags, env, parallel=True):
        """Build libunwind.
        
        libunwind's test programs often fail to build but the library itself 
        compiles just fine, so we just keep pressing on to 'make install' 
        even if 'make' appears to have died.
        """
        # pylint: disable=broad-except
        try:
            super(LibunwindInstallation, self).make(flags, env, parallel)
        except Exception as err:
            LOGGER.debug("libunwind make failed, but continuing anyway: %s", err)
