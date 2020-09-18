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
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.cf.platforms import TauMagic, X86_64, INTEL_KNL, IBM_BGQ, PPC64LE, LINUX, DARWIN, IBM_CNK,\
    ARM64
from taucmdr.cf.compiler.host import CC, CXX, PGI, GNU, INTEL


LOGGER = logger.get_logger(__name__)

REPOS = {None: [
    'http://tau.uoregon.edu/pdt.tgz',
    'http://fs.paratools.com/tau-mirror/pdt.tgz'
    ],
         X86_64: {None: [
             'http://tau.uoregon.edu/pdt.tgz',
             'http://fs.paratools.com/tau-mirror/pdt.tgz'
         ],
                  LINUX:  [
                      'http://tau.uoregon.edu/pdt_lite.tgz',
                      'http://fs.paratools.com/tau-mirror/pdt_lite.tgz'
                    ]},
         INTEL_KNL: {None: [
             'http://tau.uoregon.edu/pdt.tgz',
             'http://fs.paratools.com/tau-mirror/pdt.tgz'
         ],
                     LINUX:  [
                         'http://tau.uoregon.edu/pdt_lite.tgz',
                         'http://fs.paratools.com/tau-mirror/pdt_lite.tgz'
                     ]}}

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
            X86_64:
            {DARWIN:
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
            IBM_BGQ:
            {IBM_CNK:
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
            PPC64LE:
            {LINUX:
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
              'xmlgen']},
            ARM64:
            {LINUX:
             ['cparse',
              'cparse410',
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
    procedure is the same otherwise, so we reuse what we can from AutotoolsInstallation.
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
        self.tau_magic = TauMagic.find((self.target_arch, self.target_os))
        # PDT puts installation files (bin, lib, etc.) in a magically named subfolder
        self._bin_subdir = os.path.join(self.tau_magic.name, 'bin')
        self._lib_subdir = os.path.join(self.tau_magic.name, 'lib')
        # Work around brokenness in edg4x-rose installer
        self._retry_verify = True

    def _configure_edg4x_rose(self):
        LOGGER.info('edg4x-rose parser configuration failed.  Retrying...')
        cwd = os.path.join(self.install_prefix, 'contrib', 'rose', 'edg44', self.tau_magic.name, 'roseparse')
        if not os.path.exists(cwd):
            LOGGER.info("roseparse not available on %s.  Good luck!", self.tau_magic.name)
            return
        if util.create_subprocess(['./configure'], cwd=cwd, stdout=False, show_progress=True):
            raise SoftwarePackageError('Unable to configure edg4x-rose parsers')
        LOGGER.info("'edg4x-rose parser configuration successful.  Continuing %s verification...", self.title)

    def verify(self):
        # Sometimes PDT doesn't build the edg44 rose parsers even though they could be built.
        # If verification fails, try configuring those parsers and see if it helps.
        try:
            super(PdtInstallation, self).verify()
        except SoftwarePackageError as err:
            if not (os.path.exists(self.install_prefix) and self._retry_verify):
                raise err
            self._configure_edg4x_rose()
            self._retry_verify = False
            self.verify()

    def configure(self, _):
        family_flags = {GNU.name: '-GNU', INTEL.name: '-icpc', PGI.name: '-pgCC'}
        compiler_flag = family_flags.get(self.compilers[CXX].info.family.name, '')
        cmd = ['./configure', '-prefix=' + self.install_prefix, compiler_flag]
        LOGGER.info("Configuring PDT...")
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('%s configure failed' % self.title)
