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
from tau import logger, util
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import CC_ROLE


LOGGER = logger.get_logger(__name__)
 
SOURCES = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/binutils-2.23.2.tar.gz'}

LIBS = {None: ['libbfd.a']}


class BinutilsInstallation(AutotoolsInstallation):
    """Encapsulates a GNU binutils installation."""
    
    def __init__(self, prefix, src, arch, compilers):
        dst = os.path.join(arch, compilers[CC_ROLE].info.family.name)
        super(BinutilsInstallation, self).__init__('binutils', prefix, src, dst, arch, compilers, SOURCES)

    def _verify(self, commands=None, libraries=None):
        try:
            libraries = LIBS[self.arch]
        except KeyError:
            libraries = LIBS[None]
        return super(BinutilsInstallation, self)._verify(commands, libraries)
    
    def configure(self, flags, env):
        arch_flags = {'bgp': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                              'CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc',
                              'CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-g++',
                              '--disable-nls', '--disable-werror'],
                      'bgq': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                              'CC=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc',
                              'CXX=/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-g++',
                              '--disable-nls', '--disable-werror'],
                      'rs6000': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                 '--disable-nls', '--disable-werror',
                                 '--disable-largefile'],
                      'ibm64': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                '--disable-nls', '--disable-werror',
                                '--disable-largefile'],
                      'arm_android': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                      '--disable-nls', '--disable-werror',
                                      '--disable-largefile',
                                      '--host=%s' % self.arch],
                      'mic_linux': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                    '--host=x86_64-k1om-linux',
                                    '--disable-nls', '--disable-werror'],
                      'apple': ['CFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC', 
                                'CXXFLAGS=-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC',
                                '--disable-nls', '--disable-werror'],
                      'sparc64fx': ['CFLAGS="-fPIC -Xg"',
                                    'CXXFLAGS="-fPIC -Xg"',
                                    'AR=sparc64-unknown-linux-gnu-ar',
                                    '--host=sparc64-unknown-linux-gnu',
                                    '--disable-nls', '--disable-werror'],
                      None: ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                             '--disable-nls', '--disable-werror']}

        flags.extend(arch_flags.get(self.arch, arch_flags[None]))
            
        if self.arch == 'arm_android':
            # TODO: Android
            #patch -p1 <$START_DIR/android.binutils-2.23.2.patch
            pass
        elif self.arch == 'mic_linux':
            k1om_ar = util.which('x86_64-k1om-linux-ar')
            if not k1om_ar:
                for path in glob.glob('/usr/linux-k1om-*'):
                    k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
                    if k1om_ar:
                        break
            env['PATH'] = os.pathsep.join([os.path.dirname(k1om_ar), env.get('PATH', os.environ['PATH'])])
        elif self.arch == 'sparc64fx':
            # TODO: SPARC64
            #fccpxpath=`which fccpx | sed 's/\/bin\/fccpx$//'`
            #if [ -r $fccpxpath/util/bin/sparc64-unknown-linux-gnu-ar ]; then
            #  echo "NOTE: Using ar from $fccpxpath/util/bin/sparc64-unknown-linux-gnu-ar"
            #  export PATH=$fccpxpath/util/bin:$PATH
            #fi
            #./configure \
            #    CFLAGS="-fPIC -Xg" CXXFLAGS="-fPIC -Xg" \
            #        CC=$fccpxpath/bin/fccpx \
            #        CXX=$fccpxpath/bin/FCCpx \
            #        AR=sparc64-unknown-linux-gnu-ar \
            #        --host=sparc64-unknown-linux-gnu \
            #        --prefix=$bfddir \
            #        --disable-nls --disable-werror > tau_configure.log 2>&1
            pass
        #TODO: Cray with MIC
#         elif CRAY_WITH_MIC:
#           craycnl)
#             unset CC CXX
#             if [ $craymic = yes ]; then
#               # Note: may need to search other paths than just /usr/linux-k1om-*
#               k1om_bin="`ls -1d /usr/linux-k1om-* | sort -r | head -1`/bin"
#               export PATH=$k1om_bin:$PATH
#               ./configure \
#                 CFLAGS='-mmic -fPIC' CXXFLAGS='-mmic -fPIC' \
#                 --host=x86_64-k1om-linux \
#                 --prefix=$bfddir \
#                 --disable-nls --disable-werror > tau_configure.log 2>&1
#               err=$?
#             else
#               ./configure \
#                 CFLAGS=-fPIC CXXFLAGS=-fPIC \
#                 --prefix=$bfddir \
#                 --disable-nls --disable-werror > tau_configure.log 2>&1
#               err=$?
#             fi
        return super(BinutilsInstallation, self).configure(flags, env)
    
    def make_install(self, flags, env, parallel=False):
        super(BinutilsInstallation, self).make_install(flags, env, parallel)

        LOGGER.debug("Copying missing BFD headers")
        for hdr in glob.glob(os.path.join(self._src_path, 'bfd', '*.h')):
            shutil.copy(hdr, self.include_path)
        for hdr in glob.glob(os.path.join(self._src_path, 'include', '*')):
            try:
                shutil.copy(hdr, self.include_path)
            except:
                dst = os.path.join(self.include_path, os.path.basename(hdr))
                shutil.copytree(hdr, dst)

        LOGGER.debug("Copying missing libiberty libraries")
        shutil.copy(os.path.join(self._src_path, 'libiberty', 'libiberty.a'), self.lib_path)
        shutil.copy(os.path.join(self._src_path, 'opcodes', 'libopcodes.a'), self.lib_path)

        LOGGER.debug("Fixing BFD header")
        for line in fileinput.input(os.path.join(self.include_path, 'bfd.h'), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('#if !defined PACKAGE && !defined PACKAGE_VERSION', '#if 0'))
