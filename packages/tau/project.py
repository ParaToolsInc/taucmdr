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
import pickle

# TAU modules
from tau import getLogger, HELP_CONTACT, USER_PREFIX, SYSTEM_PREFIX, LOG_LEVEL, DEFAULT_TAU_COMPILER_OPTIONS
from util import detectDefaultTarget, pformatDict, pformatList, mkdirp
from error import ConfigurationError, InternalError, ProjectNameError, RegistryError
from registry import getRegistry

LOGGER = getLogger(__name__)


_PROJECT_DOCOPT = """
Architecture Options:
  --target-arch=<arch>         Set target architecture.             %(target-arch_default)s

Compiler Options:
  --cc=<compiler>              Set C compiler.                      %(cc_default)s
  --c++=<compiler>             Set C++ compiler.                    %(c++_default)s
  --fortran=<compiler>         Set Fortran compiler.                %(fortran_default)s

Assisting Library Options:
  --pdt=(download|<path>)      PDT installation path.               %(pdt_default)s
  --bfd=(download|<path>)      GNU Binutils installation path.      %(bfd_default)s
  --unwind=(download|<path>)   libunwind installation path.         %(unwind_default)s
  --papi=(download|<path>)     PAPI installation path.              %(papi_default)s
  --dyninst=(download|<path>)  DyninstAPI installation path.        %(dyninst_default)s

Thread Options:
  --openmp                     Enable OpenMP measurement.           %(openmp_default)s
  --pthreads                   Enable pthreads measurement.         %(pthreads_default)s

Message Passing Interface (MPI) Options:                            
  --mpi                        Enable MPI.                          %(mpi_default)s
  --mpi-include=<path>         MPI header files installation path.  %(mpi-include_default)s
  --mpi-lib=<path>             MPI library files installation path. %(mpi-lib_default)s

NVIDIA CUDA Options:
  --cuda                       Enable CUDA measurement.             %(cuda_default)s
  --cuda-sdk=<path>            CUDA SDK installation path.          %(cuda-sdk_default)s

Symmetric Hierarchical Memory (SHMEM) Options:
  --shmem=<compiler>           Enable SHMEM and set compiler.       %(shmem_default)s
  --shmem-runtime              Measure time in SHMEM runtime.       %(shmem-runtime_default)s

Universal Parallel C (UPC) Options:
  --upc=<compiler>             Enable UPC and set compiler command.
  --upc-gasnet=<path>          GASNET installation path.            %(upc-gasnet_default)s
  --upc-network=<network>      Set UPC network.                     %(upc-network_default)s

Memory Options:
  --memory                     Enable memory measurement.           %(memory_default)s
  --memory-debug               Enable memory debugging.             %(memory-debug_default)s

I/O and Communication Options:
  --io                         Enable I/O measurement.              %(io_default)s
  --comm-matrix                Enable communication matrix.         %(comm-matrix_default)s
  
Measurement Options:
  --profile                    Enable profiling.                    %(profile_default)s
  --trace                      Enable tracing.                      %(trace_default)s
  --sample                     Enable event-based sampling.         %(sample_default)s
  --callpath=<number>          Set the callpath measurement depth.  %(callpath_default)s
  
Hints:
  Use '--no-<option>' to disable <option>.
  Defaults can be changed via 'tau project default'.
"""



# True: the option is boolean and enabled
# False: the is of any kind and is disabled
# None: the option has no default 
_DEFAULTS = {'name': None,
             'target-arch': detectDefaultTarget(),
             'cc': 'gcc',
             'c++': 'g++',
             'fortran': 'gfortran',
             'pdt': 'download',
             'pdt_c++': 'g++',
             'bfd': 'download',
             'unwind': 'download',
             'papi': False,
             'dyninst': False,
             'openmp': False,
             'pthreads': False,
             'mpi': False,
             'mpi-include': False,
             'mpi-lib': False,
             'cuda': False,
             'cuda-sdk': False,
             'shmem': False,
             'shmem-runtime': False,
             'upc': False,
             'upc-gasnet': False,
             'upc-network': False,
             'memory': False,
             'memory-debug': False,
             'io': False,
             'comm-matrix': False,
             'callpath': '2',
             'profile': True,
             'trace': False,
             'sample': False}

def _getDefault(key):
    """
    Return default value
    """
    try:
        default = getRegistry().getDefaultValue(key)
    except KeyError:
        default = _DEFAULTS[key]
    return default


