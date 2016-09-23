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
"""Score-P software installation management.

Score-P is a tool suite for profiling, event tracing, and online analysis of HPC applications.
"""

from tau import logger
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler.host import CC, INTEL, IBM, PGI, GNU
from tau.cf.target import X86_64_ARCH, IBM64_ARCH


LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://www.cs.uoregon.edu/research/tau/scorep.tgz'}

LIBRARIES = {None: ['libcube4.a']}


class ScorepInstallation(AutotoolsInstallation):
    """Downloads ScoreP."""
    # Settle down pylint.  Score-P is complex so we need a few extra arguments.
    # pylint: disable=too-many-arguments

    def __init__(self, sources, target_arch, target_os, compilers, 
                 use_mpi, use_shmem, use_binutils, use_libunwind, use_papi, use_pdt):
        super(ScorepInstallation, self).__init__('scorep', 'Score-P', sources, target_arch, target_os, 
                                                 compilers, REPOS, None, LIBRARIES, None)
        self.use_mpi = use_mpi
        self.use_shmem = use_shmem
        for pkg, used in (('binutils', use_binutils), ('libunwind', use_libunwind), 
                          ('papi', use_papi), ('pdt', use_pdt)):
            if used:
                self.add_dependency(pkg, sources)

    def configure(self, flags, env):
        flags.extend(['--enable-shared', '--without-otf2', '--without-opari2', '--without-cube', '--without-gui'])
        if self.target_arch in (X86_64_ARCH, IBM64_ARCH):
            suite_flags = {INTEL: 'intel', IBM: 'ibm', PGI: 'pgi', GNU: 'gcc'}
            family = self.compilers[CC].info.family
            flags.append('--with-nocross-compiler-suite=%s' % suite_flags[family])
        if not self.use_mpi:
            flags.append('--without-mpi')
        if not self.use_shmem:
            flags.append('--without-shmem')
        binutils = self.dependencies.get('binutils')
        libunwind = self.dependencies.get('libunwind')
        papi = self.dependencies.get('papi')
        pdt = self.dependencies.get('pdt')
        if binutils:
            flags.append('--with-libbfd=%s' % binutils.install_prefix)
        if libunwind:
            flags.append('--with-libunwind=%s' % libunwind.install_prefix)
        if papi:       
            flags.append('--with-papi=%s' % papi.install_prefix)
            flags.append('--with-papi-header=%s' % papi.include_path)
            flags.append('--with-papi-lib=%s' % papi.lib_path)
        if pdt:
            flags.append('--with-pdt=%s' % pdt.bin_path)
        return super(ScorepInstallation, self).configure(flags, env)
