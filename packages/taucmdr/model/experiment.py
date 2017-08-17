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
"""Experiment data model.

An Experiment uniquely groups a :any:`Target`, :any:`Application`, and :any:`Measurement`
and will have zero or more :any:`Trial`. There is one selected experiment per project.
The selected experiment will be used for application compilation and trial visualization.
"""

import os
import fasteners
import six
from taucmdr import logger, util
from taucmdr.error import ConfigurationError, InternalError, IncompatibleRecordError, ExperimentSelectionError
from taucmdr.mvc.model import Model
from taucmdr.mvc.controller import Controller
from taucmdr.model.trial import Trial
from taucmdr.model.project import Project
from taucmdr.cf.storage.levels import PROJECT_STORAGE, highest_writable_storage


LOGGER = logger.get_logger(__name__)


def attributes():
    from taucmdr.model.target import Target
    from taucmdr.model.application import Application
    from taucmdr.model.measurement import Measurement
    return {
        'name': {
            'primary_key': True,
            'type': 'string',
            'description': 'human-readable experiment name',
            'unique': True,
        },
        'project': {
            'model': Project,
            'required': True,
            'description': "Project this experiment belongs to"
        },
        'target': {
            'model': Target,
            'required': True,
            'description': "The experiment's hardware/software configuration",
            'argparse': {'flags': ('--target',),
                         'metavar': '<name>'}
        },
        'application': {
            'model': Application,
            'required': True,
            'description': "Application this experiment uses",
            'argparse': {'flags': ('--application',),
                         'metavar': '<name>'}
        },
        'measurement': {
            'model': Measurement,
            'required': True,
            'description': "Measurement parameters for this experiment",
            'argparse': {'flags': ('--measurement',),
                         'metavar': '<name>'}
        },
        'trials': {
            'collection': Trial,
            'via': 'experiment',
            'description': "Trials of this experiment"
        },
        'tau_makefile': {
            'type': 'string',
            'description': 'TAU Makefile used during this experiment, if any.'
        }
    }


class ExperimentController(Controller):

    def _restrict_project(self, key_dict):
        key_dict['project'] = Project.controller(self.storage).selected().eid
    
    def search(self, keys=None):
        keys = dict(keys)
        try:
            self._restrict_project(keys)
        except TypeError:
            try:
                for key in keys:
                    self._restrict_project(key)
            except TypeError:
                pass
        return super(ExperimentController, self).search(keys)


