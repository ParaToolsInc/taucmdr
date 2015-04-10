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
import glob
import errno

# TAU modules
import logger
import util
import error
import environment


LOGGER = logger.getLogger(__name__)

DEFAULT_SOURCE = {None: 'http://tau.uoregon.edu/tau.tgz'}

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


def _parseConfig(config, commandline_opts, environment_vars):
  """
  TODO: Docs
  """
  opts = set()
  envs = dict()
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
  def __init__(self, prefix, cc, cxx, fc, src, arch, 
               pdt, bfd, libunwind, papi, **config):
    if not arch:
      arch = _detectDefaultHostArch()
    if src.lower() == 'download':
      try:
        src = DEFAULT_SOURCE[arch]
      except KeyError:
        src = DEFAULT_SOURCE[None]
    self.prefix = prefix
    self.cc = cc
    self.cxx = cxx
    self.fc = fc
    self.src = src
    self.arch = arch
    self.pdt = pdt
    self.bfd = bfd
    self.papi= papi
    self.libunwind = libunwind
    if os.path.isdir(src):
      self.tau_prefix = src
    else:
      compiler_prefix = '.'.join([str(c.eid) for c in cc, cxx, fc if c])
      self.tau_prefix = os.path.join(prefix, 'tau', compiler_prefix)
    self.src_prefix = os.path.join(prefix, 'src')
    self.include_path = os.path.join(self.tau_prefix, 'include')
    self.arch_path = os.path.join(self.tau_prefix, arch)
    self.bin_path = os.path.join(self.arch_path, 'bin')
    self.lib_path = os.path.join(self.arch_path, 'lib')
    self.config = config
    self.config['halt_build_on_error'] = False  # This feels hacky

  def getTags(self):
    """
    TODO: Docs
    """
    tags = []
    config = self.config
    
    family = self.cc['family']
    if family != 'GNU':
      compiler_tags = {'Intel': 'icpc', 'PGI': 'pgi'}
      try:
        tags.append(compiler_tags[family])
      except KeyError:
        raise error.InternalError("No makefile tag specified to compiler family '%s'" % family)
      
    if config['source_inst']:
      tags.append('pdt')
    if config['openmp_support']:
      openmp_tags = {'ignore': 'openmp',
                     'ompt': 'ompt',
                     'opari': 'opari'}
      tags.append(openmp_tags[config['openmp_measurements']])
    if config['pthreads_support']:
      tags.append('pthread')
    if config['mpi_support']:
      tags.append('mpi')
    if config['cuda_support']:
      tags.append('cuda')    
    if config['shmem_support']:
      tags.append('shmem')
    if config['mpc_support']:
      tags.append('mpc')

    if self.papi:
      tags.append('papi')
    
    LOGGER.debug("TAU tags: %s" % tags)
    return tags

  def verify(self):
    """
    Returns true if if there is a working TAU installation at `prefix` with a
    directory named `arch` containing `bin` and `lib` directories or 
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
    
    # Check for Makefile.tau matching this configuration
    makefile = self.getMakefile()
    if not makefile:
      raise error.ConfigurationError("TAU Makefile not found: %s" % makefile)
    
    # Open makefile, check BFDINCLUDE, UNWIND_INC, PAPIDIR
    LOGGER.debug("Tau Makefile %s :" %makefile)
    with open(makefile, 'r') as myMakeFile:
      data = myMakeFile.readlines()
    for line in data:
      if ('BFDINCLUDE=' in line):
        mfBfdInc=line.split('=')[1].strip().strip("-I")
        if (self.bfd.include_path != mfBfdInc):
           raise error.ConfigurationError("TAU Makefile does not have BFDINCLUDE = {} set to the \
                                          BFD_INCLUDE_PATH = {}".format(mfBfdInc,self.bfd.include_path))     
      if ('UNWIND_INC=' in line):
        mfUwInc=line.split('=')[1].strip().strip("-I")
        if (self.libunwind.include_path != mfUwInc):
           raise error.ConfigurationError("TAU Makefile does not have UNWIND_INC= {}set to the \
                                          LIBUNWIND_INCLUDE_PATH = {}".format(mfUwInc,self.libunwind.include_path))     
      if ('PAPIDIR=' in line):
        mfPapiDir = line.split('=')[1].strip()
        if (self.papi.papi_prefix != mfPapiDir):
           raise error.ConfigurationError("TAU Makefile {} does not have PAPIDIR = {} set to \
                                          the PAPI_PREFIX = {}".format(makefile,mfPapiDir,self.papi.papi_prefix))     
       
    
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
    LOGGER.info('Starting TAU installation')
    
    # Download, unpack, or copy TAU source code
    dst = os.path.join(self.src_prefix, os.path.basename(self.src))
    src = os.path.join(self.tau_prefix, 'src')
    LOGGER.debug("Checking for TAU source at '%s'" % src)
    if os.path.exists(src):
      LOGGER.debug("Found source at '%s'" % src)
      srcdir = src
    else:
      LOGGER.debug("Source not found, aquiring from '%s'" % self.src)
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
      
    # Check PDT
    if bool(self.config['source_inst']) != bool(self.pdt):
      raise error.InternalError("pdt=%s but config['source_inst']=%s" % (self.pdt, self.config['source_inst']))

    # Check BFD
    if (self.config['sample'] or self.config['compiler_inst'] != 'never') and (not self.bfd):
      LOGGER.warning("BFD is recommended when using sampling or compiler-based instrumentation")

    # Check libunwind
    if (bool(self.config['sample']) or bool(self.config['openmp_support'])) != bool(self.libunwind):
      LOGGER.warning("libunwind is recommended when using sampling or OpenMP")

    # Gather TAU configuration flags
    base_flags = ['-prefix=%s' % self.tau_prefix, 
                  '-arch=%s' % self.arch, 
                  '-cc=%s' % self.cc['command'] if self.cc else '', 
                  '-c++=%s' % self.cxx['command'] if self.cxx else '', 
                  fortran_flag,
                  '-pdt=%s' % self.pdt.pdt_prefix if self.pdt else '',
                  '-bfd=%s' % self.bfd.bfd_prefix if self.bfd else '',
                  '-papi=%s' % self.papi.papi_prefix if self.papi else '',
                  '-unwind=%s' % self.libunwind.libunwind_prefix if self.libunwind else '']
    if self.config['mpi_support']:
      mpi_flags = ['-mpi'
                   # TODO: -mpiinc, -mpilib, -mpilibrary
                   ]
    else:
      mpi_flags = []
    if self.config['openmp_support']:
      openmp_flags = ['-openmp']
      measurements = self.config['openmp_measurements'] 
      if measurements == 'ompt':
        if self.cc['family'] == 'Intel':
          openmp_flags.append('-ompt')
        else:
          raise error.ConfigurationError('OMPT for OpenMP measurement only works with Intel compilers')
      elif measurements == 'opari':
        openmp_flags.append('-opari')
    else:
      openmp_flags = []
    if self.config['pthreads_support']:
      pthreads_flags = ['-pthread']
    else:
      pthreads_flags = []

    # Execute configure
    cmd = ['./configure'] + base_flags + mpi_flags + openmp_flags + pthreads_flags
    LOGGER.info("Configuring TAU...")
    if util.createSubprocess(cmd, cwd=srcdir, stdout=False):
      raise error.ConfigurationError('TAU configure failed')
  
    # Execute make
    cmd = ['make', '-j4', 'install']
    LOGGER.info('Compiling TAU...')
    if util.createSubprocess(cmd, cwd=srcdir, stdout=False):
        raise error.ConfigurationError('TAU compilation failed.')

    # Leave source, we'll probably need it again soon
    # Create a link to the source for reuse
    LOGGER.debug('Preserving %r for future use' % srcdir)
    try:
      os.symlink(srcdir, src)
    except OSError as err:
      if not (err.errno == errno.EEXIST and os.path.islink(src)):
        LOGGER.warning("Can't create symlink '%s'. TAU source code won't be reused across configurations." % src)
      
    # Verify the new installation and return
    LOGGER.info('TAU installation complete')
    return self.verify()

  def getMakefile(self):
    """
    Returns an absolute path to a TAU_MAKEFILE
    """
    config_tags = set(self.getTags())
    if not len(config_tags):
      return 'Makefile.tau'
    tau_makefiles = glob.glob(os.path.join(self.lib_path, 'Makefile.tau*'))
    for makefile in tau_makefiles:
      tags = set(os.path.basename(makefile).split('.')[1].split('-')[1:])
      if tags <= config_tags and config_tags <= tags:
        return os.path.join(self.lib_path, makefile)
    LOGGER.debug("No TAU makefile matches tags '%s'. Available: %s" % (config_tags, tau_makefiles))
    return None

  def applyCompiletimeConfig(self, opts, env):
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
    tauOpts, tauEnv = _parseConfig(self.config, commandline_options, environment_variables)
    opts.extend(tauOpts)
    env.update(tauEnv)
    env['PATH'] = os.pathsep.join([self.bin_path, env.get('PATH')])
    env['TAU_MAKEFILE'] = self.getMakefile()

  def applyRuntimeConfig(self, opts, env):
    """
    TODO: Docs
    """
    commandline_options = {
        'verbose': {True: ['-v'], False: []},
        'sample': {True: ['-ebs'], False: []}
        }
    environment_variables = {
        'verbose': {True: {'TAU_VERBOSE': '1'}, 
                    False: {'TAU_VERBOSE': '0'}},
        'profile': {True: {'TAU_PROFILE': '1'}, 
                    False: {'TAU_PROFILE': '0'}},
        'trace': {True: {'TAU_TRACE': '1'}, 
                  False: {'TAU_TRACE': '0'}},
        'sample': {True: {'TAU_SAMPLING': '1'}, 
                   False: {'TAU_SAMPLING': '0'}},
        'callpath': lambda depth: ({'TAU_CALLPATH': '1', 'TAU_CALLPATH_DEPTH': str(depth)} 
                                   if depth > 0 else {'TAU_CALLPATH': '0'})
        }
    tauOpts, tauEnv = _parseConfig(self.config, commandline_options, environment_variables)
    opts.extend(tauOpts)
    env.update(tauEnv)

    env['PATH'] = os.pathsep.join([self.bin_path, env.get('PATH')])
    env['TAU_METRICS']=os.pathsep.join(self.config['metrics'])
  
  def showProfile(self, path):
    """
    Shows profile data in the specified file or folder
    """
    _, env = environment.base()
    env['PATH'] = os.pathsep.join([self.bin_path, env.get('PATH')])
    for viewer in 'paraprof', 'pprof':
      if os.path.isfile(path):
        cmd = [viewer, path]
      else:
        cmd = [viewer]
      LOGGER.info("Opening %s in %s" % (path, viewer))
      retval = util.createSubprocess(cmd, cwd=path, env=env, log=False)
      if retval != 0:
        LOGGER.warning("%s failed")
    if retval != 0:
      raise error.ConfigurationError("All viewers failed to open '%s'" % path,
                                     "Check that `java` is working, X11 is working,"
                                     " network connectivity, and file permissions")
