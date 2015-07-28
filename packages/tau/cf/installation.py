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
import sys
import shutil
import multiprocessing
import logger, util
from cf import SoftwarePackageError
from error import ConfigurationError

LOGGER = logger.getLogger(__name__)


class Installation(object):
    """Encapsulates a software package installation.
    
    Attributes:
        name: Software package name.
        src: String absolute path to the source code.
        arch: String describing the target architecture.
        compilers: CompilerSet object
        src_prefix: Directory containing a subdirectory containing source code.
        install_prefix: Unique installation location depending on compilers.
        include_path: Convinence variable, install_prefix + '/include'
        bin_path: Convinence variable, install_prefix + '/bin'
        lib_path: Convinence variable, install_prefix + '/lib'
    """
    #pylint: disable=too-many-instance-attributes
    #pylint: disable=too-many-arguments

    def __init__(self, name, prefix, src, arch, compilers, sources):
        """Initializes the installation object.
        
        To set up a new installation, pass prefix=/path/to/directory and
        src={/path/to/source_archive_file, 'download'}.  `prefix` will be 
        created if it does not exist.  `src` may be a URL, file path, or the
        special keyword 'download'
        
        To set up an interface to an existing installation, pass
        src=/path/to/existing/installation and ignore prefix. Attributes
        `src` and `src_prefix` will be set to None.
        
        Args:
            name: Human readable name of the software package, e.g. 'TAU'
            prefix: Path to a directory to contain subdirectories for 
                    installation files, source file, and compilation files.
            src: Path to a directory where the software has already been 
                 installed, or a path to a source archive file, or the special
                 keyword 'download'
            arch: Target architecture (a.k.a TAU architecture)
            compilers: CompilerSet specifying which compilers to use
            sources: (arch, path) dictionary specifying where to get source
                     code archives for different architectures.  The None
                     key specifies the default (i.e. universal) source.    
        """ 
        self.name = name
        if os.path.isdir(src):
            self.install_prefix = src
            self.src_prefix = None
            self.src = None
        else:
            self.install_prefix = os.path.join(prefix, name, compilers.id)
            self.src_prefix = os.path.join(prefix, 'src')
            if src and src.lower() == 'download':
                self.src = sources.get(arch, sources[None])
            else:
                self.src = src
        self.arch = arch
        self.compilers = compilers
        self.include_path = os.path.join(self.install_prefix, 'include')
        self.bin_path = os.path.join(self.install_prefix, 'bin')
        self.lib_path = os.path.join(self.install_prefix, 'lib')
        
    def _parallel_make_flags(self):
        ncores = multiprocessing.cpu_count()
        return ['-j%s' % ncores]

    def _prepare_src(self):
        """Prepares source code for installation.
        
        Sets self._src_path to the path to the fresh, clean source code.
            
        Raises:
            ConfigurationError: The source code couldn't be copied or downloaded.
        """
        if not self.src: 
            raise SoftwarePackageError("No source code provided for %s" % self.name)
        elif os.path.isdir(self.src):
            LOGGER.debug("Copying source directory '%s' to '%s'" % (self.src, self.src_prefix))
            try:
                shutil.copytree(self.src, self.src_prefix, symlinks=True)
            except:
                raise ConfigurationError("Cannot copy source directory '%s'" % self.src,
                                         "Check that the directory is accessable")
            else:
                self._src_path = os.path.join(self.src_prefix, os.path.basename(self.src))
        else:
            dst = os.path.join(self.src_prefix, os.path.basename(self.src))
            try:
                util.download(self.src, dst)
            except IOError:
                raise ConfigurationError("Cannot acquire source archive '%s'" % self.src,
                                         "Check that the file or directory is accessable")
            try:
                self._src_path = util.extract(dst, self.src_prefix)
            except IOError:
                raise ConfigurationError("Cannot extract source archive '%s'" % self.src,
                                         "Check that the file or directory is accessable")
            finally:
                try: os.remove(dst)
                except: pass
 
    def verify(self, commands=[], libraries=[]):
        """Returns true if the installation is valid.
        
        A valid installation provides all expected libraries and commands.
        
        Args:
            commands: List of commands that should be present and executable.
            libraries: List of libraries that should be present and readable.
        
        Returns:
            True: If the installation at self.install_prefix is valid.
        
        Raises:
          SoftwarePackageError: Describs why the installation is invalid.
        """
        LOGGER.debug("Checking %s installation at '%s' targeting arch '%s'" % 
                     (self.name, self.install_prefix, self.arch))
        if not os.path.exists(self.install_prefix):
            raise SoftwarePackageError("'%s' does not exist" % self.install_prefix)
        for cmd in commands:
            path = os.path.join(self.bin_path, cmd)
            if not os.path.exists(path):
                raise SoftwarePackageError("'%s' is missing" % path)
            if not os.access(path, os.X_OK):
                raise SoftwarePackageError("'%s' exists but is not executable" % path)
        for lib in libraries:
            path = os.path.join(self.lib_path, lib)
            if not util.file_accessible(path):
                raise SoftwarePackageError("'%s' is not accessible" % path)
        LOGGER.debug("%s installation at '%s' is valid" % (self.name, self.install_prefix))
        return True
        
    def install(self):
        """Installs the software package.
        
        Raises:
            NotImplementedError: This method must be overridden by a subclass.
        """
        raise NotImplementedError
    
    def compiletime_config(self, opts=None, env=None):
        """Configure compilation environment to use this software package. 

        Returns command line options and environment variables required by this
        software package **when it is used to compile other software packages**.
        The default behavior, to be overridden by subclasses as needed, is to 
        prepend `self.bin_path` to the PATH environment variable.
        
        Args:
            opts: List of command line options.
            env: Dictionary of environment variables.
            
        Returns: 
            A tuple of opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        if os.path.isdir(self.bin_path):
            try:
                env['PATH'] = os.pathsep.join([self.bin_path, env['PATH']])
            except KeyError:
                env['PATH'] = self.bin_path
        return list(set(opts)), env

    def runtime_config(self, opts=None, env=None):
        """Configure runtime environment to use this software package.
        
        Returns command line options and environment variables required by this 
        software package **when other software packages depending on it execute**.
        The default behavior, to be overridden by subclasses as needed, is to 
        prepend `self.bin_path` to the PATH environment variable and 
        `self.lib_path` to the system library path (e.g. LD_LIBRARY_PATH).
        
        Args:
            opts: List of command line options.
            env: Dictionary of environment variables.
            
        Returns:
            A tuple of opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env) if env else dict(os.environ)
        if os.path.isdir(self.bin_path):
            try:
                env['PATH'] = os.pathsep.join([self.bin_path, env['PATH']])
            except KeyError:
                env['PATH'] = self.bin_path
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


