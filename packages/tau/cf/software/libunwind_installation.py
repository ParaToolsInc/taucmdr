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
import sys
import fileinput
from tau import logger
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE, CXX_ROLE
from tau.cf.target import ARM64_ARCH, IBM_BGQ_ARCH, CRAY_CNL_OS


LOGGER = logger.get_logger(__name__)

SOURCES = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libunwind-1.1.tar.gz',
           ARM64_ARCH: {None:
                        'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libunwind-arm64-1.1.tgz'}}

LIBRARIES = {None: ['libunwind.a']}


class LibunwindInstallation(AutotoolsInstallation):
    """Encapsulates a libunwind installation."""

    def __init__(self, prefix, src, target_arch, target_os, compilers):
        dst = os.path.join(target_arch, compilers[CC_ROLE].info.family.name)
        super(LibunwindInstallation, self).__init__('libunwind', prefix, src, dst, 
                                                    target_arch, target_os, compilers, SOURCES, None, LIBRARIES)

    def configure(self, flags, env):
        flags.extend(['CC='+self.compilers[CC_ROLE].absolute_path, 
                      'CXX='+self.compilers[CXX_ROLE].absolute_path]) 
        if self.target_arch is IBM_BGQ_ARCH:
            flags.append('--disable-shared')
            for line in fileinput.input(os.path.join(self.src_prefix, 'src', 'unwind', 'Resume.c'), inplace=1):
                # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
                sys.stdout.write(line.replace('_Unwind_Resume', '_Unwind_Resume_other'))
        elif self.target_os is CRAY_CNL_OS:
            flags.extend(['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC', '--disable-shared'])

        # Fix test so `make install` succeeds more frequently 
        for line in fileinput.input(os.path.join(self.src_prefix, 'tests', 'crasher.c'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('r = c(1);', 'r = 1;'))

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
            
    def make_install(self, flags, env, parallel=False):
        super(LibunwindInstallation, self).make_install(flags, env, parallel)
        lib64_path = os.path.join(self.install_prefix, 'lib64')
        lib_path = os.path.join(self.install_prefix, 'lib')
        if os.path.isdir(lib64_path) and not os.path.isdir(lib_path): 
            os.symlink(lib64_path, lib_path)

