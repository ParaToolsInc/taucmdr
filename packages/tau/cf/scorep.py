#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
#This file is part of TAU Commander
#
#@section COPYRIGHT
#
#Copyright (c) 2015, ParaTools, Inc.
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice, 
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice, 
#     this list of conditions and the following disclaimer in the documentation 
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
#     be used to endorse or promote products derived from this software without 
#     specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#"""

# System modules
import os
import sys
import shutil
import platform
import subprocess

# TAU modules
import cf
import logger
import util
import error
import environment as env


LOGGER = logger.getLogger(__name__)

DEFAULT_SOURCE = 'http://tau.uoregon.edu/pdt.tgz'

def _detectDefaultHostOS():
  """
  Detect the default host operating system
  """
  return platform.system()
DEFAULT_HOST_OS = _detectDefaultHostOS()


def _detectDefaultHostArch():
    """
    Use PDT's archfind script to detect the host target architecture
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cmd = os.path.join(os.path.dirname(here), 'util', 'archfind', 'archfind')
    return subprocess.check_output(cmd).strip()
DEFAULT_HOST_ARCH = _detectDefaultHostArch()


#def _detectDefaultDeviceArch():
#  """
#  Detect coprocessors
#  """
#  return None
#DEFAULT_DEVICE_ARCH = _detectDefaultDeviceArch()

def _getFortranConfigureFlag(compiler):
  if compiler.family != 'MPI':
     family_map = {'GNU': 'gfortran',
                   'Intel': 'intel'}
     try:
       return family_map[compiler.family]
     except KeyError:
       raise InternalError("Unknown compiler family for Fortran: '%s'" % compiler.family)
  else:
    # TODO:  Recognize family from MPI compiler
    raise InternalError("Unknown compiler family for Fortran: '%s'" % compiler.family)

def verifyInstallation(prefix, arch, cc=None, cxx=None, fortran=None):
  """
  Returns True if there is a working PDT installation at 'prefix' or raisestau.
  a error.ConfigurationError describing why that installation is broken.
  """
  LOGGER.debug("Checking PDT installation at '%s' targeting arch '%s'" % (prefix, arch))
  
  if not os.path.exists(prefix):
    raise error.ConfigurationError("'%s' does not exist" % prefix)
  bin = os.path.join(prefix, arch, 'bin')
  lib = os.path.join(prefix, arch, 'lib')

  # Check for all commands
#  for cmd in COMMANDS:
#    path = os.path.join(bin, cmd)
#    if not os.path.exists(path):
#      raise error.ConfigurationError("'%s' is missing" % path)
#    if not os.access(path, os.X_OK):
#      raise error.ConfigurationError("'%s' exists but is not executable" % path)
#  
#  # Check that there is at least one makefile
#  makefile = os.path.join(prefix, 'include', 'Makefile')
#  if not os.path.exists(makefile):
#    raise error.ConfigurationError("'%s' does not exist" % makefile)
#  
#  # Check for the minimal config 'vanilla' makefile
#  makefile = os.path.join(lib, 'Makefile.tau')
#  if not os.path.exists(makefile):
#    LOGGER.warning("TAU installation at '%s' does not have a minimal Makefile.tau." % prefix)
#
#  taudb_prefix = os.path.join(os.path.expanduser('~'), '.ParaProf')
#  LOGGER.debug("Checking tauDB installation at '%s'" % taudb_prefix)
#  
#  if not os.path.exists(taudb_prefix):
#    raise error.ConfigurationError("'%s' does not exist" % taudb_prefix)
#
#  path = os.path.join(taudb_prefix, 'perfdmf.cfg')
#  if not os.path.exists(path):
#    raise error.ConfigurationError("'%s' does not exist" % path)
#
#  LOGGER.debug("tauDB installation at '%s' is valid" % taudb_prefix)
  LOGGER.debug("PDT installation at '%s' is valid" % prefix)
  return True


