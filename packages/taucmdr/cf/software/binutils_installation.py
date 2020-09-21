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
"""Binutils software installation management.

GNU binutils provildes BFD, which TAU uses for symbol resolution during
sampling, compiler-based instrumentation, and other measurement approaches.
"""

import os
import sys
import glob
import shutil
import fileinput
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.cf.compiler.host import CC, CXX, PGI, GNU


LOGGER = logger.get_logger(__name__)

VERSION = '2.27'

REPOS = {None: ['http://ftp.gnu.org/gnu/binutils/binutils-'+VERSION+'.tar.gz',
                'https://mirrors.kernel.org/gnu/binutils/binutils-'+VERSION+'.tar.gz',
                'http://mirror.rit.edu/gnu/binutils/binutils-'+VERSION+'.tar.gz',
                'https://mirror.cyberbits.eu/gnu/binutils/binutils-'+VERSION+'.tar.gz',
                'http://mirror.ufs.ac.za/gnu/binutils/binutils-'+VERSION+'.tar.gz',
                'https://ftp.jaist.ac.jp/pub/GNU/binutils/binutils-'+VERSION+'.tar.gz',
                'http://fs.paratools.com/tau-mirror/binutils-'+VERSION+'.tar.gz']}

LIBRARIES = {None: ['libbfd.a']}


class BinutilsInstallation(AutotoolsInstallation):
    """Encapsulates a GNU binutils installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        # binutils can't be built with PGI compilers so substitute GNU compilers instead
        if compilers[CC].unwrap().info.family is PGI:
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError:
                raise SoftwarePackageError("GNU compilers (required to build binutils) could not be found.")
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super(BinutilsInstallation, self).__init__('binutils', 'GNU Binutils', sources,
                                                   target_arch, target_os, compilers, REPOS, None, LIBRARIES, None)

    def configure(self, flags):
        from taucmdr.cf.platforms import DARWIN, IBM_BGP, IBM_BGQ, INTEL_KNC
        flags.extend(['--disable-nls', '--disable-werror'])
        for var in 'CPP', 'CC', 'CXX', 'FC', 'F77', 'F90':
            os.environ.pop(var, None)
        if self.target_os is DARWIN:
            flags.append('CFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC')
            flags.append('CXXFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC')
        else:
            flags.append('CFLAGS=-fPIC')
            flags.append('CXXFLAGS=-fPIC')
        if self.target_arch is IBM_BGP:
            flags.append('CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc')
            flags.append('CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-g++')
        elif self.target_arch is IBM_BGQ:
            flags.append('CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc')
            flags.append('CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-g++')
        elif self.target_arch.is_ibm():
            flags.append('--disable-largefile')
        elif self.target_arch is INTEL_KNC:
            k1om_ar = util.which('x86_64-k1om-linux-ar')
            if not k1om_ar:
                for path in glob.glob('/usr/linux-k1om-*'):
                    k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
                    if k1om_ar:
                        break
                else:
                    raise ConfigurationError("Cannot find KNC native compilers in /usr/linux-k1om-*")
            os.environ['PATH'] = os.pathsep.join((os.path.dirname(k1om_ar), os.environ['PATH']))
            flags.append('--host=x86_64-k1om-linux')
        return super(BinutilsInstallation, self).configure(flags)

    def make_install(self, flags):
        super(BinutilsInstallation, self).make_install(flags)
        LOGGER.debug("Copying missing BFD headers")
        for hdr in glob.glob(os.path.join(self._src_prefix, 'bfd', '*.h')):
            shutil.copy(hdr, self.include_path)
        for hdr in glob.glob(os.path.join(self._src_prefix, 'include', '*')):
            try:
                shutil.copy(hdr, self.include_path)
            except IOError:
                dst = os.path.join(self.include_path, os.path.basename(hdr))
                shutil.copytree(hdr, dst)
        LOGGER.debug("Copying missing libiberty libraries")
        shutil.copy(os.path.join(self._src_prefix, 'libiberty', 'libiberty.a'), self.lib_path)
        shutil.copy(os.path.join(self._src_prefix, 'opcodes', 'libopcodes.a'), self.lib_path)
        LOGGER.debug("Fixing BFD header")
        for line in fileinput.input(os.path.join(self.include_path, 'bfd.h'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('#if !defined PACKAGE && !defined PACKAGE_VERSION', '#if 0'))

    def compiletime_config(self, opts=None, env=None):
        """Configure compilation environment to use this software package.

        Don't put `self.bin_path` in PATH since this offends ``ld`` on some systems.

        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.

        Returns:
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        return list(set(opts)), env

    def runtime_config(self, opts=None, env=None):
        """Configure runtime environment to use this software package.

        Don't put `self.bin_path` in PATH since this offends ``ld`` on some systems
        but do put `self.lib_path` in LD_LIBRARY_PATH.

        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.

        Returns:
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        if os.path.isdir(self.lib_path):
            if sys.platform == 'darwin':
                library_path = 'DYLD_LIBRARY_PATH'
            else:
                library_path = 'LD_LIBRARY_PATH'
            try:
                env[library_path] = os.pathsep.join([self.lib_path, env[library_path]])
            except KeyError:
                env[library_path] = self.lib_path
        return list(set(opts)), env
