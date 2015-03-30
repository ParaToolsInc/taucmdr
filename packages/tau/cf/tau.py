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
import environment


LOGGER = logger.getLogger(__name__)

DEFAULT_SOURCE = 'http://tau.uoregon.edu/tau.tgz'

COMPILER_WRAPPERS = {'CC': 'tau_cc.sh',
                     'CXX': 'tau_cxx.sh',
                     'FC': 'tau_f90.sh',
                     'UPC': 'tau_upc.sh'}

COMMANDS = [
    'jumpshot',
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
    'trace2profile'
]

TAU_COMPILER_OPTIONS = {
    'verbose': {True: ['-optVerbose'], 
                False: ['-optQuiet']},
    'halt_on_error': {True: ['-optNoRevert'], 
                      False: ['-optRevert']},
    'compiler_inst': {'always': ['-optCompInst'], 
                      'never': ['-optNoCompInst'],
                      'fallback': ['-optRevert', '-optNoCompInst']},
}

TAU_ENVIRONMENT_OPTIONS = {
    'profile': {True: [('TAU_PROFILE', 1)], 
                False: [('TAU_PROFILE', 0)]},
    'trace': {True: [('TAU_TRACE', 1)],
              False: [('TAU_TRACE', 0)]},
    'sample': {True: [('TAU_SAMPLE', 1)],
               False: [('TAU_SAMPLE', 0)]},
    'callpath': {True: [('TAU_CALLPATH', 1), ('TAU_CALLPATH_DEPTH', None)],
                 False: [('TAU_CALLPATH', 0), ('TAU_CALLPATH_DEPTH', 0)]},
    'memory_usage': {True: [('TAU_TRACK_HEAP', 1)],
                     False: [('TAU_TRACK_HEAP', 0)]}
}


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



def verifyInstallation(prefix, arch, cc=None, cxx=None, fc=None):
  """
  Returns a path to a directory containing 'bin' and 'lib' directories for
  architecture `arch` if there is a working TAU installation at `prefix` or 
  raises a ConfigurationError describing why that installation is broken.
  """
  LOGGER.debug("Checking TAU installation at '%s' targeting arch '%s'" % (prefix, arch))
  
  if not os.path.exists(prefix):
    raise error.ConfigurationError("'%s' does not exist" % prefix)
  arch_path = os.path.join(prefix, arch)
  bin = os.path.join(arch_path, 'bin')
  lib = os.path.join(arch_path, 'lib')

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

  # Check for a makefile that matches requirements
  # TODO: Pick the right one
  # makefile = makefile

  taudb_prefix = os.path.join(os.path.expanduser('~'), '.ParaProf')
  LOGGER.debug("Checking tauDB installation at '%s'" % taudb_prefix)
  
  if not os.path.exists(taudb_prefix):
    raise error.ConfigurationError("'%s' does not exist" % taudb_prefix)

  path = os.path.join(taudb_prefix, 'perfdmf.cfg')
  if not os.path.exists(path):
    raise error.ConfigurationError("'%s' does not exist" % path)

  LOGGER.debug("tauDB installation at '%s' is valid" % taudb_prefix)
  LOGGER.debug("TAU installation at '%s' is valid" % prefix)
  
  return arch_path, makefile


def initialize(prefix, src, force_reinitialize=False, 
               arch=None, cc=None, cxx=None, fc=None):
  """
  TODO: Docs
  """
  tau_prefix = os.path.join(prefix, 'tau')
  if not arch:
    arch = detectDefaultHostArch()
  LOGGER.debug("Initializing TAU at '%s' from '%s' with arch=%s" % (tau_prefix, src, arch))
  
  # Check if the installation is already initialized
  if not force_reinitialize:
    try:
      return verifyInstallation(tau_prefix, arch=arch, 
                                cc=cc, cxx=cxx, fc=fc)
    except error.ConfigurationError, err:
      LOGGER.debug("Invalid installation: %s" % err)
  
  # Control build output
  with logger.logging_streams():

    # Download, unpack, or copy TAU source code
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
      
    # TAU's configure script has a goofy way of specifying the fortran compiler
    if fc:
      if fc['family'] != 'MPI':
         family_map = {'GNU': 'gfortran', 
                       'Intel': 'intel'}
         fc_family = fc['family']
         try:
           fortran_flag = '-fortran=%s' % family_map[fc_family]
         except KeyError:
           raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)
      else:
        # TODO:  Recognize family from MPI compiler
        raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)
    else:
      fortran_flag = ''
  
    # Initialize installation with a minimal configuration
    prefix_flag = '-prefix=%s' % tau_prefix
    arch_flag = '-arch=%s' % arch
    cc_flag = '-cc=%s' % cc['command'] if cc else ''
    cxx_flag = '-c++=%s' % cxx['command'] if cxx else ''
    cmd = ['./configure', prefix_flag, arch_flag, 
           cc_flag, cxx_flag, fortran_flag]
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
    environment.PATH.append(os.path.join(tau_prefix, arch, 'bin'))
    LOGGER.info('TAU configured successfully')
  
  # Verify the new installation and return
  return verifyInstallation(tau_prefix, arch=arch, 
                            cc=cc, cxx=cxx, fc=fc)


def getBuildEnvironment():