def initialize(prefix, src, force_reinitialize=False, 
               arch=None, 
               compiler_cmd=None):
  """
  TODO: Docs
  """
  pdt_prefix = os.path.join(prefix, 'pdt')
  if not arch:
    arch = detectDefaultHostArch()
  LOGGER.debug("Initializing pdt at '%s' from '%s' with arch=%s" % (pdt_prefix, src, arch))

  # Check compilers
  cc = None
  cxx = None
  fortran = None
  if compiler_cmd:
    family = cf.compiler.getFamily(compiler_cmd[0])
    for comp in family['CC']:
      if util.which(comp.command):
        cc = comp.command
        break
    if not cc:
      raise error.ConfigurationError("Cannot find C compiler command!")
    LOGGER.debug('Found CC=%s' % cc)
    for comp in family['CXX']:
      if util.which(comp.command):
        cxx = comp.command
        break
    if not cxx:
      raise error.ConfigurationError("Cannot find C++ compiler command!")
    LOGGER.debug('Found CXX=%s' % cxx)
    for comp in family['FC']:
      if util.which(comp.command):
        # pdt's configure script has a goofy way of specifying the fortran compiler
        fortran = _getFortranConfigureFlag(comp)
    LOGGER.debug('Found FC=%s' % fortran)
  
  # Check if the installation is already initialized
  try:
    verifyInstallation(pdt_prefix, arch=arch, cc=cc, cxx=cxx, fortran=fortran)
  except error.ConfigurationError, err:
    LOGGER.debug("Invalid installation: %s" % err)
    pass
  else:
    if not force_reinitialize:
      return
  
  # Control build output
  with logger.logging_streams():
    
    # Download, unpack, or copy pdt source code
    if src.lower() == 'download':
      src = DEFAULT_SOURCE
    src_prefix = os.path.join(prefix, 'src')
    dst = os.path.join(src_prefix, os.path.basename(src))
    try:
      util.download(src, dst)
      srcdir = util.extract(dst, src_prefix)
    except IOError:
      raise error.ConfigurationError("Cannot acquire source file '%s'" % src,
                               "Check that the file or directory is accessable")
    finally:
      try: os.remove(dst)
      except: pass
  
    # Initialize installation with a minimal configuration
    prefix_flag = '-prefix=%s' % pdt_prefix
    arch_flag = '-arch=%s' % arch if arch else ''
    cmd = ['./configure', prefix_flag, arch_flag]
    LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
    LOGGER.info('Configuring PDT...\n    %s' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, cwd=srcdir, stdout=sys.stdout, stderr=sys.stderr)
    if proc.wait():
      raise error.ConfigurationError('pdt configure failed')
  
    # Execute make
    cmd = ['make', '-j4', 'install']
    LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
    LOGGER.info('Compiling PDT...\n    %s' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, cwd=srcdir, stdout=sys.stdout, stderr=sys.stderr)
    if proc.wait():
        raise error.ConfigurationError('pdt compilation failed.')

    # Leave source, we'll probably need it again soon
    LOGGER.debug('Preserving %r for future use' % srcdir)
    
#    # Initialize tauDB with a minimal configuration
#    taudb_configure = os.path.join(tau_prefix, arch, 'bin', 'taudb_configure')
#    cmd = [taudb_configure, '--create-default']
#    LOGGER.debug('Creating subprocess: %r' % cmd)
#    LOGGER.info('Configuring tauDB...\n    %s' % ' '.join(cmd))
#    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
#    if proc.wait():
#      raise error.ConfigurationError('tauDB configure failed.')

    # Add pdt to PATH
    env.PATH.append(os.path.join(pdt_prefix, arch, 'bin'))
    LOGGER.info('pdt configured successfully')



