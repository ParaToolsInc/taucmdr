"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import sys
import subprocess
import taucmd
import shutil
from taucmd import util
from taucmd.pkgs import Package
from taucmd.error import InternalError, PackageError

LOGGER = taucmd.getLogger(__name__)


class BfdPackage(Package):
    """
    GNU binutils package
    """
    
    SOURCES = ['http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/binutils-2.23.2.tar.gz']

    def __init__(self, project):
        super(BfdPackage, self).__init__(project)
        self.prefix = os.path.join(self.project.prefix, 'bfd')

    def install(self, stdout=sys.stdout, stderr=sys.stderr):
        config = self.project.config
        bfd = config['bfd']
        if not bfd:
            raise InternalError('Tried to install bfd when (not config["bfd"])')

        if os.path.isdir(self.prefix):
            LOGGER.debug("BFD already installed at %r" % self.prefix)
            return
        LOGGER.info('Installing BFD at %r' % self.prefix)

        if bfd.lower() == 'download':
            src = self.SOURCES
        elif os.path.isdir(bfd):
            LOGGER.debug('Assuming user-supplied BFD at %r is properly installed' % bfd)
            return
        elif os.path.isfile(bfd):
            src = [bfd]
            LOGGER.debug('Will build BFD from user-specified file %r' % bfd)
        else:
            raise PackageError('Invalid BFD directory %r' % bfd, 
                               'Verify that the directory exists and that you have correct permissions to access it.')
            
        # Configure the source code for this configuration
        srcdir = self._getSource(src, stdout, stderr)
        cmd = self._getConfigureCommand()
        LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Configuring BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('BFD configure failed.')
    
        # Execute make
        cmd = ['make']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Compiling BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('BFD compilation failed.')
    
        # Execute make install
        cmd = ['make', 'install']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Installing BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('BFD installation failed.')
        
        # Cleanup
        LOGGER.debug('Recursively deleting %r' % srcdir)
        shutil.rmtree(srcdir)
        LOGGER.info('BFD installation complete.')
        
    def uninstall(self, stdout=sys.stdout, stderr=sys.stderr):
        LOGGER.debug('Recursively deleting %r' % self.prefix)
        shutil.rmtree(self.prefix)
        LOGGER.info('BFD uninstalled.')

    def _getConfigureCommand(self):
        """
        Returns the command that will configure BFD
        """
        flags = {'CFLAGS': '-fPIC', 
                 'CXXFLAGS': '-fPIC',
                 '--disable-nls': None, 
                 '--disable-werror': None}
        arch_flags = {'bgp': {'CC': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc',
                              'CXX': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-g++'},
                      'bgq': {'CC': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc',
                              'CXX': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-g++'},
                      'rs6000': {'--disable-largefile': None},
                      'ibm64': {'--disable-largefile': None} }
        flags.update(arch_flags.get(self.project.config['target-arch'], {}))
        command = ['./configure', '--prefix=%s' % self.prefix] + ['%s=%s' % i if i[1] else '%s' % i[0] for i in flags.iteritems()]
        LOGGER.debug("BFD configure command: %s" % command)
        return command

    def _getSource(self, sources, stdout, stderr):
        """
        Downloads or copies BFD source code
        """
        for src in sources:
            dst = os.path.join(self.project.source_prefix, os.path.basename(src))
            if src.startswith('http') or src.startswith('ftp'):
                try:
                    util.download(src, dst, stdout, stderr)
                except:
                    continue
            elif src.startswith('file'):
                try:
                    shutil.copy(src, dst)
                except:
                    continue
            else:
                raise InternalError("Don't know how to acquire source file %r" % src)
            src_path = util.extract(dst, self.project.source_prefix)
            os.remove(dst)
            return src_path
        raise PackageError('Failed to get source code')