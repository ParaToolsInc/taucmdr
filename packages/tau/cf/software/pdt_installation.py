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
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import AutotoolsInstallation


LOGGER = logger.getLogger(__name__)

SOURCES = {None: 'http://tau.uoregon.edu/pdt.tgz',
           # Why isn't this called pdt-x86_64.tgz ?? "lite" tells me nothing
           'x86_64': 'http://tau.uoregon.edu/pdt_lite.tgz'}

COMMANDS = {None: ['cparse',
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
            'apple': ['cparse',
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
                      'xmlgen']}


class PdtInstallation(AutotoolsInstallation):
    """
    Encapsulates a PDT installation.
    
    PDT doesn't actually use an Autotools configure script but the installation 
    proceedure is the same otherwise, so we reuse what we can from AutotoolsInstallation.
    """

    def __init__(self, prefix, src, arch, compilers):
        try:
            dst = compilers.CC.wrapped.family
        except AttributeError:
            dst = compilers.CC.family
        super(PdtInstallation, self).__init__('PDT', prefix, src, dst, arch, compilers, SOURCES)
        self.arch_path = os.path.join(self.install_prefix, arch)
        self.bin_path = os.path.join(self.arch_path, 'bin')
        self.lib_path = os.path.join(self.arch_path, 'lib')

    def _verify(self):
        commands = COMMANDS.get(self.arch, COMMANDS[None])
        return super(PdtInstallation,self)._verify(commands=commands)

    def configure(self, flags, env):
        family_flags = {'GNU': '-GNU', 
                        'Intel': '-icpc', 
                        'PGI': '-pgCC',
                        None: ''}
        if self.compilers.CXX.wrapped:
            family = self.compilers.CXX.wrapped.family
        else:
            family = self.compilers.CXX.family
        compiler_flag = family_flags.get(family, family_flags[None])
        prefix_flag = '-prefix=%s' % self.install_prefix
        cmd = ['./configure', prefix_flag, compiler_flag]
        LOGGER.info("Configuring PDT for %s compilers..." % family)
        if self._safe_subprocess(cmd, cwd=self._src_path, stdout=False):
            raise SoftwarePackageError('PDT configure failed')
