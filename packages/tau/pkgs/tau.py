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
import shutil
import fnmatch
import subprocess
import tau
from tau import TAU_MASTER_SRC_DIR
from tau.pkgs import Package
from tau.pkgs.bfd import BfdPackage
from tau.pkgs.pdt import PdtPackage
from tau.error import PackageError

LOGGER = tau.getLogger(__name__)


class TauPackage(Package):
    """
    TAU package
    """
    
    def __init__(self, project):
        super(TauPackage, self).__init__(project)
        keys = ['bfd', 'cuda', 'dyninst', 'mpi', 'openmp', 'papi', 'pdt', 'pthreads']
        name = '_'.join(sorted([k.lower() for k in keys if self.project.config.get(k)]))
        self.prefix = os.path.join(self.project.prefix, 'tau', name)
        self.bfd = BfdPackage(self.project)
        self.pdt = PdtPackage(self.project)
        self.unwind = None # FIXME: UnwindPackage
        self.papi = None
        self.dyninst = None
        self.cuda = None       

    def install(self, stdout=sys.stdout, stderr=sys.stderr):
        # Install dependencies
        if self.bfd:
            self.bfd.install(stdout, stderr)
        if self.pdt:
            self.pdt.install(stdout, stderr)
        
        if os.path.isdir(self.prefix):
            LOGGER.debug("TAU already installed at %r" % self.prefix)
            return
        LOGGER.info('Installing TAU at %r' % self.prefix)

        # Configure the source code for this project
        srcdir = self._getSource(TAU_MASTER_SRC_DIR)
        cmd = self._getConfigureCommand()
        LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Configuring TAU...\n%s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('TAU configure failed.')
        
        # Execute make
        cmd = ['make', '-j', 'install']
        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
        LOGGER.info('Compiling TAU...\n%s' % ' '.join(cmd))
        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
        if proc.wait():
            shutil.rmtree(self.prefix, ignore_errors=True)
            raise PackageError('TAU compilation failed.')
        
        # Leave source, we'll probably need it again soon
        LOGGER.debug('Preserving %r for future use' % srcdir)
        LOGGER.info('TAU installation complete.')
        
    def uninstall(self, stdout=sys.stdout, stderr=sys.stderr):
        LOGGER.debug('Recursively deleting %r' % self.prefix)
        shutil.rmtree(self.prefix)
        LOGGER.info('TAU uninstalled.')

    def _getSource(self, source):
        """
        Makes a fresh clone of the TAU source code
        """
        source_prefix = os.path.join(self.project.registry.prefix, 'src')
        dest = os.path.join(source_prefix, 'tau')
        # Don't copy if the source already exists
        if os.path.exists(dest) and os.path.isdir(dest):
            LOGGER.debug('TAU source code directory %r already exists.' % dest)
        else:
            def ignore(path, names):
                globs = ['*.o', '*.a', '*.so', '*.dylib', '*.pyc', 'a.out', 
                         '.all_configs', '.last_config', '.project', '.cproject',
                         '.git', '.gitignore', '.ptp-sync', '.pydevproject']
                # Ignore bindirs in the top level directory
                if path == source:
                    bindirs = ['x86_64', 'bgl', 'bgp', 'bgq', 'craycnl', 'apple']
                    globs.extend(bindirs)
                # Build set of ignored files
                ignored_names = []
                for pattern in globs:
                    ignored_names.extend(fnmatch.filter(names, pattern))
                return set(ignored_names)
            LOGGER.debug('Copying from %r to %r' % (source, dest))
            LOGGER.info('Creating new copy of TAU at %r.  This will only be done once.' % dest)
            shutil.copytree(source, dest, ignore=ignore)
        return dest

    def _translateConfigureArg(self, key, val):
        """
        Gets the configure script argument(s) corresponding to a Tau Commander argument
        """

    def _getConfigureCommand(self):
        """
        Returns the command that will configure TAU for this project
        """
        config = self.project.config
        pdt_prefix = self.pdt.prefix if config['pdt'] == 'download' else config['pdt']
        bfd_prefix = self.bfd.prefix if config['bfd'] == 'download' else config['bfd']
        
        # Excluded (e.g. runtime) flags
        excluded = ['name', 'cuda', 'profile', 'trace', 'sample', 'callpath', 
                    'memory', 'memory-debug', 'comm-matrix']
        # No parameter flags
        noparam = {'mpi': '-mpi',
                   'openmp': '-opari',
                   'pthreads': '-pthread',
                   'io': '-iowrapper',
                   'pdt': '-pdt=%s' % pdt_prefix,
                   'bfd': '-bfd=%s' % bfd_prefix,
                   'unwind': '-unwind=%s' % config['unwind'],
                   'cuda-sdk': '-cuda=%s' % 'FIXME'}
        # One parameter flags
        oneparam = {'dyninst': '-dyninst=%s',
                    'mpi-include': '-mpiinc=%s',
                    'mpi-lib': '-mpilib=%s',
                    'papi': '-papi=%s',
                    'target-arch': '-arch=%s',
                    'upc': '-upc=%s',
                    'upc-gasnet': '-gasnet=%s',
                    'upc-network': '-upcnetwork=%s',
                    #TODO: Translate compiler command correctly
                    'cc': '-cc=%s',
                    'c++': '-c++=%s',
                    'fortran': '-fortran=%s',
                    'pdt_c++': '-pdt_c++=%s'}

        cmd = ['./configure', '-prefix=%s' % self.prefix]
        for key, val in config.iteritems():
            if val and key not in excluded:
                try:
                    arg = [noparam[key]]
                except KeyError:
                    try:
                        arg = [oneparam[key] % val]
                    except KeyError:
                        raise PackageError("Couldn't find an appropriate configure argument for %r" % key)
                cmd.extend(arg)
        return cmd
        
