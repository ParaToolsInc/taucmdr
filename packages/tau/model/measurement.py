#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

from tau import requisite
from tau.arguments import ParseBooleanAction
from tau.controller import Controller, ByName
from tau.error import ConfigurationError


class Measurement(Controller, ByName):
    """
    Measurement data model controller.
    
    A Measurement describes how data will be gathered during the measurement
    phase of the performance engineering workflow.
    """

    attributes = {
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
            'compat': {'Target': {'pdt_source': requisite.Violation}},
        },
        'source_inst': {
            'type': 'string',
            'default': 'automatic',
            'description': "use hooks inserted into the application source code to gather performance data",
            'argparse': {'flags': ('--source-inst',),
                         'group': 'instrumentation',
                         'metavar': 'mode',
                         'nargs': '?',
                         'const': 'auto',
                         'choices': ['automatic', 'manual', 'never']},
            'compat': {'Target': {'pdt_source': requisite.Required}},
        },
        'compiler_inst': {
            'type': 'string',
            'default': 'fallback',
            'description': "use compiler-generated callbacks to gather performance data",
            'argparse': {'flags': ('--compiler-inst',),
                         'group': 'instrumentation',
                         'metavar': 'mode',
                         'nargs': '?',
                         'const': 'always',
                         'choices': ['always', 'fallback', 'never']},
            'compat': {'Target': {'binutils_source': requisite.Recommended, 
                                  'libunwind_source': requisite.Recommended}},
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
            'compat': {'Application': {'mpi': requisite.Required}},
        },
        'openmp': {
            'type': 'string',
            'default': 'compiler_default',
            'description': 'use specified library to measure time spent in OpenMP directives',
            'argparse': {'flags': ('--openmp',),
                         'group': 'library',
                         'metavar': 'library',
                         'nargs': '?',
                         'const': 'opari',
                         'choices': ['compiler_default', 'opari', 'ompt']},
            'compat': {'Application': {'openmp': requisite.Required}},
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
            'compat': {'Target': {'binutils_source': requisite.Recommended, 
                                  'libunwind_source': requisite.Recommended}},
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
            'description': 'metrics to measure, e.g. TIME or PAPI_FP_INS',
            'argparse': {'flags': ('--metrics',),
                         'group': 'data',
                         'metavar': '<METRIC>',
                         'nargs': '+'},
            'compat': {'Target': {'papi_source': requisite.Recommended}},
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
        },
    }

    def onCreate(self):
        def get_flag(key):
            return self.attributes[key]['argparse']['flags'][0]
        
        if not (self['profile'] or self['trace']):
            profile_flag = get_flag('profile')
            trace_flag = get_flag('trace')
            raise ConfigurationError("Profiling, tracing, or both must be enabled",
                                     "Specify %s or %s or both" % (profile_flag, trace_flag))
        
        if (self['source_inst'] == 'never' and self['compiler_inst'] == 'never' and not self['sample']):
            source_inst_flag = get_flag('source_inst')
            compiler_inst_flag = get_flag('compiler_inst')
            sample_flag = get_flag('sample')
            raise ConfigurationError("At least one instrumentation method must be used",
                                     "Specify %s, %s, or %s" % (source_inst_flag, compiler_inst_flag, sample_flag))
            
         
