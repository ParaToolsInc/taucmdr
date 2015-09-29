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
"""Measurement data model attributes."""

# pylint: disable=invalid-name


from tau.cli.arguments import ParseBooleanAction
from tau.error import ConfigurationError
from tau.core.target import Target
from tau.core.application import Application
from tau.core.measurement import Measurement
from tau.cf.compiler import INTEL_COMPILERS
from tau.cf.compiler.installed import InstalledCompiler


def intel_only(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
    """Compatibility checking callback.
    
    Guarantees that OMPT can only be used when Intel compilers are specified.
    
    Args:
        lhs (Controller): The controller invoking `check_compatibility`.
        lhs_attr (str): Name of the attribute that defines the 'compat' property.
        lhs_value: Value of the attribute that defines the 'compat' property.
        rhs (Controller): Controller we are checking against (argument to `check_compatibility`).
        rhs_attr (str): The right-hand side attribute we are checking for compatibility.
        
    Raises:
        ConfigurationError: OMPT selected when non-Intel compilers specified in target configuration.
    """
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

ATTRIBUTES = {
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
                     'choices': ('none', 'opari', 'ompt'),
                     'nargs': 1},
        'compat': {'opari':
                   Application.require('openmp', True),
                   'ompt':
                   (Application.require('openmp', True),
                    Target.require('CC_ROLE', intel_only),
                    Target.require('CXX_ROLE', intel_only),
                    Target.require('FC_ROLE', intel_only))}
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
        'compat': {lambda metrics: bool(len([met for met in metrics if 'PAPI' in met])): 
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
    }
}
