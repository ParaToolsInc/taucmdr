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
"""Program Database Toolkit (PDT) software installation management.

TAU uses PDT for source instrumentation.
"""

import os
from tau import logger, util
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CXX_ROLE, GNU_COMPILERS, INTEL_COMPILERS, PGI_COMPILERS
from tau.cf.target import TAU_ARCH_APPLE, TAU_ARCH_BGQ, X86_64_ARCH, LINUX_OS, TauArch


LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://tau.uoregon.edu/pdt.tgz',
         X86_64_ARCH: {None: 'http://tau.uoregon.edu/pdt.tgz', 
                       LINUX_OS:  'http://tau.uoregon.edu/pdt_lite.tgz'}}

COMMANDS = {None:
            ['cparse',
             'cxxparse',
             'edg33-upcparse',
             'edg44-c-roseparse',
             'edg44-cxx-roseparse',
             'edg44-upcparse',
             'edgcpfe',
             'f90fe',
             'f90parse',
             'f95parse',
             'gfparse',
             'pdbcomment',
             'pdbconv',
             'pdbhtml',
             'pdbmerge',
             'pdbstmt',
             'pdbtree',
             'pdtf90disp',
             'pdtflint',
             'pebil.static',
             'roseparse',
             'smaqao',
             'taucpdisp',
             'tau_instrumentor',
             'upcparse',
             'xmlgen'],
            TAU_ARCH_APPLE.architecture: 
            {TAU_ARCH_APPLE.operating_system: 
             ['cparse',
              'cxxparse',
              'edgcpfe',
              'f90fe',
              'f90parse',
              'f95parse',
              'gfparse',
              'pdbcomment',
              'pdbconv',
              'pdbhtml',
              'pdbmerge',
              'pdbstmt',
              'pdbtree',
              'pdtf90disp',
              'pdtflint',
              'taucpdisp',
              'xmlgen']},
            TAU_ARCH_BGQ.architecture:
            {TAU_ARCH_BGQ.operating_system:
             ['cparse',
              'cxxparse',
              'edg44-c-roseparse',
              'edg44-cxx-roseparse',
              'edg44-upcparse',
              'edgcpfe',
              'f90fe',
              'f90parse',
              'f95parse',
              'gfparse',
              'pdbcomment',
              'pdbconv',
              'pdbhtml',
              'pdbmerge',
              'pdbstmt',
              'pdbtree',
              'pdtf90disp',
              'pdtflint',
              'taucpdisp',
              'tau_instrumentor',
              'xmlgen']}}

class PdtInstallation(AutotoolsInstallation):
    """Encapsulates a PDT installation.
    
    PDT doesn't actually use an Autotools configure script but the installation 
    proceedure is the same otherwise, so we reuse what we can from AutotoolsInstallation.
    """

    def __init__(self, sources, target_arch, target_os, compilers):
        prefix = compilers[CXX_ROLE].info.family.name
        super(PdtInstallation, self).__init__('pdt', 'PDT', prefix, sources, 
                                              target_arch, target_os, compilers, REPOS, COMMANDS, None, None)

    def _change_install_prefix(self, value):
        # PDT puts installation files (bin, lib, etc.) in a magically named subfolder
        super(PdtInstallation, self)._change_install_prefix(value)
        self.arch = TauArch.get(self.target_arch, self.target_os)
        self.arch_path = os.path.join(self.install_prefix, self.arch.name)
        self.bin_path = os.path.join(self.arch_path, 'bin')
        self.lib_path = os.path.join(self.arch_path, 'lib')

    def configure(self, flags, env):
        family_flags = {GNU_COMPILERS.name: '-GNU', 
                        INTEL_COMPILERS.name: '-icpc', 
                        PGI_COMPILERS.name: '-pgCC'}
        family = self.compilers[CXX_ROLE].info.family
        compiler_flag = family_flags.get(family.name, '')
        prefix_flag = '-prefix=%s' % self.install_prefix
        cmd = ['./configure', prefix_flag, compiler_flag]
        LOGGER.info("Configuring PDT for %s compilers...", family)
        if util.create_subprocess(cmd, cwd=self.src_prefix, stdout=False):
            raise SoftwarePackageError('PDT configure failed')
