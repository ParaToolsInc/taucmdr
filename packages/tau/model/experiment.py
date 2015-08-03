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

import os
import glob
import shutil
from tau import logger, settings, util
from tau.error import ConfigurationError, InternalError
from tau.controller import Controller
from tau.model.trial import Trial
from tau.model.compiler_command import CompilerCommand
from tau.cf.tau import TauInstallation
from tau.cf.compiler.installed import InstalledCompiler

LOGGER = logger.getLogger(__name__)


class Experiment(Controller):
    """
    Experiment data model controller
    
    An Experiment uniquely groups a Target, Application, and Measurement and
    will have zero or more Trials. 
    """

    attributes = {
        'project': {
            'model': 'Project',
            'required': True,
            'description': "Project this experiment belongs to"
        },
        'target': {
            'model': 'Target',
            'required': True,
            'description': "Target this experiment runs on"
        },
        'application': {
            'model': 'Application',
            'required': True,
            'description': "Application this experiment uses"
        },
        'measurement': {
            'model': 'Measurement',
            'required': True,
            'description': "Measurement parameters for this experiment"
        },
        'trials': {
            'collection': 'Trial',
            'via': 'experiment',
            'description': "Trials of this experiment"
        },
    }

    def name(self):
        populated = self.populate()
        return '%s (%s, %s, %s)' % (populated['project']['name'],
                                    populated['target']['name'],
                                    populated['application']['name'],
                                    populated['measurement']['name'])

    def prefix(self):
        """
        Storage location for all experiment data
        """
        populated = self.populate()
        return os.path.join(populated['project'].prefix(),
                            populated['target']['name'],
                            populated['application']['name'],
                            populated['measurement']['name'])

    def onCreate(self):
        """
        Initialize experiment storage
        """
        prefix = self.prefix()
        try:
            util.mkdirp(prefix)
        except:
            raise ConfigurationError('Cannot create directory %r' % prefix,
                                     'Check that you have `write` access')

    def onDelete(self):
        """
        Clean up experiment storage
        """
        if self.isSelected():
            settings.unset('experiment_id')
        prefix = self.prefix()
        try:
            shutil.rmtree(prefix)
        except Exception as err:
            if os.path.exists(prefix):
                LOGGER.error(
                    "Could not remove experiment data at '%s': %s" % (prefix, err))

    def select(self):
        """
        Set this experiment as the "selected" experiment.
        """
        if not self.eid:
            raise InternalError('Tried to select an experiment without an eid')
        settings.set('experiment_id', self.eid)

    def isSelected(self):
        return self.eid and settings.get('experiment_id') == self.eid

    @classmethod
    def getSelected(cls):
        """Gets the selected Experiment.
        
        Returns:
            An Experiment object for the currently selected experiment.
        """
        experiment_id = settings.get('experiment_id')
        if experiment_id:
            found = cls.one(eid=experiment_id)
            if not found:
                raise InternalError('Invalid experiment ID: %r' % experiment_id)
            return found
        return None

    def configure(self):
        """Sets up the Experiment for a new trial.
        
        Installs new software as needed.
        """
        populated = self.populate()
        # TODO: Should install packages in a location where all projects can use
        prefix = populated['project']['prefix']
        target = populated['target']
        application = populated['application']
        measurement = populated['measurement']

        host_arch = target['host_arch']
        compilers = target.get_compilers()
        verbose=(logger.LOG_LEVEL == 'DEBUG')
        
        # Configure/build/install TAU if needed
        self.tau = TauInstallation(prefix, target['tau_source'], host_arch, compilers,
                                   verbose=verbose,
                                   pdt_source=target['pdt_source'],
                                   bfd_source=target['bfd_source'],
                                   libunwind_source=target['libunwind_source'],
                                   papi_source=target['papi_source'],
                                   openmp_support=application['openmp'],
                                   pthreads_support=application['pthreads'],
                                   mpi_support=application['mpi'],
                                   cuda_support=application['cuda'],
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
                                   measure_pthreads=None,  # TODO
                                   measure_cuda=None,  # Todo
                                   measure_shmem=None,  # TODO
                                   measure_mpc=None,  # TODO
                                   measure_memory_usage=measurement['memory_usage'],
                                   measure_memory_alloc=measurement['memory_alloc'],
                                   measure_callpath=measurement['callpath'])
        with self.tau:
            self.tau.install()

    def managedBuild(self, compiler_cmd, compiler_args):
        """
        TODO: Docs
        """
        LOGGER.debug("Managed build: %s" % ([compiler_cmd] + compiler_args))
        target = self.populate('target')
        given_compiler = InstalledCompiler(compiler_cmd)
        given_compiler_eid = CompilerCommand.from_info(given_compiler).eid
        target_compiler_eid = target[given_compiler.role.keyword]       

        # Confirm target supports compiler
        if given_compiler_eid != target_compiler_eid:
            target_compiler = CompilerCommand.one(eid=target_compiler_eid).info()
            raise ConfigurationError("Target '%s' is configured with %s '%s', not %s '%s'" %
                                     (target['name'], target_compiler.short_descr, target_compiler.absolute_path,
                                      given_compiler.short_descr, given_compiler.absolute_path),
                                     "Select a different target or compile with '%s'" % 
                                     target_compiler.absolute_path)
        self.configure()
        self.tau.compile(given_compiler.info(), compiler_args)
        
    def managedRun(self, application_cmd, application_args):
        """
        TODO: Docs
        """
        command = util.which(application_cmd)
        if not command:
            raise ConfigurationError("Cannot find executable: %s" % application_cmd)
        cwd = os.getcwd()

        self.configure()
        cmd, env = self.tau.get_application_command(application_cmd, application_args)
        return Trial.perform(self, cmd, cwd, env)

    def show(self, trial_numbers=None):
        """
        Show most recent trial or all trials with given numbers
        """
        self.configure()
        if trial_numbers:
            trials = []
            for n in trial_numbers:
                t = Trial.one({'experiment': self.eid, 'number': n})
                if not t:
                    raise ConfigurationError("No trial number %d in experiment %s" % (n, self.name()))
                trials.append(t)
        else:
            all_trials = self.populate('trials')
            if not all_trials:
                trials = None
            else:
                latest_date = all_trials[0]['begin_time']
                for trial in all_trials:
                    if trial['begin_time'] > latest_date:
                        latest_date = trial['begin_time']
                trials = [trial]
        if not trials:
            raise ConfigurationError("No trials in experiment %s" % self.name(),
                                     "See `tau trial create --help`")
        for trial in trials:
            prefix = trial.prefix()
            profiles = glob.glob(os.path.join(prefix, 'profile.*.*.*'))
            if not profiles:
                profiles = glob.glob(os.path.join(prefix, 'MULTI__*'))
            if profiles:
                self.tau.show_profile(prefix)
