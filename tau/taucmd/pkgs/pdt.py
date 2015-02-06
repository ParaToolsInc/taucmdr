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
from taucmd.error import InternalError, PackageError, ConfigurationError


LOGGER = taucmd.getLogger(__name__)


class PdtPackage(Package):
    """
    Program Database Toolkit package
    """
    
    SOURCES = ['http://tau.uoregon.edu/pdt.tgz']

    def __init__(self, project):
        super(PdtPackage, self).__init__(project)
        self.system_prefix = os.path.join(taucmd.registry.REGISTRY.system.prefix, 
                                          self.project.target_prefix, 'pdt')
        self.user_prefix =  os.path.join(taucmd.registry.REGISTRY.user.prefix, 
                                         self.project.target_prefix, 'pdt')

    def install(self, stdout=sys.stdout, stderr=sys.stderr):
        config = self.project.config
        pdt = config['pdt']
        if not pdt:
            raise InternalError('Tried to install pdt when (not config["pdt"])')

        for loc in [self.system_prefix, self.user_prefix]:
            if os.path.isdir(loc):
                LOGGER.info("Using PDT installation found at %s" % loc)
                self.prefix = loc
                return
        
        # Try to install systemwide
        if taucmd.registry.REGISTRY.system.isWritable():
            self.prefix = self.system_prefix
        elif taucmd.registry.REGISTRY.user.isWritable():
            self.prefix = self.user_prefix
        else:
            raise ConfigurationError("User-level TAU installation at %r is not writable" % self.user_prefix,
                                     "Check the file permissions and try again") 
        LOGGER.info('Installing PDT at %r' % self.prefix)

        if pdt.lower() == 'download':
            src = self.SOURCES
        elif os.path.isdir(pdt):
            LOGGER.debug('Assuming user-supplied PDT at %r is properly installed' % pdt)
            return
        elif os.path.isfile(pdt):
            src = [pdt]
            LOGGER.debug('Will build PDT from user-specified file %r' % pdt)
        else:
            raise PackageError('Invalid PDT directory %r' % pdt, 
                               'Verify that the directory exists and that you have correct permissions to access it.')

        # Configure the source code for this configuration
        srcdir = self._getSource(src, stdout, stderr)
        cmd = self._getConfigureCommand()
        LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Configuring PDT...\n%s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('PDT configure failed.')
    
        # Execute make
        cmd = ['make', '-j']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Compiling PDT...\n%s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('PDT compilation failed.')
    
        # Execute make install
        cmd = ['make', 'install']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Installing PDT...\n%s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('PDT installation failed.')
        
        # Cleanup
        LOGGER.debug('Recursively deleting %r' % srcdir)
        shutil.rmtree(srcdir)
        LOGGER.info('PDT installation complete.')
        
    def uninstall(self, stdout=sys.stdout, stderr=sys.stderr):
        LOGGER.debug('Recursively deleting %r' % self.prefix)
        shutil.rmtree(self.prefix)
        LOGGER.info('PDT uninstalled.')

    def _getConfigureCommand(self):
        """
        Returns the command that will configure PDT
        """
        # TODO: Support other compilers
        return ['./configure', '-GNU', '-prefix=%s' % self.prefix]

    def _getSource(self, sources, stdout, stderr):
        """
        Downloads or copies BFD source code
        """
        source_prefix = os.path.join(self.project.registry.prefix, 'src')
        for src in sources:
            dst = os.path.join(source_prefix, os.path.basename(src))
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
            src_path = util.extract(dst, source_prefix)
            os.remove(dst)
            return src_path
        raise PackageError('Failed to get source code')

