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

import cf.tau_api
import cf.pdt
import cf.bfd
import cf.papi
import cf.libunwind

from tau import logger, settings, error, util, environment
from tau.controller import Controller
from tau.model.compiler import Compiler
from tau.model.trial import Trial

LOGGER = logger.getLogger(__name__)


class Experiment(Controller):

    """
    Experiment data model controller
    """

    attributes = {
        'project': {
            'model': 'Project',
            'required': True,
        },
        'target': {
            'model': 'Target',
            'required': True,
        },
        'application': {
            'model': 'Application',
            'required': True,
        },
        'measurement': {
            'model': 'Measurement',
            'required': True,
        },
        'trials': {
            'collection': 'Trial',
            'via': 'experiment'
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
            raise error.ConfigurationError('Cannot create directory %r' % prefix,
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
        if not self.eid:
            raise error.InternalError(
                'Tried to select an experiment without an eid')
        settings.set('experiment_id', self.eid)

    def isSelected(self):
        if self.eid:
            return settings.get('experiment_id') == self.eid
        return False

    @classmethod
    def getSelected(cls):
        experiment_id = settings.get('experiment_id')
        if experiment_id:
            found = cls.one(eid=experiment_id)
            if not found:
                raise error.InternalError(
                    'Invalid experiment ID: %r' % experiment_id)
            return found
        return None

    def configure(self):
        """
        Installs all software required to perform the experiment
        """
        populated = self.populate()
        # TODO: Should install packages in a location where all projects can
        # use
        prefix = populated['project']['prefix']
        target = populated['target'].populate()
        application = populated['application']
        measurement = populated['measurement']

        cc = target['CC']
        cxx = target['CXX']
        fc = target['FC']
        verbose = (logger.LOG_LEVEL == 'DEBUG')

        # Configure/build/install  if needed
        # TODO:  Needt to change this logic after compatibilty is checked
        #    REFACTOR ******
        # don't instantiate if  target['pdt_source'] is False
        if target['pdt_source']:
            pdt = cf.pdt.Pdt(
                prefix, cxx, target['pdt_source'], target['host_arch'])
            pdt.install()
            self.pdt = pdt
        else:
            self.pdt = None

        if target['bfd_source']:
            bfd = cf.bfd.Bfd(
                prefix, cxx, target['bfd_source'], target['host_arch'])
            bfd.install()
            self.bfd = bfd
        else:
            self.bfd = None

        if target['libunwind_source']:
            libunwind = cf.libunwind.Libunwind(
                prefix, cxx, target['libunwind_source'], target['host_arch'])
            libunwind.install()
            self.libunwind = libunwind
        else:
            self.libunwind = None

        if (util.parseBoolean(target['papi_source'])) or (util.parseBoolean(target['papi_source']) == None):
            papi = cf.papi.Papi(
                prefix, cxx, target['papi_source'], target['host_arch'])
            papi.install()
            self.papi = papi
        else:
            self.papi = None

        if not measurement['source_inst'] and not measurement['compiler_inst']:
            self.pdt = None
            self.bfd = None
            self.papi = None
            self.libunwind = None

        # Configure/build/install TAU if needed
        tau = cf.tau_api.Tau(prefix, cc, cxx, fc, target['tau_source'], target['host_arch'],
                         verbose=verbose,
                         pdt=self.pdt,
                         bfd=self.bfd,
                         papi=self.papi,
                         libunwind=self.libunwind,
                         profile=measurement['profile'],
                         trace=measurement['trace'],
                         sample=measurement['sample'],
                         source_inst=measurement['source_inst'],
                         compiler_inst=measurement['compiler_inst'],
                         keep_inst_files=measurement['keep_inst_files'],
                         reuse_inst_files=measurement['reuse_inst_files'],
                         io_wrapper=measurement['io_wrapper'],
                         link_only=measurement['link_only'],
                         # TODO: Library wrapping inst [dynamic]
                         # TODO: binary rewrite  inst
                         openmp_support=application['openmp'],
                         openmp_measurements=measurement['openmp'],
                         pthreads_support=application['pthreads'],
                         pthreads_measurements=None,  # TODO
                         mpi_support=application['mpi'],
                         mpi_measurements=measurement['mpi'],
                         cuda_support=application['cuda'],
                         cuda_measurements=None,  # Todo
                         shmem_support=application['shmem'],
                         shmem_measurements=None,  # TODO
                         mpc_support=application['mpc'],
                         mic_support=application['mic-linux'],
                         mpc_measurements=None,  # TODO
                         memory_support=None,  # TODO
                         memory_measurements=None,  # TODO
                         callpath=measurement['callpath'],
                         metrics=measurement['metrics']
                         )
        tau.install()
        self.tau = tau

    def managedBuild(self, compiler_cmd, compiler_args):
        """
        TODO: Docs
        """
        self.configure()
        target = self.populate('target')
        measurement = self.populate('measurement')
        given_compiler = Compiler.identify(compiler_cmd)
        target_compiler = target[given_compiler['role']]

        # Confirm target supports compiler
        if given_compiler.eid != target_compiler:
            raise error.ConfigurationError("Target '%s' is configured with %s compiler '%s', not '%s'",
                                           (self['name'], given_compiler['language'],
                                            given_compiler.absolutePath(),
                                            target_compiler.absolutePath()),
                                           "Use a different target or use compiler '%s'" %
                                           target_compiler.absolutePath())

        # Build compile-time environment from component packages
        opts, env = environment.base()
        if measurement['source_inst']:
            if (self.pdt):
                self.pdt.applyCompiletimeConfig(opts, env)
            if (self.bfd):
                self.bfd.applyCompiletimeConfig(opts, env)
            if (self.papi):
                self.papi.applyCompiletimeConfig(opts, env)
            if (self.libunwind):
                self.libunwind.applyCompiletimeConfig(opts, env)
        self.tau.applyCompiletimeConfig(opts, env)

        use_wrapper = measurement['source_inst'] or measurement['comp_inst']
        if use_wrapper:
            compiler_cmd = given_compiler['tau_wrapper']

        cmd = [compiler_cmd] + opts + compiler_args
        retval = util.createSubprocess(cmd, env=env)
        # This would work if TAU's wrapper scripts returned nonzero on error...
#     if retval == 0:
#       LOGGER.info("TAU has finished building the application.  Now use `tau <command>` to gather data from <command>.")
#     else:
#       LOGGER.warning("TAU was unable to build the application.  You can see detailed output in '%s'" % logger.LOG_FILE)
        return retval

    def managedRun(self, application_cmd, application_args):
        """
        TODO: Docs
        """
        self.configure()
        measurement = self.populate('measurement')

        command = util.which(application_cmd)
        if not command:
            raise error.ConfigurationError(
                "Cannot find executable: %s" % application_cmd)
        path = os.path.dirname(command)

        # Check for existing profile files
        if measurement['profile']:
            profiles = glob.glob(os.path.join(path, 'profile.*.*.*'))
            if len(profiles):
                LOGGER.warning(
                    "Profile files found in '%s'! They will be deleted." % path)
                for f in profiles:
                    try:
                        os.remove(f)
                    except:
                        continue
        # Check for existing trace files
        # TODO

        # Build environment from component packages
        opts, env = environment.base()
        self.tau.applyRuntimeConfig(opts, env)

        # TODO : Select tau_exec as needed
        use_tau_exec = False
        if use_tau_exec:
            # TODO: tau_exec flags and command line args
            cmd = ['tau_exec'] + opts + [application_cmd]
        else:
            cmd = [application_cmd]
        cmd += application_args

        return Trial.perform(self, cmd, path, env)

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
                    raise error.ConfigurationError(
                        "No trial number %d in experiment %s" % (n, self.name()))
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
            raise error.ConfigurationError("No trials in experiment %s" % self.name(),
                                           "See `tau trial create --help`")

        opts, env = environment.base()
        self.tau.applyRuntimeConfig(opts, env)

        for trial in trials:
            prefix = trial.prefix()
            profiles = glob.glob(os.path.join(prefix, 'profile.*.*.*'))
            if not profiles:
                profiles = glob.glob(os.path.join(prefix, 'MULTI__*'))
            if profiles:
                self.tau.showProfile(prefix)
