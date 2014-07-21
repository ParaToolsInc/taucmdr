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
import glob
import taucmd
import pickle
import pprint
import subprocess
from textwrap import dedent
from datetime import datetime
from taucmd import TauError
from taucmd.installers import pdt, bfd, tau
from taucmd import util


LOGGER = taucmd.getLogger(__name__)

PROJECT_OPTIONS = """
Architecture Options:
  --target-arch=<arch>         Set target architecture.             [default: %(target-arch_default)s]

Compiler Options:
  --cc=<compiler>              Set C compiler.                      [default: %(cc_default)s]
  --c++=<compiler>             Set C++ compiler.                    [default: %(cxx_default)s]
  --fortran=<compiler>         Set Fortran compiler.                [default: %(fc_default)s]
  --upc=<compiler>             Set UPC compiler.                    [default: %(upc_default)s]

Assisting Library Options:
  --pdt=(download|<path>)      PDT installation path.               [default: %(pdt_default)s]
  --no-pdt                     Disable PDT source instrumentation.
  --bfd=(download|<path>)      GNU Binutils installation path.      [default: %(bfd_default)s]
  --no-bfd                     Disable source location resolution.
  --unwind=(download|<path>)   libunwind installation path.         [default: %(unwind_default)s]
  --no-unwind                  Disable callstack unwinding.
  --papi=(download|<path>)     PAPI installation path.              [default: %(papi_default)s]
  --no-papi                    Disable hardware metrics.
  --dyninst=(download|<path>)  DyninstAPI installation path.        [default: %(dyninst_default)s]
  --no-dyninst                 Disable binary instrumentation.

Thread Options:
  --openmp                     Enable OpenMP measurement.           [default: %(openmp_default)s]
  --no-openmp                  Disable OpenMP measurement.          
  --pthreads                   Enable pthreads measurement.         [default: %(pthreads_default)s]
  --no-pthreads                Disable pthreads measurement.        

Message Passing Interface (MPI) Options:                            
  --mpi                        Enable MPI measurement.              [default: %(mpi_default)s]
  --no-mpi                     Disable MPI measurement.
  --mpi-include=<path>         MPI header files installation path.  [default: %(mpi-include_default)s]
  --mpi-lib=<path>             MPI library files installation path. [default: %(mpi-lib_default)s]

NVIDIA CUDA Options:
  --cuda                       Enable CUDA measurement.             [default: %(cuda_default)s]
  --no-cuda                    Disable CUDA measurement.
  --cuda-sdk=<path>            CUDA SDK installation path.          [default: %(cuda-sdk_default)s]

Universal Parallel C (UPC) Options:
  --upc-gasnet=<path>          GASNET installation path.            [default: %(upc-gasnet_default)s]
  --upc-network=<network>      Set UPC network.                     [default: %(upc-network_default)s]

Memory Options:
  --memory                     Enable memory measurement.           [default: %(memory_default)s]
  --no-memory                  Disable memory measurement.
  --memory-debug               Enable memory debugging.             [default: %(memory-debug_default)s]
  --no-memory-debug            Disable memory debugging.

I/O and Communication Options:
  --io                         Enable I/O measurement.              [default: %(io_default)s]
  --no-io                      Disable I/O measurement.
  --comm-matrix                Enable communication matrix.         [default: %(comm-matrix_default)s]
  --no-comm-matrix             Disable communication matrix.
  
Measurement Options:
  --callpath=<number>          Set the callpath measurement depth.  [default: %(callpath_default)s]
  --profile                    Enable profiling.                    [default: %(profile_default)s]
  --no-profile                 Disable profiling.
  --trace                      Enable tracing.                      [default: %(trace_default)s]
  --no-trace                   Disable tracing.
  --sample                     Enable event-based sampling.         [default: %(sample_default)s]
  --no-sample                  Disable event-based sampling.
"""

_UNDEFINED_DEFAULTS = {'target-arch_default': util.detectDefaultTarget(),
                       'cc_default': 'gcc',
                       'cxx_default': 'g++',
                       'fc_default': 'gfortran',
                       'upc_default': 'gupc',
                       'pdt_default': 'download',
                       'bfd_default': 'download',
                       'unwind_default': 'download',
                       'papi_default': 'download',
                       'dyninst_default': 'download',
                       'openmp_default': False,
                       'pthreads_default': False,
                       'mpi_default': False,
                       'mpi-include_default': '/usr/include',
                       'mpi-lib_default': '/usr/lib',
                       'cuda_default': False,
                       'cuda-sdk_default': '/usr/local/cuda',
                       'upc-gasnet_default': '/usr/local',
                       'upc-network_default': 'smp',
                       'memory_default': False,
                       'memory-debug_default': False,
                       'io_default': True,
                       'comm-matrix_default': False,
                       'callpath_default': '2',
                       'profile_default': True,
                       'trace_default': False,
                       'sample_default': False}

def getProjectOptions():
    userDefaults = taucmd.registry.getUserRegistry().defaults
    systemDefaults = taucmd.registry.getSystemRegistry().defaults
     
    defaults = {}
    features = []
    enabled = []
    disabled = []
    for key, val in _UNDEFINED_DEFAULTS.iteritems():
        try:
            default = userDefaults[key]
        except KeyError:
            try:
                default = systemDefaults[key]
            except KeyError:
                default = val
        if val == False:
            val = 'disabled'
        elif val == True:
            val = 'enabled'
        defaults[key] = val
    try:
        return PROJECT_OPTIONS % defaults
    except KeyError, e:
        raise TauError('%s: Check _UNDEFINED_DEFAULTS' % str(e))


