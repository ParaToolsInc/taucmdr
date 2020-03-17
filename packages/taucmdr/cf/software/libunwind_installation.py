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
import shutil
import fileinput
from taucmdr import logger
from taucmdr.error import ConfigurationError
from taucmdr.cf.platforms import IBM_BGQ, ARM64, PPC64LE, PPC64, CRAY_CNL, LINUX
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.cf.compiler.host import CC, CXX, PGI, GNU



LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libunwind-1.1.tar.gz',
         ARM64: {LINUX: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libunwind-arm64-1.1.tgz'}}

LIBRARIES = {None: ['libunwind.a']}

HEADERS = {None: ['libunwind.h', 'unwind.h']}


class LibunwindInstallation(AutotoolsInstallation):
    """Encapsulates a libunwind installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        # libunwind can't be built with PGI compilers so substitute GNU compilers instead
        if compilers[CC].unwrap().info.family is PGI:
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError:
                raise SoftwarePackageError("GNU compilers (required to build libunwind) could not be found.")
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super(LibunwindInstallation, self).__init__('libunwind', 'libunwind', sources, target_arch, target_os,
                                                    compilers, REPOS, None, LIBRARIES, HEADERS)

    def configure(self, flags):
        """Configure libunwind."""
        os.environ['CC'] = self.compilers[CC].unwrap().absolute_path
        os.environ['CXX'] = self.compilers[CXX].unwrap().absolute_path
        if self.target_arch is IBM_BGQ:
            flags.append('--disable-shared')
            for line in fileinput.input(os.path.join(self._src_prefix, 'src', 'unwind', 'Resume.c'), inplace=1):
                # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
                sys.stdout.write(line.replace('_Unwind_Resume', '_Unwind_Resume_other'))
        elif self.target_os is CRAY_CNL:
            os.environ['CFLAGS'] = '-fPIC'
            os.environ['CXXFLAGS'] = '-fPIC'
            flags.append('--disable-shared')
            flags.append('--disable-minidebuginfo')
        # If needed, fix test so `make install` succeeds more frequently.
        crasher_c = os.path.join(self._src_prefix, 'tests', 'crasher.c')
        if os.path.exists(crasher_c):
            for line in fileinput.input(crasher_c, inplace=1):
                # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
                sys.stdout.write(line.replace('r = c(1);', 'r = 1;'))
        return super(LibunwindInstallation, self).configure(flags)

    def make(self, flags):
        """Build libunwind.

        libunwind's test programs often fail to build but the library itself
        compiles just fine, so we just keep pressing on to 'make install'
        even if 'make' appears to have died.
        """
        # pylint: disable=broad-except
        try:
            super(LibunwindInstallation, self).make(flags)
        except Exception as err:
            LOGGER.debug("libunwind make failed, but continuing anyway: %s", err)


    def make_install(self, flags):
        if self.target_arch in [PPC64, PPC64LE]:
            flags.append('-i')
        super(LibunwindInstallation, self).make_install(flags)

    def installation_sequence(self):
        if self.target_arch is ARM64:
            LOGGER.info("Using pre-built libunwind package from U. Oregon Performance Research Laboratory")
            shutil.move(self._src_prefix, self.install_prefix)
        else:
            super(LibunwindInstallation, self).installation_sequence()