def getProjectOptions(show_defaults=True):
    """
    Returns a string of command line options formatted for docopt
    """
    defaults = {}
    for key, val in _DEFAULTS.iteritems():
        default = _getDefault(key)
        if default == False:
            default = 'disabled'
        elif default == True:
            default = 'enabled'
        defaults[key] = default
    keys = ['%s_default' % key for key in defaults.iterkeys()]
    if show_defaults:
        vals = ['[default: %s]' % val for val in defaults.itervalues()]
    else:
        vals = ['']*len(defaults)
    default_strs = dict(zip(keys, vals))
    try:
        return _PROJECT_DOCOPT % default_strs
    except KeyError, e:
        raise InternalError('%s: Check %s._DEFAULTS' % (str(e), __name__))


def getConfigFromOptions(args, apply_defaults=True, exclude=[]):
    """
    Check command line arguments and apply defaults
    """
    config = {}
    downloadable = ['pdt', 'bfd', 'unwind', 'papi', 'dyninst']
    for key_arg, val in args.iteritems():
        try:
            val = {'enabled': True, 'disabled': False}[val]
        except KeyError:
            pass
        if (key_arg.startswith('--') and not key_arg.startswith('--no-') and key_arg not in exclude):
            key = key_arg[2:]
            nokey_arg = '--no-%s' % key
            if args[nokey_arg]:
                overridden = '%s=%s' % (key_arg, val) if val else str(key_arg)
                LOGGER.info('NOTE: %s overrides %s' % (nokey_arg, overridden))
                config[key] = False
            elif val:
                config[key] = 'download' if (key in downloadable and val.lower() == 'download') else val
            elif apply_defaults:
                config[key] = _getDefault(key)
    try:
        config['callpath'] = int(config['callpath'])
    except ValueError:
        raise ConfigurationError('The argument to --callpath must be an integer')
    measurements = ['profile', 'trace', 'sample']
    if not any(map(lambda x: config[x], measurements)):
        raise ConfigurationError('At least one of [%s] is required.' \
                                 % ', '.join(map(lambda x: '--%s' % x, measurements)),
                                 "See 'tau project create --help.'")
    required = ['target-arch', 'cc', 'c++']
    for req in required:
        if not config[req]:
            raise ConfigurationError('--%s is required.' % req,
                                     "See 'tau project create --help'.")
    return config