## System modules
#import os
#import sys
#import subprocess
#import shutil
#
## TAU modules
#from tau import getLogger
#from util import download, extract
#from pkgs import Package
#from error import InternalError, PackageError, ConfigurationError
#from registry import getRegistry
#
#LOGGER = logger.getLogger(__name__)
#
#
#class PdtPackage(Package):
#    """
#    Program Database Toolkit package
#    """
#    
#    SOURCES = ['http://tau.uoregon.edu/pdt.tgz']
#
#    def __init__(self, project):
#        super(PdtPackage, self).__init__(project)
#        self.system_prefix = os.path.join(getRegistry().system.prefix, 
#                                          self.project.target_prefix, 'pdt')
#        self.user_prefix =  os.path.join(getRegistry().user.prefix, 
#                                         self.project.target_prefix, 'pdt')
#
#    def install(self, stdout=sys.stdout, stderr=sys.stderr):
#        config = self.project.config
#        pdt = config['pdt']
#        if not pdt:
#            raise InternalError('Tried to install pdt when (not config["pdt"])')
#
#        for loc in [self.system_prefix, self.user_prefix]:
#            if os.path.isdir(loc):
#                LOGGER.info("Using PDT installation found at %s" % loc)
#                self.prefix = loc
#                return
#        
#        # Try to install systemwide
#        if getRegistry().system.isWritable():
#            self.prefix = self.system_prefix
#        elif getRegistry().user.isWritable():
#            self.prefix = self.user_prefix
#        else:
#            raise ConfigurationError("User-level TAU installation at %r is not writable" % self.user_prefix,
#                                     "Check the file permissions and try again") 
#        LOGGER.info('Installing PDT at %r' % self.prefix)
#
#        if pdt.lower() == 'download':
#            src = self.SOURCES
#        elif os.path.isdir(pdt):
#            LOGGER.debug('Assuming user-supplied PDT at %r is properly installed' % pdt)
#            return
#        elif os.path.isfile(pdt):
#            src = ['file://'+pdt]
#            LOGGER.debug('Will build PDT from user-specified file %r' % pdt)
#        else:
#            raise PackageError('Invalid PDT directory %r' % pdt, 
#                               'Verify that the directory exists and that you have correct permissions to access it.')
#
#        # Configure the source code for this configuration
#        srcdir = self._getSource(src, stdout, stderr)
#        cmd = self._getConfigureCommand()
#        LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
#        LOGGER.info('Configuring PDT...\n%s' % ' '.join(cmd))
#        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
#        if proc.wait():
#            shutil.rmtree(self.prefix, ignore_errors=True)
#            raise PackageError('PDT configure failed.')
#    
#        # Execute make
#        cmd = ['make', '-j']
#        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
#        LOGGER.info('Compiling PDT...\n%s' % ' '.join(cmd))
#        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
#        if proc.wait():
#            shutil.rmtree(self.prefix, ignore_errors=True)
#            raise PackageError('PDT compilation failed.')
#    
#        # Execute make install
#        cmd = ['make', 'install']
#        LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
#        LOGGER.info('Installing PDT...\n%s' % ' '.join(cmd))
#        proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
#        if proc.wait():
#            shutil.rmtree(self.prefix, ignore_errors=True)
#            raise PackageError('PDT installation failed.')
#        
#        # Cleanup
#        LOGGER.debug('Recursively deleting %r' % srcdir)
#        shutil.rmtree(srcdir)
#        LOGGER.info('PDT installation complete.')
#        
#    def uninstall(self, stdout=sys.stdout, stderr=sys.stderr):
#        LOGGER.debug('Recursively deleting %r' % self.prefix)
#        shutil.rmtree(self.prefix)
#        LOGGER.info('PDT uninstalled.')
#
#    def _getConfigureCommand(self):
#        """
#        Returns the command that will configure PDT
#        """
#        # TODO: Support other compilers
#        return ['./configure', '-GNU', '-prefix=%s' % self.prefix]
#
#    def _getSource(self, sources, stdout, stderr):
#        """
#        Downloads or copies PDT source code
#        """
#        source_prefix = os.path.join(self.project.registry.prefix, 'src')
#        for src in sources:
#            dst = os.path.join(source_prefix, os.path.basename(src))
#            if src.startswith('http://') or src.startswith('ftp://'):
#                try:
#                    download(src, dst, stdout, stderr)
#                except:
#                    continue
#            elif src.startswith('file://'):
#                try:
#                    shutil.copy(src, dst)
#                except:
#                    continue
#            else:
#                raise InternalError("Don't know how to acquire source file %r" % src)
#            src_path = extract(dst, source_prefix)
#            os.remove(dst)
#            return src_path
#        raise PackageError('Failed to get source code')
#