def getConfigFromOptions(args):
    """
    Strip and check command line arguments and apply defaults
    """
    userDefaults = taucmd.registry.getUserRegistry().defaults
    systemDefaults = taucmd.registry.getSystemRegistry().defaults

    config = {}
    exclude = ['--help', '-h']
    downloadable = ['pdt', 'bfd', 'unwind', 'papi', 'dyninst']
    for key, val in args.iteritems():
        if key[0:2] == '--' and key[0:5] != '--no-' and key not in exclude:
            key = key[2:]
            # Check for corresponding '--no-*' argument
            nokey = '--no-%s' % key
            try:
                noval = args[nokey]
            except KeyError:
                config[key] = val
                continue
            if val and noval:
                raise TauConfigurationError('Both %s and %s were specified.  Please pick one.' % (key, nokey))
            elif noval:
                config[key] = False
            elif val:
                if key in downloadable and val.upper() == 'DOWNLOAD':
                    config[key] = 'download'
                else:
                    config[key] = val
            else:
                try:
                    config[key] = userDefaults[key]
                except KeyError:
                    try:
                        config[key] = systemDefaults[key]
                    except KeyError:
                        config[key] = _UNDEFINED_DEFAULTS['%s_default' % key]


    # TODO: Other PDT compilers
    config['pdt_c++'] = 'g++'
    return config


# _BOOL_OPTIONS = [('openmp', 'OpenMP measurement', False),
#                  ('pthreads', 'pthreads measurement', False),
#                  ('mpi', 'MPI measurement', False),
#                  ('cuda', 'NVIDIA CUDA measurement', False),
#                  ('memory', 'Memory measurement', False),
#                  ('memory-debug', 'Memory debugging', False),
#                  ('io', 'I/O measurement', True),
#                  ('comm-matrix', 'Communication matrix', False),
#                  ('profile', 'Profiling', True),
#                  ('trace', 'Tracing', False),
#                  ('sample', 'Event-based sampling', False)]

# def getProjectCommandLineOptions():
#     userDefaults = taucmd.registry.getUserRegistry().defaults
#     systemDefaults = taucmd.registry.getSystemRegistry().defaults
#     
#     fmt = '    {:<27}{:<37}{}'
#     defaults = {}
#     features = []
#     enabled = []
#     disabled = []
#     for key, val in _UNDEFINED_DEFAULTS.iteritems():
#         try:
#             default = userDefaults[key]
#         except KeyError:
#             try:
#                 default = systemDefaults[key]
#             except KeyError:
#                 default = val
#         defaults[key] = val
#     for opt in _BOOL_OPTIONS:
#         key, desc, undef = opt
#         try:
#             default = userDefaults[key]
#         except KeyError:
#             try:
#                 default = systemDefaults[key]
#             except KeyError:
#                 default = undef
#         if default:
#             enabled.append(key)
#             features.append(fmt.format(key, desc, '[default: enabled]'))
#         else:
#             disabled.append(key)
#             features.append(fmt.format(key, desc, '[default: disabled]'))
#         defaults['enable_default'] = ','.join(enabled)
#         defaults['disable_default'] = ','.join(disabled)
#         defaults['features'] = '\n'.join(features)
#     try:
#         return PROJECT_OPTIONS % defaults
#     except KeyError, e:
#         raise TauError('%s: Check _UNDEFINED_DEFAULTS and _PROJECT_BOOL_OPTIONS' % str(e))


class ProjectNameError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class Project(object):
    """
    TODO: DOCS
    """
    def __init__(self, registry, config):
        config['tau-prefix'] = tau.getPrefix(config)
        config['pdt-prefix'] = pdt.getPrefix(config)
        config['bfd-prefix'] = bfd.getPrefix(config)
        self.registry = registry
        self.config = config

    def __str__(self):
        return pprint.pformat(self.config)

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
        return dict((key, self.config[key]) for key in compiler_fields)
    
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
        config = self.config
        if not config['refresh']:
            return
        
        banner = """
        %(bar)s
        *
        * Compiling project %(proj_name)r.
        * This may take a long time but will only be done once.
        *
        %(bar)s
        """ % {'bar': '*'*80, 'proj_name': config['name']}
        LOGGER.info(dedent(banner))

        # Control configure/build output
        devnull = None
        if taucmd.LOG_LEVEL == 'DEBUG':
            stdout = sys.stdout
            stderr = sys.stderr
        else:
            devnull = open(os.devnull, 'w')
            stdout = devnull
            stderr = devnull
        
        # Build PDT, BFD, TAU as needed
        pdt.install(config, stdout, stderr)
        bfd.install(config, stdout, stderr)
        tau.install(config, stdout, stderr)

        # Mark this configuration as built
        if devnull:
            devnull.close() 
        config['refresh'] = False
        config['modified'] = datetime.now()
        self.registry.save()
        
    def getEnvironment(self):
        """
        Returns an environment for use with subprocess.Popen that specifies 
        environment variables for this project
        """
        config = self.config
        env = dict(os.environ)
        bindir = os.path.join(config['tau-prefix'], config['target-arch'], 'bin')
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
        makefiles = os.path.join(config['tau-prefix'], config['target-arch'], 'lib', 'Makefile.tau*')
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
        if taucmd.LOG_LEVEL == 'DEBUG':
            options.append('-optVerbose')
        else:
            options.append('-optQuiet')
        env['TAU_OPTIONS'] = ' '.join(taucmd.DEFAULT_TAU_COMPILER_OPTIONS + options)
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