class Project(object):
    """
    TODO: DOCS
    """
    def __init__(self, config, registry):
        from tau.pkgs.taupkg import TauPackage
        self.config = config
        self.registry = registry
        self.refresh = True
        self.target_prefix = '_'.join([config['target-arch']] + sorted(self.getCompilers().values()))
        self.prefix = os.path.join(self.registry.prefix, self.target_prefix)
        self.tau = TauPackage(self)

    def __str__(self):
        return pformatDict(self.config)
    
    def __len__(self):
        return len(self.config)

    def __iter__(self):
        for item in self.config.iteritems():
            yield item
              
    def __getitem__(self, key):
        return self.config[key]

    def getName(self):
        config = self.config
        callpath_depth = int(config['callpath'])
        config['callpath'] = callpath_depth
        if config['name']:
            return config['name']
        else:
            nameparts = ['bfd', 'comm-matrix', 
                         'cuda', 'dyninst', 'io', 'memory', 'memory-debug', 'mpi', 'openmp',
                         'papi', 'pdt', 'profile', 'pthreads', 'sample', 'trace']
            valueparts = ['c++', 'cc', 'fortran', 'target-arch', 'upc', 'upc-network']
            parts = [config[part].lower() for part in valueparts if config[part]]
            parts.extend([part.lower() for part in nameparts if config[part]])
            if callpath_depth:
                parts.append('callpath%d' % callpath_depth)
            parts.sort()
            name = '_'.join(parts)
            config['name'] = name
            return name

    def getCompilers(self):
        compiler_fields = ['cc', 'c++', 'fortran', 'upc']
        return dict((key, self.config[key]) for key in compiler_fields if self.config.get(key))
    
    def hasCompilers(self):
        compilers = self.getCompilers()
        return reduce(lambda a, b: a or b, compilers.values())

    def supportsCompiler(self, cmd):
        config = self.config
        if config['mpi']:
            if cmd[0:3] == 'mpi' or cmd in ['cc', 'c++', 'CC', 'cxx', 'f77', 'f90', 'ftn']:
                return True
        elif cmd[0:3] == 'mpi':
            return False
        if self.hasCompilers():
            return cmd in self.getCompilers().values()
        # Assume compiler is supported unless explicitly stated otherwise 
        return True
    
    def supportsExec(self, cmd):
        config = self.config
        if cmd in ['mpirun', 'mpiexec']:
            return bool(config['mpi'])
        return True

    def compile(self):
        if not self.refresh:
            LOGGER.debug('Project %r already compiled' % self.getName())
            return
        
        LOGGER.info('Compiling project %r. This will be done only once.' % self.getName())
 
        # Control build output
        devnull = None
        if LOG_LEVEL == 'DEBUG':
            stdout = sys.stdout
            stderr = sys.stderr
        else:
            devnull = open(os.devnull, 'w')
            stdout = devnull
            stderr = devnull
     
        self.tau.install(stdout, stderr)
            
        # Mark this configuration as built
        if devnull:
            devnull.close() 
        self.refresh = False
        getRegistry().save()

    def getEnvironment(self):
        """
        Returns an environment for use with subprocess.Popen that specifies 
        environment variables for this project
        """
        config = self.config
        env = dict(os.environ)
        bindir = os.path.join(self.tau.prefix, config['target-arch'], 'bin')
        try:
            env['PATH'] = bindir + ':' + env['PATH']
            LOGGER.debug('Updated PATH to %r' % env['PATH'])
        except KeyError:
            LOGGER.warning('The PATH environment variable was unset.')
            env['PATH'] = bindir
        return env

    def getTauMakefile(self):
        """
        Returns TAU_MAKEFILE for this configuration
        """
        config = self.config
        makefiles = os.path.join(self.tau.prefix, config['target-arch'], 'lib', 'Makefile.tau*')
        makefile = glob.glob(makefiles)[0]
        LOGGER.debug('TAU Makefile: %r' % makefile)
        return makefile
    
    def getTauTags(self):
        """
        Returns TAU tags for this project
        """
        makefile = self.getTauMakefile()
        start = makefile.find('Makefile.tau')
        mktags = makefile[start+12:].split('-')
        tags = []
        if not self.config['mpi']:
            tags += ['SERIAL']
        if len(mktags) > 1:
            tags.extend(map(lambda x: x.upper(), mktags[1:]))
        return tags
        
    def getTauCompilerEnvironment(self):
        """
        Returns an environment for use with subprocess.Popen that specifies the
        compile-time TAU environment variables for this project
        """
        env = self.getEnvironment()
        options = []
        if LOG_LEVEL == 'DEBUG':
            options.append('-optVerbose')
        else:
            options.append('-optQuiet')
        env['TAU_OPTIONS'] = ' '.join(DEFAULT_TAU_COMPILER_OPTIONS + options)
        env['TAU_MAKEFILE'] = self.getTauMakefile()
        return env

    def getTauCompilerFlags(self):
        """
        Returns compiler flags for the TAU compiler wrappers (tau_cc.sh, etc.)
        """
        # These are set in TAU_OPTIONS environment variable
        return []
    
    def getTauMakeEnvironment(self):
        """
        Returns an environment for use with subprocess.Popen that specifies the
        run-time TAU environment variables for this project
        """
        env = self.getTauCompilerEnvironment()
        compilers = {'CC': 'tau_cc.sh',
                     'CXX': 'tau_cxx.sh',
                     'F77': 'tau_f77.sh',
                     'F90': 'tau_f90.sh',
                     'UPC': 'tau_upc.sh',
                     'LD': 'tau_compiler.sh -optLinkOnly'}
        env.update(compilers)
        return env

    def getTauMakeFlags(self):
        """
        Returns make flags
        """
        compilers = {'CC': 'tau_cc.sh',
                     'CXX': 'tau_cxx.sh',
                     'F77': 'tau_f77.sh',
                     'F90': 'tau_f90.sh',
                     'UPC': 'tau_upc.sh',
                     'LD': 'tau_compiler.sh -optLinkOnly'}
        return ['%s=%s' % t for t in compilers.iteritems()]

    def getTauExecEnvironment(self):
        """
        Returns an environment for use with subprocess.Popen that specifies the
        run-time TAU environment variables for this project
        """
        config = self.config
        env = self.getEnvironment()
        parts = {'callpath': ['TAU_CALLPATH'],
                 'comm-matrix': ['TAU_COMM_MATRIX'],
                 'memory': ['TAU_TRACK_HEAP', 'TAU_TRACK_MEMORY_LEAKS'],
                 'memory-debug': ['TAU_MEMDBG_PROTECT_ABOVE', 'TAU_TRACK_MEMORY_LEAKS'],
                 'profile': ['TAU_PROFILE'],
                 'sample': ['TAU_SAMPLING'],
                 'trace': ['TAU_TRACE']}
        for key, val in config.iteritems():
            if key in parts and val:
                env.update([(x, '1') for x in parts[key]])
        if config['callpath']:
            env['TAU_CALLPATH_DEPTH'] = str(config['callpath'])
        return env

    def getTauExecFlags(self):
        """
        Returns tau_exec flags
        """
        config = self.config
        parts = {'memory': '-memory',
                 'memory-debug': '-memory_debug',
                 'io': '-io'}
        tags = self.getTauTags()
        flags = ['-T', ','.join(tags)]
        for key, val in config.iteritems():
            if key in parts and val:
                flags.append(parts[key])
        return flags
