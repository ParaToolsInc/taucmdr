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
from tau import logger, util
from tau.error import ConfigurationError, InternalError, IncompatibleRecordError
from tau.mvc.model import Model
from tau.model.trial import Trial
from tau.model.project import Project
from tau.cf.storage.levels import PROJECT_STORAGE, highest_writable_storage


LOGGER = logger.get_logger(__name__)

PROFILE_EXPORT_FORMATS = ['ppk', 'zip', 'tar', 'tgz', 'tar.bz2']


def attributes():
    from tau.model.target import Target
    from tau.model.application import Application
    from tau.model.measurement import Measurement
    return {
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': 'human-readable experiment name',
            'argparse': {'flags': ('--name',),
                         'metavar': '<name>'}
        },
        'project': {
            'model': Project,
            'required': True,
            'description': "Project this experiment belongs to"
        },
        'target': {
            'model': Target,
            'required': True,
            'description': "Target this experiment runs on"
        },
        'application': {
            'model': Application,
            'required': True,
            'description': "Application this experiment uses"
        },
        'measurement': {
            'model': Measurement,
            'required': True,
            'description': "Measurement parameters for this experiment"
        },
        'trials': {
            'collection': Trial,
            'via': 'experiment',
            'description': "Trials of this experiment"
        }
    }


