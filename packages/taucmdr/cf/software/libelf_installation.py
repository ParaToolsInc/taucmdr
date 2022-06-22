#
# Copyright (c) 2020, ParaTools, Inc.
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
"""libelf software installation management.


The ELF library provides an interface to read, modify or create ELF files in
            an architecture-independent way.
"""

import os
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.error import ConfigurationError
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.compiler.host import CC, CXX, PGI, GNU, NVHPC

REPOS = {None: ['http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/elfutils-0.180.tar.bz2',
                'https://sourceware.org/elfutils/ftp/0.180/elfutils-0.180.tar.bz2']}

LIBRARIES = {None: ['libelf.a']}

HEADERS = {None: ['libelf.h']}


class LibelfInstallation(AutotoolsInstallation):
    """Encapsulates a libelf installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        if compilers[CC].unwrap().info.family is PGI or compilers[CC].unwrap().info.family is NVHPC :
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError as err:
                raise SoftwarePackageError("GNU compilers (required to build libelf) could not be found.") from err
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super().__init__('libelf', 'libelf', sources,
                                                 target_arch, target_os, compilers, REPOS, None, LIBRARIES, HEADERS)

    def configure(self, flags):
        flags.extend(['--disable-debuginfod'])
        cc = os.environ['CC']
        os.environ['CC'] = GNU.installation()[CC].unwrap().info.command
        ret = super().configure(flags)
        os.environ['CC'] = cc
