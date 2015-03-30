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


def _parseConfig(config, commandline_opts, environment_vars):
  """
  TODO: Docs
  """
  opts = set()
  envs = dict(os.environ)
  for key, val in config.iteritems():
    try:
      option = commandline_opts[key]
    except KeyError:
      pass
    else:
      try:
        opts |= set(option(val))
      except TypeError:
        try:
          opts |= set(option[val])
        except KeyError:
          raise error.InternalError('Invalid TAU configuration parameter: %s=%s' % (key, val))
    try:
      option = environment_vars[key]
    except KeyError:
      pass
    else:
      try:
        envs.update(option(val))
      except TypeError:
        try:
          envs.update(option[val])
        except KeyError:
          raise error.InternalError('Invalid TAU configuration parameter: %s=%s' % (key, val))
  return list(opts), envs



class Tau(object):
  """
  Encapsulates a TAU installation
  """
  def __init__(self, prefix, cc, cxx, fc, src, arch, **config):
    if src.lower() == 'download':
      src = DEFAULT_SOURCE
    if not arch:
      arch = _detectDefaultHostArch()
    self.prefix = prefix
    self.src = src
    self.arch = arch
    self.cc = cc
    self.cxx = cxx
    self.fc = fc
    compiler_prefix = '.'.join([str(c.eid) for c in cc, cxx, fc if c])
    self.src_prefix = os.path.join(prefix, 'src')
    self.tau_prefix = os.path.join(prefix, 'tau', compiler_prefix)
    self.include_path = os.path.join(self.tau_prefix, 'include')
    self.arch_path = os.path.join(self.tau_prefix, arch)
    self.bin_path = os.path.join(self.arch_path, 'bin')
    self.lib_path = os.path.join(self.arch_path, 'lib')
    self.taudb_prefix = os.path.join(os.path.expanduser('~'), '.ParaProf')
    self.config = config
    self.config['halt_build_on_error'] = False

  def verify(self):
    """
    Returns a path to a directory containing 'bin' and 'lib' directories for
    architecture `arch` if there is a working TAU installation at `prefix` or 
    raises a ConfigurationError describing why that installation is broken.
    """
    LOGGER.debug("Checking TAU installation at '%s' targeting arch '%s'" % (self.tau_prefix, self.arch))    
    if not os.path.exists(self.tau_prefix):
      raise error.ConfigurationError("'%s' does not exist" % self.tau_prefix)
  
    # Check for all commands
    for cmd in COMMANDS:
      path = os.path.join(self.bin_path, cmd)
      if not os.path.exists(path):
        raise error.ConfigurationError("'%s' is missing" % path)
      if not os.access(path, os.X_OK):
        raise error.ConfigurationError("'%s' exists but is not executable" % path)
    
    # Check that there is at least one makefile
    makefile = os.path.join(self.include_path, 'Makefile')
    if not os.path.exists(makefile):
      raise error.ConfigurationError("'%s' does not exist" % makefile)
    
    # Check for the minimal config 'vanilla' makefile
    makefile = os.path.join(self.lib_path, 'Makefile.tau')
    if not os.path.exists(makefile):
      LOGGER.warning("TAU installation at '%s' does not have a minimal Makefile.tau." % self.tau_prefix)
    
    # Check tauDB
    LOGGER.debug("Checking tauDB installation at '%s'" % self.taudb_prefix)
    if not os.path.exists(self.taudb_prefix):
      raise error.ConfigurationError("'%s' does not exist" % self.taudb_prefix)
    path = os.path.join(self.taudb_prefix, 'perfdmf.cfg')
    if not os.path.exists(path):
      raise error.ConfigurationError("'%s' does not exist" % path)
  
    LOGGER.debug("tauDB installation at '%s' is valid" % self.taudb_prefix)
    LOGGER.debug("TAU installation at '%s' is valid" % self.tau_prefix)
    return True

  def install(self, force_reinstall=False):
    """
    TODO: Docs
    """
    LOGGER.debug("Initializing TAU at '%s' from '%s' with arch=%s" % 
                 (self.tau_prefix, self.src, self.arch))
    
    # Check if the installation is already initialized
    if not force_reinstall:
      try:
        return self.verify()
      except error.ConfigurationError, err:
        LOGGER.debug(err)
    
    # Control build output
    LOGGER.info('Starting TAU installation')
    with logger.logging_streams():
      # Download, unpack, or copy TAU source code
      dst = os.path.join(self.src_prefix, os.path.basename(self.src))
      try:
        util.download(self.src, dst)
        srcdir = util.extract(dst, self.src_prefix)
      except IOError:
        raise error.ConfigurationError("Cannot acquire source file '%s'" % self.src,
                                       "Check that the file or directory is accessable")
      finally:
        try: os.remove(dst)
        except: pass

      # TAU's configure script has a goofy way of specifying the fortran compiler
      if self.fc:
        if self.fc['family'] != 'MPI':
           family_map = {'GNU': 'gfortran', 
                         'Intel': 'intel'}
           fc_family = self.fc['family']
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
      prefix_flag = '-prefix=%s' % self.tau_prefix
      arch_flag = '-arch=%s' % self.arch
      cc_flag = '-cc=%s' % self.cc['command'] if self.cc else ''
      cxx_flag = '-c++=%s' % self.cxx['command'] if self.cxx else ''
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
      taudb_configure = os.path.join(self.bin_path, 'taudb_configure')
      cmd = [taudb_configure, '--create-default']
      LOGGER.debug('Creating subprocess: %r' % cmd)
      LOGGER.info('Configuring tauDB...\n    %s' % ' '.join(cmd))
      proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
      if proc.wait():
        raise error.ConfigurationError('tauDB configure failed.')
    
    # Verify the new installation and return
    LOGGER.info('TAU installation complete')
    return self.verify()

  def getMakefile(self):
    """
    Returns an absolute path to a TAU_MAKEFILE
    """
    # TODO: Pick the right one
    makefile = 'Makefile.tau'
    return os.path.join(self.lib_path, makefile)

  def getCompiletimeConfig(self):
    """
    TODO: Docs
    """
    commandline_options = {
        'halt_build_on_error': {True: [], False: ['-optRevert']},
        'verbose': {True: ['-optVerbose'], False: ['-optQuiet']},
        'compiler_inst': {'always': ['-optCompInst'], 
                          'never': ['-optNoCompInst'],
                          'fallback': ['-optRevert', '-optNoCompInst']}
                           }
    environment_variables = {}
    opts, env = _parseConfig(self.config, commandline_options, environment_variables)
    env['PATH'] = os.pathsep.join([self.bin_path, env['PATH']])
    env['TAU_MAKEFILE'] = self.getMakefile()
    return opts, env

  def getRuntimeConfig(self):
    """
    TODO: Docs
    """
    commandline_options = {
        'verbose': {True: ['-v'], False: []},
        'sample': {True: ['-ebs'], False: []}
        }
    environment_variables = {
        'verbose': {True: {'TAU_VERBOSE': 1}, 
                    False: {'TAU_VERBOSE': 0}},
        'profile': {True: {'TAU_PROFILE': 1}, 
                    False: {'TAU_PROFILE': 0}},
        'trace': {True: {'TAU_TRACE': 1}, 
                  False: {'TAU_TRACE': 0}},
        'sample': {True: {'TAU_SAMPLE': 1}, 
                   False: {'TAU_SAMPLE': 0}},
        'callpath': lambda depth: ({'TAU_CALLPATH': 1, 'TAU_CALLPATH_DEPTH': depth} 
                                   if depth > 0 else {'TAU_CALLPATH': 0})
        }
    return _parseConfig(self.config, commandline_opts, environment_vars)


    