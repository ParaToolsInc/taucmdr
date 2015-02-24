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

DEFAULT_SOURCE = 'http://tau.uoregon.edu/tau.tgz'

COMPILER_WRAPPERS = {'CC': 'tau_cc.sh',
                     'CXX': 'tau_cxx.sh',
                     'F77': 'tau_f77.sh',
                     'F90': 'tau_f90.sh',
                     'UPC': 'tau_upc.sh'}

COMMANDS = ['jumpshot',
            'paraprof',
            'perfdmf_configure',
            'perfdmf_createapp',
            'perfdmf_createexp',
            'perfdmfdb.py',
            'perfdmf_loadtrial',
            'perfexplorer',
            'perfexplorer_configure',
            'phaseconvert',
            'pprof',
            'ppscript',
            'slog2print',
            'tau2slog2',
            'tau_analyze',
            'taucc',
            'tau_cc.sh',
            'tau_compiler.sh',
            'tau-config',
            'tau_convert',
            'taucxx',
            'tau_cxx.sh',
            'taudb_configure',
            'taudb_install_cert',
            'taudb_keygen',
            'taudb_loadtrial',
            'tau_ebs2otf.pl',
            'tau_ebs_process.pl',
            'tauex',
            'tau_exec',
            'tau_f77.sh',
            'tauf90',
            'tau_f90.sh',
            'tau_gen_wrapper',
            'tau_header_replace.pl',
            'tauinc.pl',
            'tau_java',
            'tau_javamax.sh',
            'tau_macro.sh',
            'tau_merge',
            'tau_multimerge',
            'tau_pebil_rewrite',
            'tau_reduce',
            'tau_resolve_addresses.py',
            'tau_rewrite',
            'tau_selectfile',
            'tau_show_libs',
            'tau_throttle.sh',
            'tau_treemerge.pl',
            'tauupc',
            'tau_upc.sh',
            'tau_user_setup.sh',
            'trace2profile']


def _detectDefaultHostOS():
  """
  Detect the default host operating system
  """
  return platform.system()
DEFAULT_HOST_OS = _detectDefaultHostOS()