class AutotoolsInstallation(Installation):
    """
    Superclass for Installations that follow GNU Autotools installation process.
    
    Follows a typical ./configure && make && make install proceedure.
    """
    #pylint: disable=too-many-arguments

    def __init__(self, name, prefix, src, arch, compilers, sources):
        super(AutotoolsInstallation,self).__init__(name, prefix, src, arch, 
                                                   compilers, sources)
        
    def configure(self, flags=[], env={}):
        """Invoke configure.
        
        Args:
            flags: List of command line flags to pass to 'configure'.
            env: Dictionary of environment variables to set before invoking 'configure'.
            
        Raises:
            SoftwarePackageError: Configuration failed.
        """
        LOGGER.debug("Configuring %s at '%s'" % (self.name, self._src_path))
        flags = list(flags)
        env = dict(env)

        # Prepare configuration flags
        flags += ['--prefix=%s' % self.install_prefix]
        compiler_env = {'GNU': {'CC': 'gcc', 'CXX': 'g++'},
                        'Intel': {'CC': 'icc', 'CXX': 'icpc'},
                        'PGI': {'CC': 'pgcc', 'CXX': 'pgCC'}}
        try:
            env.update(compiler_env[self.compilers.cc.family])
        except KeyError:
            LOGGER.info("Allowing %s to select compilers" % self.name)
        cmd = ['./configure'] + flags
        LOGGER.info("Configuring %s..." % self.name)
        if util.createSubprocess(cmd, cwd=self._src_path, env=env, stdout=False):
            raise SoftwarePackageError('%s configure failed' % self.name)   
    
    def make(self, flags=[], env={}, parallel=True):
        """Invoke make.
        
        Args:
            flags: List of command line flags to pass to 'make'.
            env: Dictionary of environment variables to set before invoking 'make'.
            
        Raises:
            SoftwarePackageError: Configuration failed.
        """
        LOGGER.debug("Making %s at '%s'" % (self.name, self._src_path))
        flags = list(flags)
        env = dict(env)
        if parallel:
            flags += self._parallel_make_flags()
        cmd = ['make'] + flags
        LOGGER.info("Compiling %s..." % self.name)
        if util.createSubprocess(cmd, cwd=self._src_path, env=env, stdout=False):
            raise SoftwarePackageError('%s compilation failed' % self.name)

    def make_install(self, flags=[], env={}, parallel=False):
        """Invoke 'make install'.
        
        Args:
            flags: List of command line flags to pass to 'make install'.
            env: Dictionary of environment variables to set before invoking 'make install'.
            
        Raises:
            SoftwarePackageError: Configuration failed.
        """
        LOGGER.debug("Installing %s at '%s' to '%s'" % 
                     (self.name, self._src_path, self.install_prefix))
        flags = list(flags)
        env = dict(env)
        if parallel:
            flags += self._parallel_make_flags()
        cmd = ['make', 'install'] + flags
        LOGGER.info("Installing %s..." % self.name)
        if util.createSubprocess(cmd, cwd=self._src_path, env=env, stdout=False):
            raise SoftwarePackageError('%s installation failed' % self.name)
        # Some systems use lib64 instead of lib
        if (os.path.isdir(self.lib_path+'64') and not os.path.isdir(self.lib_path)):
            os.symlink(self.lib_path+'64', self.lib_path)

    def install(self, force_reinstall=False):
        """Execute the typical GNU Autotools installation sequence.
        
        Args:
            force_reinstall: Set to True to force reinstallation.
            
        Returns:
            True if the installation succeeds and is successfully verified.
            
        Raises:
            SoftwarePackageError: Installation failed.
        """
        if not self.src:
            return self.verify()
        elif not force_reinstall:
            try:
                return self.verify()
            except Exception as err:
                LOGGER.debug(err)
        LOGGER.debug("Installing %s at '%s' from '%s' with arch=%s" %
                     (self.name, self.install_prefix, self.src, self.arch))

        self._prepare_src()

        # Perform Autotools installation sequence
        try:
            self.configure()
            self.make()
            self.make_install()
        except Exception as err:
            LOGGER.info("%s installation failed: %s " % (self.name, err))
            shutil.rmtree(self.install_prefix, ignore_errors=True)
        finally:
            LOGGER.debug("Deleting '%s'" % self._src_path)
            shutil.rmtree(self._src_path, ignore_errors=True)
            del self._src_path

        # Verify the new installation
        try:
            return self.verify()
        except Exception as err:
            shutil.rmtree(self.install_prefix, ignore_errors=True)
            raise SoftwarePackageError('%s installation failed verification: %s' % (err, self.name))
        else:
            LOGGER.info('%s installation complete', self.name)