class Experiment(Model):
    """Experiment data model."""

    __attributes__ = attributes
    
    __controller__ = ExperimentController

    @classmethod
    def controller(cls, storage=PROJECT_STORAGE):
        return cls.__controller__(cls, storage)

    @classmethod
    def select(cls, name):
        """Changes the selected experiment in the current project.
        
        Raises:
            ExperimentSelectionError: No experiment with the given name in the currently selected project.

        Args:
            name (str): Name of the experiment to select.
        """
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        expr_ctrl = cls.controller()
        data = {"name": name, "project": proj.eid}
        matching = expr_ctrl.search(data)
        if not matching:
            raise ExperimentSelectionError("There is no experiment named '%s' in project '%s'." % (name, proj['name']))
        elif len(matching) > 1:
            raise InternalError("More than one experiment with data %r exists!" % data)
        else:
            expr = matching[0]
        proj_ctrl.select(proj, expr)

    @classmethod
    def rebuild_required(cls):
        """Builds a string indicating if an application rebuild is required.

        Rebuild information is taken from the 'rebuild_required' topic.

        Returns:
            str: String indicating why an application rebuild is required.
        """
        def _fmt(val):
            if isinstance(val, list):
                return "[%s]" % ", ".join(val)
            elif isinstance(val, six.string_types):
                return "'%s'" % val
            else:
                return str(val)
        rebuild_required = cls.controller().pop_topic('rebuild_required')
        if not rebuild_required:
            return ''
        parts = ["Application rebuild required:"]
        for changed in rebuild_required:
            for attr, change in six.iteritems(changed):
                old, new = (_fmt(x) for x in change)
                if old is None:
                    parts.append("  - %s is now set to %s" % (attr, new))
                elif new is None:
                    parts.append("  - %s is now unset" % attr)
                else:
                    parts.append("  - %s changed from %s to %s" % (attr, old, new))
        return '\n'.join(parts)

    @property
    def prefix(self):
        return os.path.join(self.populate('project').prefix, self['name'])

    def verify(self):
        """Checks all components of the experiment for mutual compatibility."""
        populated = self.populate()
        proj = populated['project']
        targ = populated['target']
        app = populated['application']
        meas = populated['measurement']
        for model in targ, app, meas:
            if proj.eid not in model['projects']:
                raise IncompatibleRecordError("%s '%s' is not a member of project configuration '%s'." %
                                              (model.name, model['name'], proj['name']))
        for lhs in [targ, app, meas]:
            for rhs in [targ, app, meas]:
                lhs.check_compatibility(rhs)

    def on_create(self):
        self.verify()
        try:
            util.mkdirp(self.prefix)
        except:
            raise ConfigurationError('Cannot create directory %r' % self.prefix,
                                     'Check that you have `write` access')

    def on_delete(self):
        try:
            util.rmtree(self.prefix)
        except Exception as err:  # pylint: disable=broad-except
            if os.path.exists(self.prefix):
                LOGGER.error("Could not remove experiment data at '%s': %s", self.prefix, err)

    def data_size(self):
        return sum([int(trial.get('data_size', 0)) for trial in self.populate('trials')])

    def next_trial_number(self):
        trials = self.populate('trials')
        for i, j in enumerate(sorted([trial['number'] for trial in trials])):
            if i != j:
                return i
        return len(trials)

    @fasteners.interprocess_locked(os.path.join(highest_writable_storage().prefix, '.lock'))
    def configure(self):
        """Sets up the Experiment for a new trial.

        Installs or configures TAU and all its dependencies.  After calling this
        function, the experiment is ready to operate on the user's application.

        Returns:
            TauInstallation: Object handle for the TAU installation.
        """
        from taucmdr.cf.software.tau_installation import TauInstallation
        LOGGER.debug("Configuring experiment %s", self['name'])
        populated = self.populate(defaults=True)
        target = populated['target']
        application = populated['application']
        measurement = populated['measurement']
        tau = TauInstallation(\
                    target.sources(),
                    target_arch=target.architecture(),
                    target_os=target.operating_system(),
                    compilers=target.compilers(),
                    # TAU feature suppport
                    application_linkage=application.get_or_default('linkage'),
                    openmp_support=application.get_or_default('openmp'),
                    pthreads_support=application.get_or_default('pthreads'),
                    tbb_support=application.get_or_default('tbb'),
                    mpi_support=application.get_or_default('mpi'),
                    mpi_include_path=target.get('mpi_include_path', []),
                    mpi_library_path=target.get('mpi_library_path', []),
                    mpi_libraries=target.get('mpi_libraries', []),
                    cuda_support=application.get_or_default('cuda'),
                    cuda_prefix=target.get('cuda', None),
                    opencl_support=application.get_or_default('opencl'),
                    opencl_prefix=target.get('opencl', None),
                    shmem_support=application.get_or_default('shmem'),
                    shmem_include_path=target.get('shmem_include_path', []),
                    shmem_library_path=target.get('shmem_library_path', []),
                    shmem_libraries=target.get('shmem_libraries', []),
                    mpc_support=application.get_or_default('mpc'),
                    # Instrumentation methods and options
                    source_inst=measurement.get_or_default('source_inst'),
                    compiler_inst=measurement.get_or_default('compiler_inst'),
                    link_only=measurement.get_or_default('link_only'),
                    io_inst=measurement.get_or_default('io'),
                    keep_inst_files=measurement.get_or_default('keep_inst_files'),
                    reuse_inst_files=measurement.get_or_default('reuse_inst_files'),
                    select_file=application.get('select_file', None),
                    # Measurement methods and options
                    profile=measurement.get_or_default('profile'),
                    trace=measurement.get_or_default('trace'),
                    sample=measurement.get_or_default('sample'),
                    metrics=measurement.get_or_default('metrics'),
                    measure_mpi=measurement.get_or_default('mpi'),
                    measure_openmp=measurement.get_or_default('openmp'),
                    measure_opencl=measurement.get_or_default('opencl'),
                    measure_cuda=measurement.get_or_default('cuda'),
                    measure_shmem=measurement.get_or_default('shmem'),
                    measure_heap_usage=measurement.get_or_default('heap_usage'),
                    measure_memory_alloc=measurement.get_or_default('memory_alloc'),
                    measure_comm_matrix=measurement.get_or_default('comm_matrix'),
                    measure_callsite=measurement.get_or_default('callsite'),
                    callpath_depth=measurement.get_or_default('callpath'),
                    throttle=measurement.get_or_default('throttle'),
                    metadata_merge=measurement.get_or_default('metadata_merge'),
                    throttle_per_call=measurement.get_or_default('throttle_per_call'),
                    throttle_num_calls=measurement.get_or_default('throttle_num_calls'),
                    forced_makefile=target.get('forced_makefile', None))
        tau.install()
        self.controller(self.storage).update({'tau_makefile': os.path.basename(tau.get_makefile())}, self.eid)
        return tau

    def managed_build(self, compiler_cmd, compiler_args):
        """Uses this experiment to perform a build operation.

        Checks that this experiment is compatible with the desired build operation,
        prepares the experiment, and performs the operation.

        Args:
            compiler_cmd (str): The compiler command intercepted by TAU Commander.
            compiler_args (list): Compiler command line arguments intercepted by TAU Commander.

        Raises:
            ConfigurationError: The experiment is not configured to perform the desired build.

        Returns:
            int: Build subprocess return code.
        """
        LOGGER.debug("Managed build: %s", [compiler_cmd] + compiler_args)
        target = self.populate('target')
        application = self.populate('application')
        target_compilers = target.check_compiler(compiler_cmd, compiler_args)
        try:
            found_compiler = application.check_compiler(target_compilers)
        except ConfigurationError as err:
            msg = err.value + ("\nTAU will add additional compiler options "
                               "and attempt to continue but this may have unexpected results.")
            LOGGER.warning(msg)
            found_compiler = target_compilers[0]
        # We've found a candidate compiler.  Check that this compiler record is still valid.
        installed_compiler = found_compiler.verify()
        tau = self.configure()
        try:
            proj = self.populate('project')
            tau.force_tau_options = proj['force_tau_options']
        except KeyError:
            pass
        else:
            LOGGER.info("Project '%s' forcibly adding '%s' to TAU_OPTIONS",
                        proj['name'], ' '.join(tau.force_tau_options))
        return tau.compile(installed_compiler, compiler_args)

    def managed_run(self, launcher_cmd, application_cmd, description):
        """Uses this experiment to run an application command.

        Performs all relevent system preparation tasks to run the user's application
        under the specified experimental configuration.

        Args:
            launcher_cmd (list): Application launcher with command line arguments.
            application_cmd (list): Application executable with command line arguments.
            description (str): If not None, a description of the run.

        Raises:
            ConfigurationError: The experiment is not configured to perform the desired run.

        Returns:
            int: Application subprocess return code.
        """
        command = util.which(application_cmd[0])
        if not command:
            raise ConfigurationError("Cannot find executable: %s" % application_cmd[0])
        tau = self.configure()
        cmd, env = tau.get_application_command(launcher_cmd, application_cmd)
        return Trial.controller(self.storage).perform(self, cmd, os.getcwd(), env, description)

    def trials(self, trial_numbers=None):
        """Get a list of modeled trial records.

        If `bool(trial_numbers)` is False, return the most recent trial.
        Otherwise return a list of Trial objects for the given trial numbers.

        Args:
            trial_numbers (list): List of numbers of trials to retrieve.

        Returns:
            list: Modeled trial records.

        Raises:
            ConfigurationError: Invalid trial number or no trials in selected experiment.
        """
        if trial_numbers:
            for num in trial_numbers:
                trials = []
                found = Trial.controller(self.storage).one({'experiment': self.eid, 'number': num})
                if not found:
                    raise ConfigurationError("Experiment '%s' has no trial with number %s" % (self.name, num))
                trials.append(found)
            return trials
        else:
            trials = self.populate('trials')
            if not trials:
                raise ConfigurationError("No trials in experiment %s" % self['name'])
            found = trials[0]
            for trial in trials[1:]:
                if trial['begin_time'] > found['begin_time']:
                    found = trial
            return [found]

