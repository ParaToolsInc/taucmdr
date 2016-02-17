# -*- coding: utf-8 -*-
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
# 
"""Measurement data model.

:any:`Measurement` completely describes the performance data measurements
we wish to perform.  It is often the case that we do not wish to gather all
the available data in a single run since overhead would be extreme.  Different
measurements allow us to take different views of the application's performance.
"""

from tau.error import ConfigurationError
from tau.mvc.model import Model
from tau.cf.compiler import INTEL_COMPILERS, GNU_COMPILERS
from tau.cf.compiler.installed import InstalledCompiler
from tau.cf.target import host, DARWIN_OS



def attributes():
    from tau.model.project import Project
    from tau.model.target import Target
    from tau.model.application import Application
    from tau.cli.arguments import ParseBooleanAction
    from tau.model import require_compiler_family

    ompt_intel_only = require_compiler_family(INTEL_COMPILERS, 
                                              "OMPT for OpenMP measurement only works with Intel compilers")
    gomp_gnu_only = require_compiler_family(GNU_COMPILERS, 
                                            "GOMP for OpenMP measurement only works with GNU compilers")

    return {
        'projects': {
            'collection': Project,
            'via': 'measurements',
            'description': "projects using this measurement"
        },
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': "measurement configuration name",
            'argparse': {'help': 'measurement configuration name',
                         'metavar': '<measurement_name>'},
        
        },
        'profile': {
            'type': 'boolean',
            'default': True,
            'description': "generate application profiles",
            'argparse': {'flags': ('--profile',),
                         'group': 'output format',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'trace': {
            'type': 'boolean',
            'default': False,
            'description': "generate application traces",
            'argparse': {'flags': ('--trace',),
                         'group': 'output format',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: Target.discourage('score-p_source', None)}
        },
        'sample': {
            'type': 'boolean',
            'default': host.operating_system() is not DARWIN_OS,
            'description': "use event-based sampling to gather performance data",
            'argparse': {'flags': ('--sample',),
                         'group': 'instrumentation',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: (Target.require('binutils_source'),
                              Target.exclude('binutils_source', None),
                              Target.require('libunwind_source'),
                              Target.exclude('libunwind_source', None),
                              Target.exclude('host_os', DARWIN_OS))}
        },
        'source_inst': {
            'type': 'string',
            'default': 'never' if host.operating_system() is not DARWIN_OS else 'automatic',
            'description': "use hooks inserted into the application source code to gather performance data",
            'argparse': {'flags': ('--source-inst',),
                         'group': 'instrumentation',
                         'metavar': 'mode',
                         'nargs': '?',
                         'choices': ('automatic', 'manual', 'never'),
                         'const': 'automatic'},
            'compat': {lambda x: x in ('automatic', 'manual'):
                       Target.exclude('pdt_source', None)}
        },
        'compiler_inst': {
            'type': 'string',
            'default': 'never',
            'description': "use compiler-generated callbacks to gather performance data",
            'argparse': {'flags': ('--compiler-inst',),
                         'group': 'instrumentation',
                         'metavar': 'mode',
                         'nargs': '?',
                         'choices': ('always', 'fallback', 'never'),
                         'const': 'always'},
            'compat': {lambda x: x in ('always', 'fallback'):
                       (Target.require('binutils_source'),
                        Target.exclude('binutils_source', None),
                        Target.require('libunwind_source'),
                        Target.exclude('libunwind_source', None),
                        Target.exclude('host_os', DARWIN_OS))}
        },
        'link_only': {
            'type': 'boolean',
            'default': False,
            'description': "don't instrument, only link the TAU library to the application",
            'argparse': {'flags': ('--link-only',),
                         'group': 'instrumentation',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'mpi': {
            'type': 'boolean',
            'default': False,
            'description': 'use MPI library wrapper to measure time spent in MPI methods',
            'argparse': {'flags': ('--mpi',),
                         'group': 'library',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True:
                       (Target.require('MPI_CC'),
                        Target.require('MPI_CXX'),
                        Target.require('MPI_FC'))}
        },
        'openmp': {
            'type': 'string',
            'default': 'none',
            'description': 'use specified library to measure time spent in OpenMP directives',
            'argparse': {'flags': ('--openmp',),
                         'group': 'library',
                         'metavar': 'library',
                         'choices': ('none', 'opari', 'ompt', 'gomp'),
                         'nargs': 1},
            'compat': {'opari':
                       Application.require('openmp', True),
                       'ompt':
                       (Application.require('openmp', True),
                        Target.require('CC', ompt_intel_only),
                        Target.require('CXX', ompt_intel_only),
                        Target.require('FC', ompt_intel_only)),
                       'gomp':
                       (Application.require('openmp', True),
                        Target.require('CC', gomp_gnu_only),
                        Target.require('CXX', gomp_gnu_only),
                        Target.require('FC', gomp_gnu_only))}
        },
        'cuda': {
            'type': 'boolean',
            'default': False,
            'description': 'measure cuda events via the CUPTI interface',
            'argparse': {'flags': ('--cuda',),
                         'group': 'library',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: Target.require('cuda')}
        },
        'opencl': {
            'type': 'boolean',
            'default': False,
            'description': 'measure OpenCL events',
            'argparse': {'flags': ('--opencl',),
                         'group': 'library',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: Target.require('opencl')}
        },
        'callpath': {
            'type': 'integer',
            'default': 2,
            'description': 'maximum depth for callpath recording',
            'argparse': {'flags': ('--callpath',),
                         'group': 'data',
                         'metavar': 'depth',
                         'nargs': '?',
                         'const': 2,
                         'type': int},
        },
        'io': {
            'type': 'boolean',
            'default': False,
            'description': 'measure time spent in POSIX I/O calls',
            'argparse': {'flags': ('--io',),
                         'group': 'library',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'heap_usage': {
            'type': 'boolean',
            'default': False,
            'description': 'measure heap memory usage',
            'argparse': {'flags': ('--heap_usage',),
                         'group': 'memory',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'memory_alloc': {
            'type': 'boolean',
            'default': False,
            'description': 'record memory allocation and deallocation events',
            'argparse': {'flags': ('--memory-alloc',),
                         'group': 'memory',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'metrics': {
            'type': 'array',
            'default': ['TIME'],
            'description': 'performance metrics to gather, e.g. TIME, PAPI_FP_INS',
            'argparse': {'flags': ('--metrics',),
                         'group': 'data',
                         'metavar': '<METRIC>',
                         'nargs': '+'},
            'compat': {lambda metrics: bool(len([met for met in metrics if 'PAPI' in met])):
                       (Target.require('papi_source'), 
                        Target.exclude('papi_source', None))}
        },
        'keep_inst_files': {
            'type': 'boolean',
            'default': False,
            'description': "don't remove instrumented files after compilation",
            'argparse': {'flags': ('--keep-inst-files',),
                         'group': 'instrumentation',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: Measurement.exclude('source_inst', 'never')}
        },
        'reuse_inst_files': {
            'type': 'boolean',
            'default': False,
            'description': 'reuse and preserve instrumented files after compilation',
            'argparse': {'flags': ('--reuse-inst-files',),
                         'group': 'instrumentation',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: Measurement.exclude('source_inst', 'never')}
        }
    }


class Measurement(Model):
    """Measurement data model."""
    
    __attributes__ = attributes

    def on_create(self):
        super(Measurement, self).on_create()
        def get_flag(key):
            return self.attributes[key]['argparse']['flags'][0]

        if not (self['profile'] or self['trace']):
            profile_flag = get_flag('profile')
            trace_flag = get_flag('trace')
            raise ConfigurationError("Profiling, tracing, or both must be enabled",
                                     "Specify %s or %s or both" % (profile_flag, trace_flag))
        
        if ((self['source_inst'] == 'never') and (self['compiler_inst'] == 'never') and 
            (not self['sample']) and (not self['link_only'])):
            source_inst_flag = get_flag('source_inst')
            compiler_inst_flag = get_flag('compiler_inst')
            sample_flag = get_flag('sample')
            link_only_flag = get_flag('link_only')
            raise ConfigurationError("At least one instrumentation method must be used",
                                     "Specify %s, %s, %s, or %s" % (source_inst_flag, compiler_inst_flag, 
                                                                    sample_flag, link_only_flag))


