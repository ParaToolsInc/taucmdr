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

import os
from tau.error import ConfigurationError, IncompatibleRecordError
from tau.mvc.model import Model



def attributes():
    """Construct attributes dictionary for the measurement model.
    
    We build the attributes in a function so that classes like ``tau.module.project.Project`` are
    fully initialized and usable in the returned dictionary.
    
    Returns:
        dict: Attributes dictionary.
    """
    from tau.model.project import Project
    from tau.model.target import Target
    from tau.model.application import Application
    from tau.cli.arguments import ParseBooleanAction
    from tau.model import require_compiler_family
    from tau.cf.target import host, DARWIN_OS
    from tau.cf.compiler.host import INTEL, GNU

    ompt_intel_only = require_compiler_family(INTEL, "OMPT for OpenMP measurement only works with Intel compilers")
    gomp_gnu_only = require_compiler_family(GNU, "GOMP for OpenMP measurement only works with GNU compilers")

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
            'type': 'string',
            'default': 'tau',
            'description': "generate application profiles",
            'argparse': {'flags': ('--profile',),
                         'group': 'output format',
                         'metavar': '<format>',
                         'nargs': '?',
                         'choices': ('tau', 'merged', 'cubex', 'none'),
                         'const': 'tau'},
            'compat': {'cubex': Target.exclude('scorep_source', None)},
        },
        'trace': {
            'type': 'string',
            'default': 'none',
            'description': "generate application traces",
            'argparse': {'flags': ('--trace',),
                         'group': 'output format',
                         'metavar': '<format>',
                         'nargs': '?',
                         'choices':('slog2', 'otf2', 'none'),
                         'const': 'otf2'},
            'compat': {'otf2': Target.exclude('scorep_source', None)}
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
            'compat': {'automatic': Target.exclude('pdt_source', None)},
            'on_change': Measurement.attribute_changed
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
                        Target.exclude('host_os', DARWIN_OS))},
            'on_change': Measurement.attribute_changed
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
            'on_change': Measurement.attribute_changed
        },
        'select_file': {
            'type': 'string',
            'description': 'specify selective instrumentation file',
            'argparse': {'flags': ('--select-file',),
                         'group': 'instrumentation',
                         'metavar': 'path'},
            'compat': {True:
                       (Target.require('source_inst'),
                        Target.exclude('source_inst', 'never'))},
            'on_change': Measurement.attribute_changed
        },
        'mpi': {
            'type': 'boolean',
            'default': False,
            'description': 'use MPI library wrapper to measure time spent in MPI methods',
            'argparse': {'flags': ('--mpi',),
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True:
                       (Target.require('MPI_CC'),
                        Target.require('MPI_CXX'),
                        Target.require('MPI_FC'))},
            'on_change': Measurement.attribute_changed
        },
        'openmp': {
            'type': 'string',
            'default': 'none',
            'description': 'use specified library to measure time spent in OpenMP directives',
            'argparse': {'flags': ('--openmp',),
                         'metavar': 'library',
                         'choices': ('none', 'opari', 'ompt', 'gomp')},
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
                        Target.require('FC', gomp_gnu_only))},
            'on_change': Measurement.attribute_changed
        },
        'cuda': {
            'type': 'boolean',
            'default': False,
            'description': 'measure cuda events via the CUPTI interface',
            'argparse': {'flags': ('--cuda',),
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
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'compat': {True: (Target.require('cuda'),
                              Application.require('opencl'))}
        },
        'callpath': {
            'type': 'integer',
            'default': 100,
            'description': 'maximum depth for callpath recording',
            'argparse': {'flags': ('--callpath',),
                         'group': 'data',
                         'metavar': 'depth',
                         'nargs': '?',
                         'const': 100,
                         'type': int},
        },
        'io': {
            'type': 'boolean',
            'default': False,
            'description': 'measure time spent in POSIX I/O calls',
            'argparse': {'flags': ('--io',),
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
            'on_change': Measurement.attribute_changed
        },
        'heap_usage': {
            'type': 'boolean',
            'default': False,
            'description': 'measure heap memory usage',
            'argparse': {'flags': ('--heap-usage',),
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
            'on_change': Measurement.attribute_changed
        },
        'metrics': {
            'type': 'array',
            'default': ['TIME'],
            'description': 'performance metrics to gather, e.g. TIME, PAPI_FP_INS',
            'argparse': {'flags': ('--metrics',),
                         'group': 'data',
                         'metavar': '<metric>',
                         'nargs': '+'},
            'compat': {lambda metrics: bool(len([met for met in metrics if 'PAPI' in met])):
                       (Target.require('papi_source'), 
                        Target.exclude('papi_source', None))},
            'on_change': Measurement.metrics_changed
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
        'comm_matrix': {
            'type': 'boolean',
            'default': False,
            'description': 'record the point-to-point communication matrix',
            'argparse': {'flags': ('--comm-matrix',),
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction}
        },
        'throttle': {
            'type': 'boolean',
            'default': True,
            'description': 'throttle lightweight events to reduce overhead',
            'argparse': {'flags': ('--throttle',),
                         'metavar': 'T/F',
                         'nargs': '?',
                         'const': True,
                         'action': ParseBooleanAction},
        },
        'throttle_per_call': {
            'type': 'integer',
            'default': 10,
            'description': 'lightweight event duration threshold in microseconds',
            'argparse': {'flags': ('--throttle-per-call',),
                         'metavar': 'us',
                         'nargs': '?',
                         'const': 10,
                         'type': int},
        },
        'throttle_num_calls': {
            'type': 'integer',
            'default': 100000,
            'description': 'lightweight event call count threshold',
            'argparse': {'flags': ('--throttle-num-calls',),
                         'metavar': 'count',
                         'nargs': '?',
                         'const': 100000,
                         'type': int},
        }
    }


class Measurement(Model):
    """Measurement data model."""
    
    __attributes__ = attributes

    @classmethod
    def attribute_changed(cls, meas, attr, new_value):
        if meas.is_selected():
            old_value = meas.get(attr, None)
            cls.controller(meas.storage).push_to_topic('rebuild_required', {attr: (old_value, new_value)})
    
    @classmethod
    def metrics_changed(cls, meas, attr, new_value):
        if meas.is_selected():
            old_value = meas.get(attr, [])
            old_papi = [metric for metric in old_value if 'PAPI' in metric]
            new_papi = [metric for metric in new_value if 'PAPI' in metric]
            if bool(old_papi) != bool(new_papi):
                cls.controller(meas.storage).push_to_topic('rebuild_required', {attr: (old_value, new_value)})

    def on_create(self):
        def get_flag(key):
            return self.attributes[key]['argparse']['flags'][0]

        if self['profile'].lower() == 'none' and self['trace'].lower() == 'none':
            profile_flag = get_flag('profile')
            trace_flag = get_flag('trace')
            raise ConfigurationError("Profiling, tracing, or both must be enabled",
                                     "Specify %s or %s or both" % (profile_flag, trace_flag))
        
        if ((self['source_inst'].lower() == 'never') and (self['compiler_inst'].lower() == 'never') and 
                (not self['sample']) and (not self['link_only'])):
            source_inst_flag = get_flag('source_inst')
            compiler_inst_flag = get_flag('compiler_inst')
            sample_flag = get_flag('sample')
            link_only_flag = get_flag('link_only')
            raise ConfigurationError("At least one instrumentation method must be used",
                                     "Specify %s, %s, %s, or %s" % (source_inst_flag, compiler_inst_flag, 
                                                                    sample_flag, link_only_flag))
        try:
            select_file = self['select_file']
        except KeyError:
            pass
        else:
            if not os.path.exists(select_file):
                raise ConfigurationError("Selective instrumentation file '%s' not found" % select_file)

    def on_update(self):
        from tau.error import ImmutableRecordError
        from tau.model.experiment import Experiment
        expr_ctrl = Experiment.controller()
        found = expr_ctrl.search({'measurement': self.eid})
        used_by = [expr['name'] for expr in found if expr.data_size() > 0]
        if used_by:
            raise ImmutableRecordError("Measurement '%s' cannot be modified because "
                                       "it is used by these experiments: %s" % (self['name'], ', '.join(used_by)))
        for expr in found:
            try:
                expr.verify()
            except IncompatibleRecordError as err:
                raise ConfigurationError("Changing measurement '%s' in this way will create an invalid condition "
                                         "in experiment '%s':\n    %s." % (self['name'], expr['name'], err),
                                         "Delete experiment '%s' and try again." % expr['name'])

    def is_selected(self):
        """Returns True if this target configuration is part of the selected experiment, False otherwise."""
        from tau.model.project import Project, ProjectSelectionError, ExperimentSelectionError
        try:
            selected = Project.controller().selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError):
            return False
        return selected['measurement'] == self.eid
