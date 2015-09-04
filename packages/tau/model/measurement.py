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

from tau.cli.arguments import ParseBooleanAction
from tau.model import Controller, ByName
from tau.error import ConfigurationError
from tau.cf.compiler import CC_ROLE, CXX_ROLE, FC_ROLE, INTEL_COMPILERS
from tau.cf.compiler.installed import InstalledCompiler
from tau.cf.compiler.mpi import MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE
      

class Measurement(Controller, ByName):
    """Measurement data controller."""      
    
    def on_create(self):
        super(Measurement,self).on_create()
        def get_flag(key):
            return self.attributes[key]['argparse']['flags'][0]
        
        if not (self['profile'] or self['trace']):
            profile_flag = get_flag('profile')
            trace_flag = get_flag('trace')
            raise ConfigurationError("Profiling, tracing, or both must be enabled",
                                     "Specify %s or %s or both" % (profile_flag, trace_flag))
        
        if self['source_inst'] == 'never' and self['compiler_inst'] == 'never' and not self['sample']:
            source_inst_flag = get_flag('source_inst')
            compiler_inst_flag = get_flag('compiler_inst')
            sample_flag = get_flag('sample')
            raise ConfigurationError("At least one instrumentation method must be used",
                                     "Specify %s, %s, or %s" % (source_inst_flag, compiler_inst_flag, sample_flag))


def intel_only(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
    lhs_name = lhs.model_name.lower()
    rhs_name = rhs.model_name.lower()
    msg = "%s = %s in %s requires %s in %s to be an Intel compiler" % (lhs_attr, lhs_value, lhs_name, 
                                                                       rhs_attr, rhs_name)
    try:
        compiler_record = rhs.populate(rhs_attr)
    except KeyError:
        raise ConfigurationError("%s but it is undefined" % msg)
    given_compiler = InstalledCompiler(compiler_record['path'])
    given_family = given_compiler.info.family
    if given_family is not INTEL_COMPILERS:
        raise ConfigurationError("%s but it is a %s compiler" % (msg, given_family),
                                 "OMPT for OpenMP measurement only works with Intel compilers")


# Prevent circular imports by importing controllers from other models 
# only after defining our own controller.  
from tau.model.target import Target
from tau.model.application import Application

Measurement.attributes = {
    'projects': {
        'collection': 'Project',
        'via': 'measurements',
        'description': "projects using this measurement"
    },
    'name': {
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
        'default': False,
        'description': "use event-based sampling to gather performance data",
        'argparse': {'flags': ('--sample',),
                     'group': 'instrumentation',
                     'metavar': 'T/F',
                     'nargs': '?',
                     'const': True,
                     'action': ParseBooleanAction},
        'compat': {True: (Target.discourage('binutils_source', None),
                          Target.discourage('libunwind_source', None))}
    },
    'source_inst': {
        'type': 'string',
        'default': 'automatic',
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
        'default': 'fallback',
        'description': "use compiler-generated callbacks to gather performance data",
        'argparse': {'flags': ('--compiler-inst',),
                     'group': 'instrumentation',
                     'metavar': 'mode',
                     'nargs': '?',
                     'choices': ('always', 'fallback', 'never'),
                     'const': 'always'},
        'compat': {lambda x: x in ('always', 'fallback'):
                   (Target.discourage('binutils_source', None),
                    Target.discourage('libunwind_source', None))}
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
        'default': True,
        'description': 'use MPI library wrapper to measure time spent in MPI methods',
        'argparse': {'flags': ('--mpi',),
                     'group': 'library',
                     'metavar': 'T/F',
                     'nargs': '?',
                     'const': True,
                     'action': ParseBooleanAction},
        'compat': {True:
                   (Target.require(MPI_CC_ROLE.keyword),
                    Target.require(MPI_CXX_ROLE.keyword),
                    Target.require(MPI_FC_ROLE.keyword))}
    },
    'openmp': {
        'type': 'string',
        'default': 'none',
        'description': 'use specified library to measure time spent in OpenMP directives',
        'argparse': {'flags': ('--openmp',),
                     'group': 'library',
                     'metavar': 'library',
                     'choices': ('none', 'opari', 'ompt'),
                     'nargs': 1},
        'compat': {'opari':
                   Application.require('openmp', True),
                   'ompt':
                   (Application.require('openmp', True),
                    Target.require(CC_ROLE.keyword, intel_only),
                    Target.require(CXX_ROLE.keyword, intel_only),
                    Target.require(FC_ROLE.keyword, intel_only))}
    },
    'callpath': {
        'type': 'integer',
        'default': 0,
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
    'memory_usage': {
        'type': 'boolean',
        'default': False,
        'description': 'measure memory consumption',
        'argparse': {'flags': ('--memory-usage',),
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
        'compat': {lambda x: bool(len([met for met in x if 'PAPI' in met])): 
                   Target.exclude('papi_source', None)}
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
    },
}