def _detectDefaultHostArch():
    """
    Use TAU's archfind script to detect the host target architecture
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cmd = os.path.join(os.path.dirname(here), 'util', 'archfind', 'archfind')
    return subprocess.check_output(cmd).strip()
DEFAULT_HOST_ARCH = _detectDefaultHostArch()


def _detectDefaultDeviceArch():
  """
  Detect coprocessors
  """
  return None
DEFAULT_DEVICE_ARCH = _detectDefaultDeviceArch()
 

def verifyInstallation(prefix, arch):
  """
  Returns True if there is a working TAU installation at 'prefix' or raisestau.
  a error.ConfigurationError describing why that installation is broken.
  """
  LOGGER.debug("Checking TAU installation at '%s' targeting arch '%s'" % (prefix, arch))
  
  if not os.path.exists(prefix):
    raise error.ConfigurationError("'%s' does not exist" % prefix)
  bin = os.path.join(prefix, arch, 'bin')
  lib = os.path.join(prefix, arch, 'lib')

  # Check for all commands
  for cmd in COMMANDS:
    path = os.path.join(bin, cmd)
    if not os.path.exists(path):
      raise error.ConfigurationError("'%s' is missing" % path)
    if not os.access(path, os.X_OK):
      raise error.ConfigurationError("'%s' exists but is not executable" % path)
  
  # Check that there is at least one makefile
  makefile = os.path.join(prefix, 'include', 'Makefile')
  if not os.path.exists(makefile):
    raise error.ConfigurationError("'%s' does not exist" % makefile)
  
  # Check for the minimal config 'vanilla' makefile
  makefile = os.path.join(lib, 'Makefile.tau')
  if not os.path.exists(makefile):
    LOGGER.warning("TAU installation at '%s' does not have a minimal Makefile.tau." % prefix)

  taudb_prefix = os.path.join(os.path.expanduser('~'), '.ParaProf')
  LOGGER.debug("Checking tauDB installation at '%s'" % taudb_prefix)
  
  if not os.path.exists(taudb_prefix):
    raise error.ConfigurationError("'%s' does not exist" % taudb_prefix)

  path = os.path.join(taudb_prefix, 'perfdmf.cfg')
  if not os.path.exists(path):
    raise error.ConfigurationError("'%s' does not exist" % path)

  LOGGER.debug("tauDB installation at '%s' is valid" % taudb_prefix)
  LOGGER.debug("TAU installation at '%s' is valid" % prefix)
  return True


def initialize(prefix, src, force_reinitialize=False, 
               arch=None, compiler_cmd=None):
  """
  TODO: Docs
  """
  tau_prefix = os.path.join(prefix, 'tau')
  if not arch:
    arch = detectDefaultHostArch()
  LOGGER.debug("Initializing TAU at '%s' from '%s' with arch=%s" % (tau_prefix, src, arch))
  
  # Check compilers
  if compiler_cmd:
    family = cf.compiler.getFamily(compiler_cmd[0])
      
      
  

  # Check if the installation is already initialized
  try:
    verifyInstallation(tau_prefix, arch=arch)
  except error.ConfigurationError, err:
    LOGGER.debug("Invalid installation: %s" % err)
    pass
  else:
    if not force_reinitialize:
      return
  
  # Control build output
  with logger.logging_streams():
    
    # Download, unpack, or copy TAU source code
    src_prefix = os.path.join(prefix, 'src')
    dst = os.path.join(src_prefix, os.path.basename(src))
    try:
      util.download(src, dst)
      srcdir = util.extract(dst, src_prefix)
    except IOError:
      raise error.ConfigurationError("Cannot acquire source file '%s'" % src,
                               "Check that the file or directory is accessable")
    finally:
      try:
        os.remove(dst)
      except:
        pass
  
    # Initialize installation with a minimal configuration
    prefix_flag = '-prefix=%s' % tau_prefix
    arch_flag = '-arch=%s' % arch if arch else ''
    cmd = ['./configure', prefix_flag, arch_flag]
    LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
    LOGGER.info('Configuring TAU...\n    %s' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, cwd=srcdir, stdout=sys.stdout, stderr=sys.stderr)
    if proc.wait():
      raise error.ConfigurationError('TAU configure failed')
  
    # Execute make
    cmd = ['make', '-j4', 'install']
    LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
    LOGGER.info('Compiling TAU...\n    %s' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, cwd=srcdir, stdout=sys.stdout, stderr=sys.stderr)
    if proc.wait():
        raise error.ConfigurationError('TAU compilation failed.')

    # Leave source, we'll probably need it again soon
    LOGGER.debug('Preserving %r for future use' % srcdir)
    
    # Initialize tauDB with a minimal configuration
    taudb_configure = os.path.join(tau_prefix, arch, 'bin', 'taudb_configure')
    cmd = [taudb_configure, '--create-default']
    LOGGER.debug('Creating subprocess: %r' % cmd)
    LOGGER.info('Configuring tauDB...\n    %s' % ' '.join(cmd))
    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if proc.wait():
      raise error.ConfigurationError('tauDB configure failed.')

    # Add TAU to PATH
    env.PATH.append(os.path.join(tau_prefix, arch, 'bin'))
    LOGGER.info('TAU configured successfully')

  

# class TauPackage(Package):
#     """
#     TAU package
#     """
#     
#     SOURCES = ['http://tau.uoregon.edu/tau.tgz']
#     
#     def __init__(self, project):
#         super(TauPackage, self).__init__(project)
#         keys = ['bfd', 'cuda', 'dyninst', 'mpi', 'openmp', 'papi', 'pdt', 'pthreads']
#         name = '_'.join(sorted([k.lower() for k in keys if self.project.config.get(k)]))
#         self.system_prefix = os.path.join(getRegistry().system.prefix, 
#                                   self.project.target_prefix, 'tau')
#         self.user_prefix =  os.path.join(getRegistry().user.prefix, 
#                                          self.project.target_prefix, 'tau')
#         self.bfd = BfdPackage(self.project)
#         self.pdt = PdtPackage(self.project)
#         self.unwind = None # FIXME: UnwindPackage
#         self.papi = None
#         self.dyninst = None
#         self.cuda = None
# 
#     def install(self, stdout=sys.stdout, stderr=sys.stderr):
#         config = self.project.config
#         tau_opt = config['tau']
# 
#         # Install dependencies
#         if self.bfd:
#             self.bfd.install(stdout, stderr)
#         if self.pdt:
#             self.pdt.install(stdout, stderr)
#         
#         for loc in [self.system_prefix, self.user_prefix]:
#             if os.path.isdir(loc):
#                 LOGGER.info("Using TAU installation found at %s" % loc)
#                 self.prefix = loc
#                 return
# 
#         # Try to install systemwide
#         if getRegistry().system.isWritable():
#             self.prefix = self.system_prefix
#         elif getRegistry().user.isWritable():
#             self.prefix = self.user_prefix
#         else:
#             raise error.ConfigurationError("User-level TAU installation at %r is not writable" % self.user_prefix,
#                                      "Check the file permissions and try again") 
#         LOGGER.info('Installing TAU at %r' % self.prefix)
# 
#         if tau_opt.lower() == 'download':
#             src = self.SOURCES
#         elif os.path.isdir(tau_opt):
#             LOGGER.debug('Assuming user-supplied TAU at %r is properly installed' % tau_opt)
#             return
#         elif os.path.isfile(tau_opt):
#             src = ['file://'+tau_opt]
#             LOGGER.debug('Will build TAU from user-specified file %r' % tau_opt)
#         else:
#             raise PackageError('Invalid TAU directory %r' % tau_opt, 
#                                'Verify that the directory exists and that you have correct permissions to access it.')
# 
#         # Configure the source code for this configuration
#         srcdir = self._getSource(src, stdout, stderr)
#         cmd = self._getConfigureCommand()
#         LOGGER.debug('Creating configure subprocess in %r: %r' % (srcdir, cmd))
#         LOGGER.info('Configuring TAU...\n%s' % ' '.join(cmd))
#         proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
#         if proc.wait():
#             shutil.rmtree(self.prefix, ignore_errors=True)
#             raise PackageError('TAU configure failed.')
#         
#         # Execute make
#         cmd = ['make', '-j', 'install']
#         LOGGER.debug('Creating make subprocess in %r: %r' % (srcdir, cmd))
#         LOGGER.info('Compiling TAU...\n%s' % ' '.join(cmd))
#         proc = subprocess.Popen(cmd, cwd=srcdir, stdout=stdout, stderr=stderr)
#         if proc.wait():
#             shutil.rmtree(self.prefix, ignore_errors=True)
#             raise PackageError('TAU compilation failed.')
#         
#         # Leave source, we'll probably need it again soon
#         LOGGER.debug('Preserving %r for future use' % srcdir)
#         LOGGER.info('TAU installation complete.')
#         
#     def uninstall(self, stdout=sys.stdout, stderr=sys.stderr):
#         LOGGER.debug('Recursively deleting %r' % self.prefix)
#         shutil.rmtree(self.prefix)
#         LOGGER.info('TAU uninstalled.')
# 
#     def _getSource(self, sources, stdout, stderr):
#         """
#         Downloads or copies TAU source code
#         """
#         source_prefix = os.path.join(self.project.registry.prefix, 'src')
#         for src in sources:
#             dst = os.path.join(source_prefix, os.path.basename(src))
#             if src.startswith('http://') or src.startswith('ftp://'):
#                 try:
#                     util.download(src, dst, stdout, stderr)
#                 except:
#                     continue
#             elif src.startswith('file://'):
#                 try:
#                     shutil.copy(src, dst)
#                 except:
#                     continue
#             else:
#                 raise InternalError("Don't know how to acquire source file %r" % src)
#             src_path = util.extract(dst, source_prefix)
#             os.remove(dst)
#             return src_path
#         raise PackageError('Failed to get source code')
# 
#     def _translateConfigureArg(self, key, val):
#         """
#         Gets the configure script argument(s) corresponding to a Tau Commander argument
#         """
# 
#     def _getConfigureCommand(self):
#         """
#         Returns the command that will configure TAU for this project
#         """
#         config = self.project.config
#         pdt_prefix = self.pdt.prefix if config['pdt'] == 'download' else config['pdt']
#         bfd_prefix = self.bfd.prefix if config['bfd'] == 'download' else config['bfd']
#         
#         # Excluded (e.g. runtime) flags
#         excluded = ['name', 'cuda', 'profile', 'trace', 'sample', 'callpath', 
#                     'memory', 'memory-debug', 'comm-matrix']
#         # No parameter flags
#         noparam = {'mpi': '-mpi',
#                    'openmp': '-opari',
#                    'pthreads': '-pthread',
#                    'io': '-iowrapper',
#                    'pdt': '-pdt=%s' % pdt_prefix,
#                    'bfd': '-bfd=%s' % bfd_prefix,
#                    'unwind': '-unwind=%s' % config['unwind'],
#                    'cuda-sdk': '-cuda=%s' % 'FIXME'}
#         # One parameter flags
#         oneparam = {'dyninst': '-dyninst=%s',
#                     'mpi-include': '-mpiinc=%s',
#                     'mpi-lib': '-mpilib=%s',
#                     'papi': '-papi=%s',
#                     'target-arch': '-arch=%s',
#                     'upc': '-upc=%s',
#                     'upc-gasnet': '-gasnet=%s',
#                     'upc-network': '-upcnetwork=%s',
#                     #TODO: Translate compiler command correctly
#                     'cc': '-cc=%s',
#                     'c++': '-c++=%s',
#                     'fortran': '-fortran=%s',
#                     'pdt_c++': '-pdt_c++=%s'}
# 
#         cmd = ['./configure', '-prefix=%s' % self.prefix]
#         for key, val in config.iteritems():
#             if val and key not in excluded:
#                 try:
#                     arg = [noparam[key]]
#                 except KeyError:
#                     try:
#                         arg = [oneparam[key] % val]
#                     except KeyError:
#                         raise PackageError("Couldn't find an appropriate configure argument for %r" % key)
#                 cmd.extend(arg)
#         return cmd
        
