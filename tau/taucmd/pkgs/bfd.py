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
from taucmd.error import InternalError

LOGGER = taucmd.getLogger(__name__)


class Bfd(Package):
    """
    GNU binutils package
    """
    
    PROVIDES = ['bfd']
    REQUIRES = []
    EXCLUDES = []
    SOURCES = ['http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/binutils-2.23.2.tar.gz']

    def __init__(self, project):
        self.project = project
        self.prefix = os.path.join(self.project.prefix, 'bfd') 

    def install(self, stdout=sys.stdout, stderr=sys.stderr):
        config = self.project.config
        bfd = config['bfd']
        if not bfd:
            raise InternalError('Tried to install bfd when (not config["bfd"])')

        if bfd.lower() == 'download':
            src = SOURCES
        if os.path.isdir(bfd):
            src = []
            LOGGER.debug('Assuming user-supplied BFD at %r is properly installed' % bfd)
        elif os.path.isfile(bfd):
            src = [bfd]
            LOGGER.debug('Will build BFD from user-specified file %r' % bfd)
        else:
            
            raise taucmd.Error('Invalid BFD directory %r' % bfd)
        
        # Banner
        LOGGER.info('Installing BFD at %r' % prefix)

        # Configure the source code for this configuration
        srcdir = BFD_SRC_DIR
        cmd = getConfigureCommand(config)
        LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Configuring BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        #proc = subprocess.Popen(' '.join(cmd), cwd=srcdir, stdout=stdout, stderr=stderr, shell=True)
        if proc.wait():
            shutil.rmtree(prefix, ignore_errors=True)
            raise taucmd.Error('BFD configure failed.')
    
        # Execute make
        cmd = ['make']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Compiling BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        #proc = subprocess.Popen(' '.join(cmd), cwd=srcdir, stdout=stdout, stderr=stderr, shell=True)
        if proc.wait():
            shutil.rmtree(prefix, ignore_errors=True)
            raise taucmd.Error('BFD compilation failed.')
    
        # Execute make install
        cmd = ['make', 'install']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Installing BFD...')
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        #proc = subprocess.Popen(' '.join(cmd), cwd=srcdir, stdout=stdout, stderr=stderr, shell=True)
        if proc.wait():
            shutil.rmtree(prefix, ignore_errors=True)
            raise taucmd.Error('BFD compilation failed.')
        
        # Cleanup
        shutil.rmtree(srcdir)
        LOGGER.debug('Recursively deleting %r' % srcdir)
        LOGGER.info('BFD installation complete.')
      
    def _getConfigureCommand(self):
        """
        Returns the command that will configure BFD for this project
        """
        base_flags = {'CFLAGS': '-fPIC', 
                      'CXXFLAGS': '-fPIC',
                      '--disable-nls': None, 
                      '--disable-werror': None}
        arch_flags = {'bgp': {'CC': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc',
                              'CXX': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-g++'},
                      'bgq': {'CC': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc',
                              'CXX': '/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-g++'},
                      'rs6000': {'--disable-largefile': None},
                      'ibm64': {'--disable-largefile': None} }
        arch = config['target-arch']
        prefix = config['bfd-prefix']
        flags = _BASE_FLAGS.copy()
        flags.update(_ARCH_FLAGS.get(arch, {}))
        parts = ['./configure', '--prefix=%s' % prefix] + ['%s=%s' % i if i[1] else '%s' % i[0] for i in flags.iteritems()]
        command = ' '.join(parts)
        LOGGER.debug("BFD configure command: %s" % command)
        return command
