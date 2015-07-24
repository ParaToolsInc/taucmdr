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
import glob
import shutil
from tau import logger, util
from tau.error import ConfigurationError, SoftwarePackageError


LOGGER = logger.getLogger(__name__)

DEFAULT_SOURCE = {
    None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/binutils-2.23.2.tar.gz'}

LIBS = {None: ['libbfd.a']}


class BfdInstallation(object):
    """
    Encapsulates a BFD installation
    """
    def __init__(self, prefix, cxx, src, arch):
        self.src = src
        if src.lower() == 'download':
            try:
                self.src = DEFAULT_SOURCE[arch]
            except KeyError:
                self.src = DEFAULT_SOURCE[None]
        self.prefix = prefix
        self.cxx = cxx
        self.arch = arch
        if os.path.isdir(src):
            self.bfd_prefix = src
        else:
            compiler_prefix = str(cxx.eid) if cxx else 'unknown'
            self.bfd_prefix = os.path.join(prefix, 'bfd', compiler_prefix)
        self.src_prefix = os.path.join(prefix, 'src')
        self.include_path = os.path.join(self.bfd_prefix, 'include')
        self.bin_path = os.path.join(self.bfd_prefix, 'bin')
        self.lib_path = os.path.join(self.bfd_prefix, 'lib')

    def verify(self):
        """
        Returns true if if there is a working BFD installation at `prefix` with a
        directory named `arch` containing  `lib` directories or 
        raises a ConfigurationError describing why that installation is broken.
        """
        LOGGER.debug("Checking BFD installation at '%s' targeting arch '%s'" % (
            self.bfd_prefix, self.arch))
        if not os.path.exists(self.bfd_prefix):
            raise ConfigurationError(
                "'%s' does not exist" % self.bfd_prefix)
        # Check for all libraries
        try:
            libraries = LIBS[self.arch]
            LOGGER.debug("Checking %s BFD libraries" % libraries)
        except KeyError:
            libraries = LIBS[None]
            LOGGER.debug("Checking default BFD libraries")
        for lib in libraries:
            path = os.path.join(self.lib_path, lib)
            if not os.path.exists(path):
                raise ConfigurationError("'%s' is missing" % path)
#      if not os.access(path, os.X_OK):
#        raise ConfigurationError("'%s' exists but is not executable" % path)

        LOGGER.debug("BFD installation at '%s' is valid" % self.bfd_prefix)
        return True
    
    def _configure(self, srcdir):
        """Configures BFD.
        
        Constructs and executes a configuration command line.
        May also set environment variables to prep for configuration.
        
        Args:
            srcdir: Absolute path to the source directory
            
        Raises:
            SoftwarePackageError: The configuration subprocess failed.
        """ 

        compiler_flags = {'GNU': ['CC=gcc', 'CXX=g++'],
                          'Intel': ['CC=icc', 'CXX=icpc']}

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
                                      # TODO: Pass the right host arch, not
                                      # TAU's magic host words
                                      '--host=%s' % self.arch],
                      'mic_linux': ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                    '--host=x86_64-k1om-linux',
                                    '--disable-nls', '--disable-werror'],
                      'apple': ['CFLAGS="-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC"', 
                                'CXXFLAGS="-Wno-error=unused-value -Wno-error=deprecated-declarations -fPIC"',
                                '--disable-nls', '--disable-werror'],
                      'sparc64fx': ['CFLAGS="-fPIC -Xg"',
                                    'CXXFLAGS="-fPIC -Xg"',
                                    'AR=sparc64-unknown-linux-gnu-ar',
                                    '--host=sparc64-unknown-linux-gnu',
                                    '--disable-nls', '--disable-werror'],
                      # TODO: craycnl with MIC
                      None: ['CFLAGS=-fPIC', 'CXXFLAGS=-fPIC',
                                  '--disable-nls', '--disable-werror']}

        flags = ['-prefix=%s' % self.bfd_prefix]
        try:
            flags += compiler_flags[self.cxx['family']]
        except:
            LOGGER.info("Allowing BFD to select compilers")
        try:
            flags += arch_flags[self.arch]
        except KeyError:
            flags += arch_flags[None]
            
        if self.arch == 'arm_android':
            # TODO: Android
            #patch -p1 <$START_DIR/android.binutils-2.23.2.patch
            pass
        elif self.arch == 'mic_linux':
            # TODO: MIC
            # Note: may need to search other paths than just /usr/linux-k1om-*
            #k1om_bin="`ls -1d /usr/linux-k1om-* | sort -r | head -1`/bin"
            #export PATH=$k1om_bin:$PATH
            pass
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
        cmd = ['./configure'] + flags
        LOGGER.info("Configuring BFD...")
        if util.createSubprocess(cmd, cwd=srcdir, stdout=False):
            raise SoftwarePackageError('BFD configure failed')


    def install(self, force_reinstall=False):
        """
        TODO: Docs
        """
        LOGGER.debug("Initializing BFD at '%s' from '%s' with arch=%s" %
                     (self.bfd_prefix, self.src, self.arch))

        # Check if the installation is already initialized
        if not force_reinstall:
            try:
                return self.verify()
            except ConfigurationError, err:
                LOGGER.debug(err)
        LOGGER.info('Starting BFD installation')

        # Download, unpack, or copy BFD source code
        dst = os.path.join(self.src_prefix, os.path.basename(self.src))
        try:
            util.download(self.src, dst)
            srcdir = util.extract(dst, self.src_prefix)
        except IOError as err:
            raise ConfigurationError("Cannot acquire source file '%s': %s" % 
                                     (self.src, err),
                                     "Check that the file is accessable")
        finally:
            try:
                os.remove(dst)
            except:
                pass

        try:
            # Configure
            self._configure(srcdir)

            # Build
            cmd = ['make', '-j4']
            LOGGER.info("Compiling BFD...")
            if util.createSubprocess(cmd, cwd=srcdir, stdout=False):
                raise SoftwarePackageError('BFD compilation failed.')

            # Install
            cmd = ['make', 'install']
            LOGGER.info("Installing BFD...")
            if util.createSubprocess(cmd, cwd=srcdir, stdout=False):
                raise SoftwarePackageError(
                    'BFD installation failed before verifcation.')
                
            # Some systems use lib64 instead of lib
            if (os.path.isdir(self.lib_path+'64') and not os.path.isdir(self.lib_path)):
                os.symlink(self.lib_path+'64', self.lib_path)

            LOGGER.info(
                "Copying headers from BFD source to install 'include'.")
            for f in glob.glob(os.path.join(srcdir, 'bfd', '*.h')):
                shutil.copy(f, self.include_path)
            for f in glob.glob(os.path.join(srcdir, 'include', '*')):
                try:
                    shutil.copy(f, self.include_path)
                except:
                    dst = os.path.join(
                        self.include_path, os.path.basename(f))
                    shutil.copytree(f, dst)

            # cp additional libraries:
            LOGGER.info("Copying missing libraries to install 'lib'.")
            shutil.copy(
                os.path.join(srcdir, 'libiberty', 'libiberty.a'), self.lib_path)
            shutil.copy(
                os.path.join(srcdir, 'opcodes', 'libopcodes.a'), self.lib_path)

            # fix bfd.h header in the install include location
            LOGGER.info("Fixing BFD header in install 'include' location.")
            with open(os.path.join(self.include_path, 'bfd.h'), "r+") as myfile:
                data = myfile.read().replace(
                    '#if !defined PACKAGE && !defined PACKAGE_VERSION', '#if 0')
                myfile.seek(0, 0)
                myfile.write(data)

        except Exception as err:
            LOGGER.info("BFD installation failed, cleaning up %s " % err)
            shutil.rmtree(self.bfd_prefix, ignore_errors=True)
        finally:
            # Always clean up BFD source
            LOGGER.debug('Deleting %r' % srcdir)
            shutil.rmtree(srcdir, ignore_errors=True)

        # Verify the new installation
        try:
            retval = self.verify()
        except Exception as err:
            # Installation failed, clean up any failed install files
            shutil.rmtree(self.bfd_prefix, ignore_errors=True)
            raise SoftwarePackageError(
                'BFD installation failed verification: %s' % err)
        else:
            LOGGER.info('BFD installation complete')
            return retval

    def applyCompiletimeConfig(self, opts, env):
        """
        TODO: Docs
        """
        env['PATH'] = os.pathsep.join([self.bin_path, env.get('PATH')])

    def getRuntimeConfig(self, opts, env):
        """
        TODO: Docs
        """
        pass
