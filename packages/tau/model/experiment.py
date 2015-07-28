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
from tau.model.compiler import Compiler
from tau.model.trial import Trial
from tau.cf.tau import TauInstallation
from tau.cf.compiler import CompilerSet
from tau.cf.pdt import PdtInstallation
from tau.cf.bfd import BfdInstallation
from tau.cf.libunwind import LibunwindInstallation
from tau.cf.papi import PapiInstallation

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
        target = populated['target'].populate()
        application = populated['application']
        measurement = populated['measurement']

        host_arch = target['host_arch']
        compilers = CompilerSet(target['CC'].info(),
                                target['CXX'].info(),
                                target['FC'].info())
        verbose=(logger.LOG_LEVEL == 'DEBUG')
        
        # Determine if we're reusing an existing TAU installation 
        # or if we need to build a new one
        tau_source = target['tau_source']
        if os.path.isdir(tau_source):
            tau_prefix = tau_source
            tau_source = None
            # Existing TAU installations provide their own dependencies
            pdt = None
            bfd = None
            libunwind = None
            papi = None
        else:
            tau_prefix = prefix
            pdt = (measurement['source_inst'] != 'never')
            bfd = (measurement['sample'] or 
                   measurement['compiler_inst'] != 'never' or 
                   measurement['openmp'] != 'ignore')
            libunwind = (measurement['sample'] or 
                         measurement['compiler_inst'] != 'never' or 
                         measurement['openmp'] != 'ignore')
            papi = bool(len([met for met in measurement['metrics'] if 'PAPI' in met]))

        # Install PDT, if needed        
        if pdt:
            pdt = PdtInstallation(prefix, target['pdt_source'], host_arch, compilers)
            pdt.install()

        # Install BFD, if needed
        if bfd:
            bfd = BfdInstallation(prefix, target['bfd_source'], host_arch, compilers)
            bfd.install()

        # Install libunwind, if needed
        if libunwind:
            libunwind = LibunwindInstallation(prefix, target['libunwind_source'],
                                              host_arch, compilers)
            libunwind.install()

        # Install PAPI, if needed
        if papi:
            papi = PapiInstallation(prefix, target['papi_source'], host_arch, compilers)
            papi.install()

        # Configure/build/install TAU if needed
        self.tau = TauInstallation(tau_prefix, tau_source, host_arch, compilers,
                                   pdt=pdt,
                                   bfd=bfd,
                                   libunwind=libunwind,
                                   papi=papi, 
                                   verbose=verbose,
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
        self.tau.install()


    def managedBuild(self, compiler_cmd, compiler_args):
        """
        TODO: Docs
        """
        target = self.populate('target')
        measurement = self.populate('measurement')
        given_compiler = Compiler.identify(compiler_cmd)
        target_compiler = target[given_compiler['role']]

        # Confirm target supports compiler
        if given_compiler.eid != target_compiler:
            target_compiler = Compiler.one(eid=target_compiler)
            raise ConfigurationError("Target '%s' is configured with %s compiler '%s', not '%s'" %
                                     (target['name'], given_compiler['language'],
                                      target_compiler.absolute_path(),
                                      given_compiler.absolute_path()),
                                     "Use a different target or use compiler '%s'" % 
                                     target_compiler.absolute_path())

        # Configure software installation
        self.configure()

        # Build compile-time environment from component packages
        opts, env = self.tau.apply_compiletime_config() 
        use_wrapper = measurement['source_inst'] or measurement['comp_inst']
        if use_wrapper:
            compiler_cmd = given_compiler['tau_wrapper']
        cmd = [compiler_cmd] + opts + compiler_args
        retval = util.createSubprocess(cmd, env=env)
        if retval != 0:
            LOGGER.warning("TAU was unable to build the application.  You can see detailed output in '%s'" % logger.LOG_FILE)
        return retval

    def managedRun(self, application_cmd, application_args):
        """
        TODO: Docs
        """
        self.configure()
        measurement = self.populate('measurement')

        command = util.which(application_cmd)
        if not command:
            raise ConfigurationError("Cannot find executable: %s" % application_cmd)
        cwd = os.getcwd()

        # Check for existing profile files
        if measurement['profile']:
            profiles = glob.glob(os.path.join(cwd, 'profile.*.*.*'))
            if len(profiles):
                LOGGER.warning("Profile files found in '%s'! They will be deleted." % cwd)
                for f in profiles:
                    try:
                        os.remove(f)
                    except:
                        continue
        # Check for existing trace files
        # TODO

        # Build environment from component packages
        opts, env = self.tau.apply_runtime_config()

        # TODO : Select tau_exec as needed
        use_tau_exec = False
        if use_tau_exec:
            # TODO: tau_exec flags and command line args
            cmd = ['tau_exec'] + opts + [application_cmd]
        else:
            cmd = [application_cmd]
        cmd += application_args

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
