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
from tau.error import ConfigurationError
from tau.cf.target import TauArch, X86_64_ARCH, LINUX_OS, DARWIN_OS, IBM_BGQ_ARCH, IBM_CNK_OS, PPC64LE_ARCH
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler.host import CC, CXX, PGI, GNU, INTEL


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
            X86_64_ARCH: 
            {DARWIN_OS: 
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
            IBM_BGQ_ARCH:
            {IBM_CNK_OS:
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
              'xmlgen']},
            PPC64LE_ARCH:
            {LINUX_OS:
             ['cparse',
              'cparse4101',
              'cxxparse',
              'cxxparse4101',
              'edgcpfe',
              'edgcpfe4101',
              'f90parse',
              'f95parse',
              'gfparse',
              'gfparse48',
              'gfparse485',
              'pdbcomment',
              'pdbconv',
              'pdbhtml',
              'pdbmerge',
              'pdbstmt',
              'pdbtree',
              'pdtflint',
              'taucpdisp',
              'taucpdisp4101',
              'tau_instrumentor',
              'xmlgen']}}

class PdtInstallation(AutotoolsInstallation):
    """Encapsulates a PDT installation.
    
    PDT doesn't actually use an Autotools configure script but the installation 
    proceedure is the same otherwise, so we reuse what we can from AutotoolsInstallation.
    """

    def __init__(self, sources, target_arch, target_os, compilers):
        # PDT 3.22 can't be built with PGI compilers so substitute GNU compilers instead
        if compilers[CC].unwrap().info.family is PGI:
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError:
                raise SoftwarePackageError("GNU compilers (required to build PDT) could not be found.")
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super(PdtInstallation, self).__init__('pdt', 'PDT', sources, target_arch, target_os, 
                                              compilers, REPOS, COMMANDS, None, None)
        self.arch = TauArch.get(self.target_arch, self.target_os)
        
    def _calculate_uid(self):
        # PDT only cares about changes in C/C++ compilers
        uid = util.new_uid()
        uid.update(self.src)
        uid.update(self.target_arch.name)
        uid.update(self.target_os.name)
        for role in CC, CXX:
            if role in self.compilers:
                uid.update(self.compilers[role].uid)
        return uid.hexdigest()

    def _set_install_prefix(self, value):
        # PDT puts installation files (bin, lib, etc.) in a magically named subfolder
        super(PdtInstallation, self)._set_install_prefix(value)
        arch_path = os.path.join(self.install_prefix, self.arch.name)
        self.bin_path = os.path.join(arch_path, 'bin')
        self.lib_path = os.path.join(arch_path, 'lib')
    
    def configure(self, flags, env):
        family_flags = {GNU.name: '-GNU', INTEL.name: '-icpc', PGI.name: '-pgCC'}
        family = self.compilers[CXX].info.family
        compiler_flag = family_flags.get(family.name, '')
        prefix_flag = '-prefix=%s' % self.install_prefix
        cmd = ['./configure', prefix_flag, compiler_flag]
        LOGGER.info("Configuring PDT...")
        if util.create_subprocess(cmd, cwd=self.src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('PDT configure failed')
