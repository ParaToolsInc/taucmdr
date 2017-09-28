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
"""Application data model.

:any:`Application` fully describes the application configuration to be profiled,
including the features the application uses, e.g. OpenMP, MPI, CUDA, etc.
Each specific application **configuration** has its own application record.
For example, if an application can operate with or without OpenMP then there
are potentially two application records for the same application code: one
specifying OpenMP is used and the other specifying OpenMP is not used.
"""

import os

import six
from taucmdr.error import IncompatibleRecordError, ConfigurationError, ProjectSelectionError, ExperimentSelectionError
from taucmdr.mvc.model import Model
from taucmdr.cf.compiler.host import HOST_COMPILERS
from taucmdr.cf.compiler.mpi import MPI_COMPILERS
from taucmdr.cf.compiler.shmem import SHMEM_COMPILERS
from taucmdr.cf.compiler.cuda import CUDA_COMPILERS


def attributes():
    from taucmdr.model.project import Project
    from taucmdr.model.target import Target
    from taucmdr.model.measurement import Measurement
    from taucmdr.cf.platforms import DARWIN, HOST_OS, CRAY_CNL
    return {
        'projects': {
            'collection': Project,
            'via': 'applications',
            'description': 'projects using this application',
            'hashed': False,
            'direction': 'up'
        },
        'name': {
            'primary_key': True,
            'type': 'string',
            'description': 'application configuration name',
            'unique': True,
            'hashed': True
        },
        'openmp': {
            'type': 'boolean',
            'description': 'application uses OpenMP',
            'default': False,
            'argparse': {'flags': ('--openmp',)},
            'rebuild_required': True,
            'hashed': True
        },
        'pthreads': {
            'type': 'boolean',
            'description': 'application uses pthreads',
            'default': False,
            'argparse': {'flags': ('--pthreads',)},
            'rebuild_required': True,
            'hashed': True
        },
        'tbb': {
            'type': 'boolean',
            'description': 'application uses Thread Building Blocks (TBB)',
            'default': False,
            'argparse': {'flags': ('--tbb',)},
            'rebuild_required': True,
            'hashed': True
        },
        'mpi': {
            'type': 'boolean',
            'default': False,
            'description': 'application uses MPI',
            'argparse': {'flags': ('--mpi',)},
            'compat': {True: Measurement.require('mpi', True)},
            'rebuild_required': True,
            'hashed': True
        },
        'cuda': {
            'type': 'boolean',
            'default': False,
            'description': 'application uses NVIDIA CUDA',
            'argparse': {'flags': ('--cuda',)},
            'compat': {True: Target.require('cuda_toolkit')},
            'rebuild_required': True,
            'hashed': True
        },
        'opencl': {
            'type': 'boolean',
            'default': False,
            'description': 'application uses OpenCL',
            'argparse': {'flags': ('--opencl',)},
            'compat': {True: (Target.require('cuda_toolkit'),
                              Measurement.encourage('opencl', True))},
            'rebuild_required': True,
            'hashed': True
        },
        'shmem': {
            'type': 'boolean',
            'default': False,
            'description': 'application uses SHMEM',
            'argparse': {'flags': ('--shmem',)},
            'rebuild_required': True,
            'hashed': True
        },
        'mpc': {
            'type': 'boolean',
            'default': False,
            'description': 'application uses MPC',
            'argparse': {'flags': ('--mpc',)},
            'rebuild_required': True,
            'hashed': True
        },
        'select_file': {
            'type': 'string',
            'description': 'specify selective instrumentation file',
            'argparse': {'flags': ('--select-file',),
                         'metavar': 'path'},
            'compat': {True: Measurement.exclude('source_inst', 'never')},
            'rebuild_required': True,
            'hashed': True
        },
        'linkage': {
            'type': 'string',
            'default': 'static' if HOST_OS is CRAY_CNL else 'dynamic',
            'description': "application linkage",
            'argparse': {'flags': ('--linkage',),
                         'metavar': '<linkage>',
                         'choices': ('static', 'dynamic')},
            'compat': {'static': Target.exclude('host_os', DARWIN)},
            'rebuild_required': True,
            'hashed': True
        },
    }


class Application(Model):
    """Application data model."""

    __attributes__ = attributes

    def _check_select_file(self):
        try:
            select_file = self['select_file']
        except KeyError:
            pass
        else:
            if select_file and not os.path.exists(select_file):
                raise ConfigurationError("Selective instrumentation file '%s' not found" % select_file)

    def on_create(self):
        self._check_select_file()

    def on_update(self, changes):
        from taucmdr.error import ImmutableRecordError
        from taucmdr.model.experiment import Experiment
        expr_ctrl = Experiment.controller(self.storage)
        found = expr_ctrl.search({'application': self.eid})
        using_app = [expr['name'] for expr in found if expr.data_size() > 0]
        if using_app:
            raise ImmutableRecordError("Application '%s' cannot be modified because "
                                       "it is used by these experiments: %s" % (self['name'], ', '.join(using_app)))
        for expr in found:
            try:
                expr.verify()
            except IncompatibleRecordError as err:
                raise ConfigurationError("Changing application '%s' in this way will create an invalid condition "
                                         "in experiment '%s':\n    %s." % (self['name'], expr['name'], err),
                                         "Delete experiment '%s' and try again." % expr['name'])
        self._check_select_file()
        if self.is_selected():
            for attr, change in six.iteritems(changes):
                if self.attributes[attr].get('rebuild_required'):
                    self.controller(self.storage).push_to_topic('rebuild_required', {attr: change})

    def is_selected(self):
        """Returns True if this target configuration is part of the selected experiment, False otherwise."""
        from taucmdr.model.project import Project
        try:
            selected = Project.selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError):
            return False
        if not selected:
            return False
        return selected['application'] == self.eid

    def check_compiler(self, compilers):
        """Checks a list of compilers for compatibility with this application configuration.

        Args:
            compilers (list): :any:`Compiler` instances that could possibly be compatible with this application.

        Returns:
            Compiler: A compiler from `compilers` that can be used to build the application.

        Raises:
            ConfigurationError: No compiler in `compilers` is compatible with this application.
        """
        found = []
        for compiler in compilers:
            is_host = compiler['role'].startswith(HOST_COMPILERS.keyword)
            is_mpi = compiler['role'].startswith(MPI_COMPILERS.keyword) and self['mpi']
            is_shmem = compiler['role'].startswith(SHMEM_COMPILERS.keyword) and self['shmem']
            is_cuda = compiler['role'].startswith(CUDA_COMPILERS.keyword) and self['cuda']
            if is_host or is_mpi or is_shmem or is_cuda:
                found.append(compiler)
        if not found:
            raise ConfigurationError("Application '%s' is not compatible with any of these compilers:\n  %s" %
                                     (self['name'], '\n  '.join(compiler['path'] for compiler in compilers)))
        # If more than one compiler is compatible then choose the first one
        return found[0]