class Experiment(Model):
    """Experiment data model."""
    
    __attributes__ = attributes
    
    @classmethod
    def controller(cls, storage=PROJECT_STORAGE):
        return cls.__controller__(cls, storage)
    
    @classmethod
    def select(cls, name):
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        expr_ctrl = cls.controller()
        data = {"name": name, "project": proj.eid}
        matching = expr_ctrl.search(data)
        if not matching:
            raise ConfigurationError("There is no experiment named '%s' in project '%s'." % (name, proj['name']))
        elif len(matching) > 1:
            raise InternalError("More than one experiment with data %r exists!" % data)
        else:
            expr = matching[0]            
        proj_ctrl.select(proj, expr)

    @classmethod
    def rebuild_required(cls):
        rebuild_required = cls.__controller__.pop_topic('rebuild_required')
        if not rebuild_required:
            return 'Experiment may be performed without application rebuild.'
        parts = ["Application rebuild required:"]
        for changed in rebuild_required:
            for attr, change in changed.iteritems():
                old, new = change
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
        from tau.cf.target import Architecture, OperatingSystem
        from tau.cf.software.tau_installation import TauInstallation
        LOGGER.debug("Configuring experiment %s", self['name'])
        populated = self.populate(defaults=True)
        target = populated['target']
        application = populated['application']
        measurement = populated['measurement']
        sources = {'tau': target.get('tau_source', None),
                   'binutils': target.get('binutils_source', None),
                   'libunwind': target.get('libunwind_source', None),
                   'papi': target.get('papi_source', None),
                   'pdt': target.get('pdt_source', None),
                   'scorep': target.get('scorep_source', None)}
        tau = TauInstallation(\
                    sources,
                    target_arch=Architecture.find(target['host_arch']),
                    target_os=OperatingSystem.find(target['host_os']),
                    compilers=target.compilers(),
                    # TAU feature suppport
                    openmp_support=application.get_or_default('openmp'),
                    pthreads_support=application.get_or_default('pthreads'),
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
                    select_file=measurement.get('select_file', None),
                    # Measurement methods and options
                    profile=measurement.get_or_default('profile'),
                    trace=measurement.get_or_default('trace'),
                    sample=measurement.get_or_default('sample'),
                    metrics=measurement.get_or_default('metrics'),
                    measure_mpi=measurement.get_or_default('mpi'),
                    measure_openmp=measurement.get_or_default('openmp'),
                    measure_opencl=measurement.get_or_default('opencl'),
                    measure_pthreads=None,  # TODO
                    measure_cuda=None,  # TODO
                    measure_shmem=None,  # TODO
                    measure_mpc=None,  # TODO
                    measure_heap_usage=measurement.get_or_default('heap_usage'),
                    measure_memory_alloc=measurement.get_or_default('memory_alloc'),
                    measure_comm_matrix=measurement.get_or_default('comm_matrix'),
                    callpath_depth=measurement.get_or_default('callpath'),
                    throttle=measurement.get_or_default('throttle'),
                    throttle_per_call=measurement.get_or_default('throttle_per_call'),
                    throttle_num_calls=measurement.get_or_default('throttle_num_calls'))
        tau.install()
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
        target_compiler = target.check_compiler(compiler_cmd, compiler_args)
        tau = self.configure()
        try:
            proj = self.populate('project')
            tau.force_tau_options = proj['force_tau_options']
        except KeyError:
            pass
        else:
            LOGGER.info("Project '%s' forcibly adding '%s' to TAU_OPTIONS", 
                        proj['name'], ' '.join(tau.force_tau_options))
        return tau.compile(target_compiler, compiler_args)
        
    def managed_run(self, launcher_cmd, application_cmd):
        """Uses this experiment to run an application command.
        
        Performs all relevent system preparation tasks to run the user's application
        under the specified experimental configuration.
        
        Args:
            launcher_cmd (list): Application launcher with command line arguments.
            application_cmd (list): Application executable with command line arguments.

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
        return Trial.controller(self.storage).perform(self, cmd, os.getcwd(), env)

    def _get_trials(self, trial_numbers=None):
        """Returns trial data for the given trial numbers.  
        
        If no trial numbers are given, return the most recent trial.
        
        Args:
            trial_numbers (list): List of numbers of trials to retrieve or None.
            
        Returns:
            list: Trial data.
            
        Raises:
            ConfigurationError: Invalid trial number or no trials in this experiment.
        """
        if trial_numbers:
            trials = []
            for num in trial_numbers:
                found = Trial.controller(self.storage).one({'experiment': self.eid, 'number': num})
                if not found:
                    raise ConfigurationError("No trial number %d in experiment %s" % (num, self.name))
                trials.append(found)
        else:
            trials = self.populate('trials')
            if trials:
                found = trials[0]
                for trial in trials[1:]:
                    if trial['begin_time'] > found['begin_time']:
                        found = trial
                trials = [found]
        if not trials:
            raise ConfigurationError("No trials in experiment %s" % self['name'], "See `tau trial create --help`")
        return trials
    
    def show(self, profile_tool=None, trace_tool=None, trial_numbers=None):
        """Show experiment trial data.
        
        Shows the most recent trial or all trials with given numbers.
        
        Args:
            profile_tool (str): Name of the visualization or data processing tool for profiles, e.g. `pprof`.
            trace_tool (str): Name of the visualization or data processing tool for traces, e.g. `vampir`.
            trial_numbers (list): Numbers of trials to show.
            
        Raises:
            ConfigurationError: Invalid trial numbers or no trial data for this experiment.
        """
        tau = self.configure()
        meas = self.populate('measurement')
        for trial in self._get_trials(trial_numbers):
            prefix = trial.prefix
            if meas['profile'] != 'none':
                tau.show_profile(prefix, profile_tool)
            if meas['trace'] != 'none':
                tau.show_trace(prefix, trace_tool)
                
    def export(self, profile_format=PROFILE_EXPORT_FORMATS[0], trial_numbers=None, export_location=None):
        """Export experiment trial data.
        
        Exports the most recent trial or all trials with given numbers.
        
        Args:
            profile_format (str): File format for exported profiles, see :any:`PROFILE_EXPORT_FORMATS` 
            export_location (str): Directory to contain exported profiles.
            trial_numbers (list): Numbers of trials to show.
            
        Raises:
            ConfigurationError: Invalid trial numbers or no trial data for this experiment.
        """
        assert profile_format in PROFILE_EXPORT_FORMATS
        if not export_location:
            export_location = os.getcwd()
        if profile_format == 'ppk':
            tau = self.configure()
            for trial in self._get_trials(trial_numbers):
                ppk_file = self['name'] + '.trial' + str(trial['number']) + '.ppk'
                tau.pack_profiles(trial.prefix, os.path.join(export_location, ppk_file))
        elif profile_format in ('zip', 'tar', 'tgz', 'tar.bz2'):
            for trial in self._get_trials(trial_numbers):
                trial_number = str(trial['number'])
                archive_file = self['name'] + '.trial' + trial_number + '.' + profile_format
                profile_files = [os.path.join(trial_number, os.path.basename(x)) for x in trial.profile_files()]
                old_cwd = os.getcwd()
                os.chdir(os.path.dirname(trial.prefix))
                try:
                    util.create_archive(profile_format, os.path.join(export_location, archive_file), profile_files)
                finally:
                    os.chdir(old_cwd)
        else:
            raise ConfigurationError("Invalid profile format: %s" % profile_format)
