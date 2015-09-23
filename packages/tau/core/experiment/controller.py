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
"""Experiment data model controller."""


import os
import glob
import shutil
from tau import logger, util
from tau.error import ConfigurationError, InternalError
from tau.core.mvc import Controller
from tau.core.trial import Trial
from tau.core.compiler import Compiler
from tau.core.project import Project
from tau.cf.software.tau_installation import TauInstallation
from tau.cf.compiler.installed import InstalledCompiler


LOGGER = logger.get_logger(__name__)


class Experiment(Controller):
    """Experiment data controller."""

    def __init__(self, *args, **kwargs):
        super(Experiment, self).__init__(*args, **kwargs)
        self.tau = None

    def name(self):
        populated = self.populate()
        return '%s (%s, %s, %s)' % (populated['project']['name'],
                                    populated['target']['name'],
                                    populated['application']['name'],
                                    populated['measurement']['name'])

    def prefix(self):
        populated = self.populate()
        return os.path.join(populated['project'].prefix(),
                            populated['target']['name'],
                            populated['application']['name'],
                            populated['measurement']['name'])

    def on_create(self):
        prefix = self.prefix()
        try:
            util.mkdirp(prefix)
        except:
            raise ConfigurationError('Cannot create directory %r' % prefix,
                                     'Check that you have `write` access')

    def on_delete(self):
        # pylint: disable=broad-except
        self.unselect()
        prefix = self.prefix()
        try:
            shutil.rmtree(prefix)
        except Exception as err:
            if os.path.exists(prefix):
                LOGGER.error("Could not remove experiment data at '%s': %s", prefix, err)

    def select(self):
        if not self.eid:
            raise InternalError('Tried to select an experiment without an eid')
        Project.update({'selected': self.eid}, eids=self['project'])
        self.configure()

    def unselect(self):
        if not self.eid:
            raise InternalError('Tried to unselect an experiment without an eid')
        if self.is_selected():
            Project.unset(['selected'], eids=self['project'])
        self.configure()

    def is_selected(self):
        proj = self.populate('project')
        return self.eid == proj['selected']

    def configure(self):
        """Sets up the Experiment for a new trial.
        
        Installs or configures TAU and all its dependencies.  After calling this 
        function, the experiment is ready to operate on the user's application.
        """
        populated = self.populate()
        prefix = populated['project']['prefix']
        target = populated['target']
        application = populated['application']
        measurement = populated['measurement']
        verbose = (logger.LOG_LEVEL == 'DEBUG')
        
        # Configure/build/install TAU if needed
        self.tau = TauInstallation(prefix, target['tau_source'], target['host_arch'], target['host_os'], 
                                   target.compilers(),
                                   verbose=verbose,
                                   pdt_source=target.get('pdt_source', None),
                                   binutils_source=target.get('binutils_source', None),
                                   libunwind_source=target.get('libunwind_source', None),
                                   papi_source=target.get('papi_source', None),
                                   openmp_support=application['openmp'],
                                   pthreads_support=application['pthreads'],
                                   mpi_support=application['mpi'],
                                   mpi_include_path=target.get('mpi_include_path', []),
                                   mpi_library_path=target.get('mpi_library_path', []),
                                   mpi_libraries=target.get('mpi_libraries', []),
                                   cuda_support=application['cuda'],
                                   cuda_prefix=target.get('cuda', None),
                                   opencl_support=application['opencl'],
                                   opencl_prefix=target.get('opencl', None),
                                   shmem_support=application['shmem'],
                                   mpc_support=application['mpc'],
                                   # Instrumentation methods and options            
                                   source_inst=measurement['source_inst'],
                                   compiler_inst=measurement['compiler_inst'],
                                   link_only=measurement['link_only'],
                                   io_inst=measurement['io'],
                                   keep_inst_files=measurement['keep_inst_files'],
                                   reuse_inst_files=measurement['reuse_inst_files'],
                                   # Measurements TAU must support
                                   profile=measurement['profile'],
                                   trace=measurement['trace'],
                                   sample=measurement['sample'],
                                   metrics=measurement['metrics'],
                                   measure_mpi=measurement['mpi'],
                                   measure_openmp=measurement['openmp'],
                                   measure_opencl=measurement['opencl'],
                                   measure_pthreads=None,  # TODO
                                   measure_cuda=None,  # Todo
                                   measure_shmem=None,  # TODO
                                   measure_mpc=None,  # TODO
                                   measure_memory_usage=measurement['memory_usage'],
                                   measure_memory_alloc=measurement['memory_alloc'],
                                   callpath_depth=measurement['callpath'])
        with self.tau:
            self.tau.install()

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
        given_compiler = InstalledCompiler(compiler_cmd)
        given_compiler_eid = Compiler.register(given_compiler).eid
        target_compiler_eid = target[given_compiler.info.role.keyword]       
        # Confirm target supports compiler
        if given_compiler_eid != target_compiler_eid:
            target_compiler = Compiler.one(eid=target_compiler_eid).info()
            raise ConfigurationError("Target '%s' is configured with %s '%s', not %s '%s'" %
                                     (target['name'], target_compiler.info.short_descr, target_compiler.absolute_path,
                                      given_compiler.info.short_descr, given_compiler.absolute_path),
                                     "Select a different target or compile with '%s'" % 
                                     target_compiler.absolute_path)
        self.configure()
        return self.tau.compile(given_compiler, compiler_args)
        
    def managed_run(self, application_cmd, application_args):
        """Uses this experiment to run an application command.
        
        Performs all relevent system preparation tasks to run the user's application
        under the specified experimental configuration.
        
        Args:
            application_cmd (str): The application command intercepted by TAU Commander.
            application_args (list): Application command line arguments intercepted by TAU Commander.
            
        Raises:
            ConfigurationError: The experiment is not configured to perform the desired run.
            
        Returns:
            int: Application subprocess return code.
        """
        command = util.which(application_cmd)
        if not command:
            raise ConfigurationError("Cannot find executable: %s" % application_cmd)
        self.configure()
        cmd, env = self.tau.get_application_command(application_cmd, application_args)
        return Trial.perform(self, cmd, os.getcwd(), env)

    def show(self, tool_name=None, trial_numbers=None):
        """Show experiment trial data.
        
        Shows the most recent trial or all trials with given numbers.
        
        Args:
            tool_name (str): Name of the visualization or data processing tool to use, e.g. `pprof`.
            trial_numbers (list): Numbers of trials to show.
            
        Raises:
            ConfigurationError: Invalid trial numbers or no trial data for this experiment.
        """
        self.configure()
        if trial_numbers:
            trials = []
            for num in trial_numbers:
                found = Trial.one({'experiment': self.eid, 'number': num})
                if not found:
                    raise ConfigurationError("No trial number %d in experiment %s" % (num, self.name()))
                trials.append(found)
        else:
            all_trials = self.populate('trials')
            if not all_trials:
                raise ConfigurationError("No trials in experiment %s" % self.name(),
                                         "See `tau trial create --help`")
            else:
                found = all_trials[0]
                for trial in all_trials[1:]:
                    if trial['begin_time'] > found['begin_time']:
                        found = trial
                trials = [found] 
        for trial in trials:
            prefix = trial.prefix()
            profiles = glob.glob(os.path.join(prefix, 'profile.*.*.*'))
            if not profiles:
                profiles = glob.glob(os.path.join(prefix, 'MULTI__*'))
            if profiles:
                self.tau.show_profile(prefix, tool_name)

