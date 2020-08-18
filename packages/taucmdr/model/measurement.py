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
from taucmdr import logger
from taucmdr.error import ConfigurationError, IncompatibleRecordError, ProjectSelectionError, ExperimentSelectionError
from taucmdr.mvc.model import Model
from taucmdr.mvc.controller import Controller

LOGGER = logger.get_logger(__name__)


def attributes():
    """Construct attributes dictionary for the measurement model.

    We build the attributes in a function so that classes like ``taucmdr.module.project.Project`` are
    fully initialized and usable in the returned dictionary.

    Returns:
        dict: Attributes dictionary.
    """
    from taucmdr.model.project import Project
    from taucmdr.model.target import Target
    from taucmdr.model.application import Application
    from taucmdr.cf.platforms import HOST_OS, DARWIN, IBM_CNK
    from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
    from taucmdr.cf.compiler.shmem import SHMEM_CC, SHMEM_CXX, SHMEM_FC

    def _merged_profile_compat(lhs, lhs_attr, lhs_value, rhs):
        if isinstance(rhs, Application):
            if not (rhs['mpi'] or rhs['shmem']):
                lhs_name = lhs.name.lower()
                rhs_name = rhs.name.lower()
                raise IncompatibleRecordError("%s = %s in %s requires either mpi = True or shmem = True in %s" %
                                              (lhs_attr, lhs_value, lhs_name, rhs_name))


    def _discourage_callpath(lhs, lhs_attr, lhs_value, rhs):
        if isinstance(rhs, Measurement):
            if rhs.get('callpath', 0) > 0:
                lhs_name = lhs.name.lower()
                rhs_name = rhs.name.lower()
                LOGGER.warning("%s = %s in %s recommends against callpath > 0 in %s",
                               lhs_attr, lhs_value, lhs_name, rhs_name)

    def _ensure_instrumented(lhs, lhs_attr, lhs_value, rhs):
        if isinstance(rhs, Measurement):
            if rhs.get('source_inst') == 'never' and rhs.get('compiler_inst') == 'never':
                lhs_name = lhs.name.lower()
                rhs_name = rhs.name.lower()
                raise IncompatibleRecordError(
                    "%s = %s in %s requires source_inst and compiler_inst are not both 'never' in %s" %
                    (lhs_attr, lhs_value, lhs_name, rhs_name))

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
        },
        'baseline': {
            'type': 'boolean',
            'default': False,
            'description': "completely disable all instrumentation and measure wall clock time via the OS",
            'argparse': {'flags': ('--baseline',),
                         'group': 'instrumentation'},
            'compat': {True: (Measurement.require('profile', 'tau'),
                              Measurement.require('trace', 'none'))}
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
            'compat': {'cubex': Target.exclude('scorep_source', None),
                       'merged': _merged_profile_compat},
            'rebuild_required': True
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
            'compat': {'otf2': Target.exclude('libotf2_source', None),
                       lambda x: x != 'none': _discourage_callpath},
            'rebuild_required': True
        },
        'sample': {
            'type': 'boolean',
            'default': HOST_OS not in (DARWIN, IBM_CNK),
            'description': "use event-based sampling to gather performance data",
            'argparse': {'flags': ('--sample',),
                         'group': 'instrumentation'},
            'compat': {True: (Target.require('binutils_source'),
                              Target.exclude('binutils_source', None),
                              Target.encourage('libunwind_source'),
                              Target.discourage('libunwind_source', None),
                              Target.exclude('host_os', DARWIN),
                              Measurement.exclude('baseline', True))}
        },
        'source_inst': {
            'type': 'string',
            'default': 'never' if HOST_OS is not DARWIN else 'automatic',
            'description': "use hooks inserted into the application source code to gather performance data",
            'argparse': {'flags': ('--source-inst',),
                         'group': 'instrumentation',
                         'metavar': 'mode',
                         'nargs': '?',
                         'choices': ('automatic', 'manual', 'never'),
                         'const': 'automatic'},
            'compat': {lambda x: x in ('automatic', 'manual'):
                       (Target.exclude('pdt_source', None),
                        Measurement.exclude('baseline', True))},
            'rebuild_required': True
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
                        Target.exclude('host_os', DARWIN),
                        Measurement.exclude('baseline', True))},
            'rebuild_required': True
        },
        'mpi': {
            'type': 'boolean',
            'default': False,
            'description': 'use MPI library wrapper to measure time spent in MPI methods',
            'argparse': {'flags': ('--mpi',)},
            'compat': {True:
                       (Target.require(MPI_CC.keyword),
                        Target.require(MPI_CXX.keyword),
                        Target.require(MPI_FC.keyword),
                        Application.require('mpi', True),
                        Measurement.exclude('baseline', True))},
            'rebuild_required': True
        },
        'openmp': {
            'type': 'string',
            'default': 'ignore',
            'description': 'use specified library to measure time spent in OpenMP directives',
            'argparse': {'flags': ('--openmp',),
                         'metavar': 'library',
                         'choices': ('ignore', 'opari', 'ompt'),
                         'nargs': '?',
                         'const': 'ompt'},
            'compat': {'opari':
                       (Application.require('openmp', True),
                        Measurement.exclude('baseline', True)),
                       'ompt': (Application.require('openmp', True),
                                Measurement.exclude('baseline', True))},
            'rebuild_required': True
        },
        'cuda': {
            'type': 'boolean',
            'default': False,
            'description': 'measure cuda events via the CUPTI interface',
            'argparse': {'flags': ('--cuda',)},
            'compat': {True: (Target.require('cuda_toolkit'),
                              Application.require('cuda', True),
                              Measurement.exclude('baseline', True))},
        },
        'shmem': {
            'type': 'boolean',
            'default': False,
            'description': 'use SHMEM library wrapper to measure time spent in SHMEM methods',
            'argparse': {'flags': ('--shmem',)},
            'compat': {True:
                       (Target.require(SHMEM_CC.keyword),
                        Target.require(SHMEM_CXX.keyword),
                        Target.require(SHMEM_FC.keyword),
                        Application.require('shmem', True),
                        Measurement.exclude('baseline', True))},
            'rebuild_required': True
        },
        'opencl': {
            'type': 'boolean',
            'default': False,
            'description': 'measure OpenCL events',
            'argparse': {'flags': ('--opencl',)},
            'compat': {True: (Target.require('cuda_toolkit'),
                              Application.require('opencl', True),
                              Measurement.exclude('baseline', True))},
        },
        'callpath': {
            'type': 'integer',
            'default': 100,
            'description': 'maximum depth for callpath recording',
            'argparse': {'flags': ('--callpath',),
                         'group': 'data',
                         'metavar': 'depth',
                         'nargs': '?',
                         'const': 100}
        },
        'unwind_depth': {
            'type': 'integer',
            'default': 0,
            'description': 'Record callstack to specified depth',
            'argparse': {'flags': ('--unwind-depth',),
                         'group': 'data',
                         'metavar': 'depth',
                         'nargs': '?',
                         'const': 10},
            'compat': {(lambda unwind: unwind > 0): Measurement.exclude('sample', False)}
        },
        'io': {
            'type': 'boolean',
            'default': False,
            'description': 'measure time spent in POSIX I/O calls',
            'argparse': {'flags': ('--io',)},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'heap_usage': {
            'type': 'boolean',
            'default': False,
            'description': 'measure heap memory usage',
            'argparse': {'flags': ('--heap-usage',),
                         'group': 'memory'},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'system_load': {
            'type': 'boolean',
            'default': False,
            'description': 'measure system load',
            'argparse': {'flags': ('--system-load',),
                         'group': 'data'},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'memory_alloc': {
            'type': 'boolean',
            'default': False,
            'description': 'record memory allocation/deallocation events and detect leaks',
            'argparse': {'flags': ('--memory-alloc',),
                         'group': 'memory'},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'metrics': {
            'type': 'array',
            'default': ['TIME'],
            'description': 'a space separated list of performance metrics to gather, e.g. TIME PAPI_FP_INS',
            'argparse': {'flags': ('--metrics',),
                         'group': 'data',
                         'metavar': '<metric>'},
            'compat': {lambda metrics: bool(len([met for met in metrics if 'PAPI' in met])):
                       (Target.require('papi_source'), Target.exclude('papi_source', None)),
                       lambda x: x != ['TIME']: Measurement.exclude('baseline', True)},
            'rebuild_required': True
        },
        'keep_inst_files': {
            'type': 'boolean',
            'default': False,
            'description': "don't remove instrumented files after compilation",
            'argparse': {'flags': ('--keep-inst-files',),
                         'group': 'instrumentation'},
            'compat': {True: Measurement.exclude('source_inst', 'never')}
        },
        'reuse_inst_files': {
            'type': 'boolean',
            'default': False,
            'description': 'reuse and preserve instrumented files after compilation',
            'argparse': {'flags': ('--reuse-inst-files',),
                         'group': 'instrumentation'},
            'compat': {True: Measurement.exclude('source_inst', 'never')}
        },
        'comm_matrix': {
            'type': 'boolean',
            'default': False,
            'description': 'record the point-to-point communication matrix',
            'argparse': {'flags': ('--comm-matrix',)},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'throttle': {
            'type': 'boolean',
            'default': True,
            'description': 'throttle lightweight events to reduce overhead',
            'argparse': {'flags': ('--throttle',)},
        },
        'throttle_per_call': {
            'type': 'integer',
            'default': 10,
            'description': 'lightweight event duration threshold in microseconds',
            'argparse': {'flags': ('--throttle-per-call',),
                         'metavar': 'us',
                         'nargs': '?',
                         'const': 10},
        },
        'throttle_num_calls': {
            'type': 'integer',
            'default': 100000,
            'description': 'lightweight event call count threshold',
            'argparse': {'flags': ('--throttle-num-calls',),
                         'metavar': 'count',
                         'nargs': '?',
                         'const': 100000},
        },
        'sample_resolution': {
            'type': 'string',
            'default': 'line',
            'description': 'sample resolution',
            'argparse': {'flags': ('--sample-resolution',),
                         'choices': ('file', 'function', 'line',),
                         'metavar': 'file/function/line',
                         'nargs': '?',},
            'compat': {True: (Measurement.require('sample', True))}
        },
        'sampling_period': {
            'type': 'integer',
            'default': 5000,
            'description': 'default sampling period in microseconds',
            'argparse': {'flags': ('--sampling-period',),
                         'metavar': 'us',
                         'nargs': '?',
                         'const': 5000},
            'compat': {True: (Measurement.require('sample', True))},
        },
        'track_memory_footprint': {
            'type': 'boolean',
            'default': False,
            'description': 'track memory footprint',
            'argparse': {'flags': ('--track-memory-footprint',),
                         'group': 'memory'},
            'compat': {True: Measurement.exclude('baseline', True)},
        },
        'metadata_merge': {
            'type': 'boolean',
            'default': True,
            'description': 'merge metadata of TAU profiles',
            'argparse': {'flags': ('--metadata-merge',)},
        },
        'callsite': {
            'type': 'boolean',
            'default': False,
            'description': 'record event callsites',
            'argparse': {'flags': ('--callsite',)},
            'compat': {True: (Target.require('binutils_source'),
                              Target.exclude('binutils_source', None),
                              Target.encourage('libunwind_source'),
                              Target.discourage('libunwind_source', None),
                              Target.exclude('host_os', DARWIN),
                              Measurement.exclude('baseline', True))}
        },
        'select_file': {
            'type': 'string',
            'description': 'specify selective instrumentation file',
            'argparse': {'flags': ('--select-file',),
                         'metavar': 'path'},
            'compat': {bool: (_ensure_instrumented,
                              Application.discourage('linkage', 'static'),
                              Measurement.discourage('throttle', True))},
            'rebuild_required': True
        },
        'update_nightly': {
            'type': 'boolean',
            'default': False,
            'description': 'Download newest TAU nightly',
            'argparse': {'flags': ('--update-nightly',)},
            'compat': {bool: (Target.require('tau_source', 'nightly'))},
        },
        'ptts': {
            'type': 'boolean',
            'default': False,
            'description': 'enable support for PTTS',
            'argparse': {'flags': ('--ptts',)},
        },
        'ptts_post': {
            'type': 'boolean',
            'default': False,
            'description': 'skip application sampling and post-process existing PTTS sample files',
            'argparse': {'flags': ('--ptts-post',)},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'ptts_sample_flags': {
            'type': 'string',
            'default': '',#None,
            'description': 'flags to pass to PTTS sample_ts command',
            'argparse': {'flags': ('--ptts-sample-flags',),
                         'metavar': 'sample_flags'},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'ptts_restart': {
            'type': 'boolean',
            'default': False,
            'description': ('enable restart support within PTTS, allowing application to continue'
                            'running and be reinstrumented after stop'),
            'argparse': {'flags': ('--ptts-restart',)},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'ptts_start': {
            'type': 'string',
            'default': '',#None,
            'description': 'address at which to start a PTTS sampling region',
            'argparse': {'flags': ('--ptts-start',)},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'ptts_stop': {
            'type': 'string',
            'default': '',#None,
            'description': 'address at which to stop a PTTS sampling region',
            'argparse': {'flags': ('--ptts-stop',)},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'ptts_report_flags': {
            'type': 'string',
            'default': '',#None,
            'description': 'flags to pass to PTTS report_ts command',
            'argparse': {'flags': ('--ptts-report-flags',)},
            'compat': {bool: (Measurement.require('ptts', True))},
        },
        'extra_tau_options': {
            'type': 'array',
            'description': "append extra options to TAU_OPTIONS environment variable (not recommended)",
            'rebuild_on_change': True,
            'argparse': {'flags': ('--extra-tau-options',),
                         'nargs': '+',
                         'metavar': '<option>'},
            'compat': {bool: (Measurement.discourage('extra_tau_options'),
                              Measurement.exclude('force_tau_options'),
                              Measurement.exclude('baseline', True))}
        },
        'mpit': {
            'type': 'boolean',
            'default': False,
            'description': 'MPI-T profiling interface',
            'argparse': {'flags': ('--mpit',)},
        },
        'force_tau_options': {
            'type': 'array',
            'description': "forcibly set the TAU_OPTIONS environment variable (not recommended)",
            'rebuild_on_change': True,
            'argparse': {'flags': ('--force-tau-options',),
                         'nargs': '+',
                         'metavar': '<option>'},
            'compat': {bool: (Measurement.discourage('force_tau_options'),
                              Measurement.exclude('extra_tau_options'),
                              Measurement.exclude('baseline', True))}
        },
        'tag': {
            'type': 'string',
            'description': "Narrow search for tags",
            'default': '',#None,
            'argparse': {'flags': ('--tag',),
                         'nargs': '+',
                         'metavar': '<tags>'}
        },
    }


class MeasurementController(Controller):
    """Measurement data controller."""

    def delete(self, keys, context=True):
        # pylint: disable=unexpected-keyword-arg
        from taucmdr.error import ImmutableRecordError
        from taucmdr.model.experiment import Experiment
        changing = self.search(keys, context=context)
        for model in changing:
            expr_ctrl = Experiment.controller()
            found = expr_ctrl.search({'measurement': model.eid})
            used_by = [expr['name'] for expr in found if expr.data_size() > 0]
            if used_by:
                raise ImmutableRecordError("Measurement '%s' cannot be modified because "
                                           "it is used by these experiments: %s" % (model['name'], ', '.join(used_by)))
        return super(MeasurementController, self).delete(keys)

class Measurement(Model):
    """Measurement data model."""

    __attributes__ = attributes
    __controller__ = MeasurementController

    def _check_select_file(self):
        try:
            select_file = self['select_file']
        except KeyError:
            pass
        else:
            if select_file and not os.path.exists(select_file):
                raise ConfigurationError(
                    "Selective instrumentation file '%s' not found" % select_file)

    def _check_metrics(self):
        """Check for TIME in metrics, add it if missing, ensure it is first"""
        try:
            self['metrics'].remove('TIME')
        except KeyError:
            raise ConfigurationError(
                "The metrics attribute should always exist with at least TIME present!")
        except ValueError:
            LOGGER.warning("'TIME' must always be present as the first metric!")
        finally:
            self['metrics'].insert(0, 'TIME')

    def on_create(self):
        self._check_select_file()
        self._check_metrics()

    def on_update(self, changes):
        from taucmdr.error import ImmutableRecordError
        from taucmdr.model.experiment import Experiment
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
        self._check_select_file()
        self._check_metrics()
        if self.is_selected():
            for attr, change in changes.iteritems():
                if self.attributes[attr].get('rebuild_required'):
                    if attr == 'metrics':
                        old_value, new_value = change
                        old_papi = [metric for metric in old_value if 'PAPI' in metric]
                        new_papi = [metric for metric in new_value if 'PAPI' in metric]
                        if bool(old_papi) != bool(new_papi):
                            self.controller(self.storage).push_to_topic('rebuild_required', {attr: change})
                    else:
                        self.controller(self.storage).push_to_topic('rebuild_required', {attr: change})

    def is_selected(self):
        """Returns True if this target configuration is part of the selected experiment, False otherwise."""
        from taucmdr.model.project import Project
        try:
            selected = Project.selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError):
            return False
        return selected['measurement'] == self.eid
