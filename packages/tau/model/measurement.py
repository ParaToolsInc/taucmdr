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

import string
from tau import requisite
from tau.arguments import ParseBooleanAction
from tau.controller import Controller, ByName, ModelError


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
            'description': "Projects using this Measurement"
        },
        'name': {
            'type': 'string',
            'unique': True,
            'argparse': {'help': 'measurement configuration name',
                         'metavar': '<measurement_name>'},
            'description': "Measurement configuration name"

        },
        'profile': {
            'type': 'boolean',
            'defaultsTo': True,
            'argparse': {'flags': ('--profile',),
                         'help': 'gather application profiles',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': "Set to True to gather profiles"
        },
        'trace': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--trace',),
                         'help': 'gather application traces',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': "Set to True to gather traces"
        },
        'sample': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--sample',),
                         'help': 'gather application program counter samples',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {'Target': {'pdt_source': requisite.Violation}},
            'description': "Set to True to use event-based sampling to gather performance data"
        },
        'source_inst': {
            'type': 'string',
            'defaultsTo': 'auto',
            'argparse': {'flags': ('--source-inst',),
                         'help': 'use hooks inserted into the application '
                                 'source code to instrument the application',
                         'metavar': 'mode',
                         'nargs': '?',
                         'const': 'auto',
                         'choices': ['automatic', 'manual', 'never']},
            'compat': {'Target': {'pdt_source': requisite.Required}},
            'description': "Use hooks inserted into the application source code "
                           "to instrument the application"
        },
        'compiler_inst': {
            'type': 'string',
            'defaultsTo': 'fallback',
            'argparse': {'flags': ('--compiler-inst',),
                         'help': 'use compiler callbacks to instrument the application',
                         'metavar': 'mode',
                         'nargs': '?',
                         'const': 'always',
                         'choices': ['always', 'fallback', 'never']},
            'compat': {'Target': {'bfd_source': requisite.Recommended, 
                                  'libunwind_source': requisite.Recommended}},
            'description': "Use compiler callbacks to instrument the application"
        },
        'mpi': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--mpi',),
                         'help': 'measure time spent in MPI methods',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {'Application': {'mpi': requisite.Required}},
            'description': "Measure time spent in MPI methods"
        },
        'openmp': {
            'type': 'string',
            'defaultsTo': 'ignore',
            'argparse': {'flags': ('--openmp',),
                         'help': 'approach for measuring time spent in OpenMP directives',
                         'metavar': 'method',
                         'nargs': '?',
                         'const': 'opari',
                         'choices': ['ignore', 'opari', 'ompt']},
            'compat': {'Application': {'openmp': requisite.Required}},
            'description': "Measure time spent in OpenMP directives"
        },
        'callpath': {
            'type': 'integer',
            'defaultsTo': 2,
            'argparse': {'flags': ('--callpath',),
                         'help': 'maximum depth of callpath recording',
                         'metavar': 'depth',
                         'nargs': '?',
                         'const': 2,
                         'type': int},
            'compat': {'Target': {'bfd_source': requisite.Recommended, 
                                  'libunwind_source': requisite.Recommended}},
            'description': 'Maximum depth for callpath recording'
        },
        'io': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--io',),
                         'help': 'measure time spent in I/O calls',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': 'Measure time spent in I/O calls'
        },
        'memory_usage': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--memory-usage',),
                         'help': 'measure memory consumption',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': 'Measure memory consumption'
        },
        'memory_alloc': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--memory-alloc',),
                         'help': 'record memory allocation and deallocation events',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': 'Record memory allocation and deallocation events'
        },
        'metrics': {
            'type': 'array',
            'defaultsTo': ['TIME'],
            'argparse': {'flags': ('--with-metrics',),
                         'help': 'metrics to measure, e.g. TIME or PAPI_FP_INS',
                         'metavar': '<TAU_METRICS>',
                         'nargs': '+'},
            'compat': {'Target': {'papi_source': requisite.Recommended}},
            'description': 'Metrics to measure, e.g. TIME or PAPI_FP_INS',
        },
        'keep_inst_files': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--keep-inst-files',),
                         'help': 'keep instrumented files',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': "Don't remove instrumented files after compilation"
        },
        'reuse_inst_files': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--reuse-inst-files',),
                         'help': 'reuse and preserve instrumented files.',
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'description': 'reuse and preserve instrumented files after compilation',
        },
    }

    _valid_name = set(string.digits + string.letters + '-_.')

    def onCreate(self):
        if set(self['name']) > Measurement._valid_name:
            raise ModelError('%r is not a valid measurement name.' % self['name'],
                             'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
