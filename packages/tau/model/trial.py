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
"""Trial data model.

Every application of an :any:`Experiment` produces a new :any:`Trial`.  The trial
record completely describes the hardware and software environment that produced
the performance data.
"""

import os
import glob
import errno
from datetime import datetime
from tau import logger, util
from tau.cf.target import IBM_BGQ_ARCH, IBM_BGP_ARCH
from tau.error import ConfigurationError
from tau.mvc.controller import Controller
from tau.mvc.model import Model


LOGGER = logger.get_logger(__name__)

def attributes():
    from tau.model.experiment import Experiment
    return {
        'number': {
            'primary_key': True,
            'type': 'integer',
            'required': True,
            'description': 'trial unique identifier'
        },
        'experiment': {
            'model': Experiment,
            'required': True,
            'description': "this trial's experiment"
        },
        'command': {
            'type': 'string',
            'required': True,
            'description': "command line executed when performing the trial"
        },
        'cwd': {
            'type': 'string',
            'required': True,
            'description': "directory the trial was performed in",
        },
        'environment': {
            'type': 'string',
            'required': True,
            'description': "shell environment the trial was performed in"
        },
        'begin_time': {
            'type': 'datetime',
            'description': "date and time the trial began"
        },
        'end_time': {
            'type': 'datetime',
            'description': "date and time the trial ended"
        },
        'return_code': {
            'type': 'integer',
            'description': "return code of the command executed when performing the trial"
        },
        'data_size': {
            'type': 'integer',
            'description': "the size in bytes of the trial data"
        }
    }


class TrialError(ConfigurationError):
    """Indicates there was an error while performing an experiment trial."""
    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "\n"
                   "Please check the selected configuration for errors or"
                   " send '%(logfile)s' to  %(contact)s for assistance.")


class TrialController(Controller):
    """Trial data controller."""

    def _perform_bluegene(self, expr, trial, cmd, cwd, env):
        if os.path.basename(cmd[0]) != 'qsub':
            raise TrialError("At the moment, TAU Commander requires qsub to launch on BlueGene")
        # Move TAU environment parameters to the command line
        env_parts = {}
        for key, val in env.iteritems():
            if key not in os.environ:
                env_parts[key] = val.replace(":", r"\:").replace("=", r"\=")
        env_str = ':'.join(['%s=%s' % item for item in env_parts.iteritems()])
        cmd = [cmd[0], '--env', '"%s"' % env_str] + cmd[1:]
        env = dict(os.environ)
        try:
            retval = trial.execute_command(expr, cmd, cwd, env)
        except:
            self.delete(trial.eid)
            raise
        if retval != 0:
            raise TrialError("Failed to add job to the queue.",
                             "Verify that the right input parameters were specified.",
                             "Check the program output for error messages.",
                             "Does the selected application configuration correctly describe this program?",
                             "Does the selected measurement configuration specifiy the right measurement methods?",
                             "Does the selected target configuration match the runtime environment?")
        else:
            LOGGER.info("The job has been added to the queue.  Use `tau trial show` to view data when the job ends.")
        return retval

    def _perform_interactive(self, expr, trial, cmd, cwd, env):
        def banner(mark, name, time):
            headline = '\n{:=<{}}\n'.format('== %s %s at %s ==' % (mark, name, time), logger.LINE_WIDTH)
            LOGGER.info(headline)

        banner('BEGIN', expr.name, trial['begin_time'])
        try:
            retval = trial.execute_command(expr, cmd, cwd, env)
        except:
            self.delete(trial.eid)
            raise
        else:
            end_time = str(datetime.utcnow())
            self.update({'end_time': end_time, 'return_code': retval}, trial.eid)
        finally:
            end_time = str(datetime.utcnow())
            banner('END', expr.name, end_time)

        data_size = sum(os.path.getsize(os.path.join(trial.prefix, f)) for f in os.listdir(trial.prefix))
        self.update({'data_size': data_size}, trial.eid)
        if retval != 0:
            if data_size != 0:
                LOGGER.warning("Program exited with nonzero status code: %s", retval)
            else:
                raise TrialError("Program died without producing performance data.",
                                 "Verify that the right input parameters were specified.",
                                 "Check the program output for error messages.",
                                 "Does the selected application configuration correctly describe this program?",
                                 "Does the selected measurement configuration specifiy the right measurement methods?",
                                 "Does the selected target configuration match the runtime environment?")

        measurement = expr.populate('measurement')
        profiles = trial.profile_files()
        if profiles:
            LOGGER.info("Trial %s produced %s profile files.", trial['number'], len(profiles))
            negative_profiles = [prof for prof in profiles if 'profile.-1' in prof]
            if negative_profiles:
                LOGGER.warning("Trial %s produced a profile with negative node number!"
                               " This usually indicates that process-level parallelism was not initialized,"
                               " (e.g. MPI_Init() was not called) or there was a problem in instrumentation."
                               " Check the compilation output and verify that MPI_Init (or similar) was called.",
                               trial['number'])
                for fname in negative_profiles:
                    new_name = fname.replace(".-1.", ".0.") 
                    if not os.path.exists(new_name):
                        LOGGER.info("Renaming %s to %s", fname, new_name)
                        os.rename(fname, new_name)
                    else:
                        raise ConfigurationError("The profile numbers for trial %d are wrong.",
                                                 "Check that the application configuration is correct.",
                                                 "Check that the measurement configuration is correct.",
                                                 "Check for instrumentation failure in the compilation log.")
        elif measurement['profile'] != 'none':
            raise TrialError("Trial did not produce any profiles.")
        traces = trial.trace_files()
        if traces:
            LOGGER.info("Trial %s produced %s trace files.", trial['number'], len(traces))
        elif measurement['trace'] != 'none':
            raise TrialError("Application completed successfuly but did not produce any traces.")            
        return retval

    def perform(self, expr, cmd, cwd, env):
        """Performs a trial of an experiment.

        Args:
            expr (Experiment): Experiment data.
            cmd (str): Command to profile, with command line arguments.
            cwd (str): Working directory to perform trial in.
            env (dict): Environment variables to set before performing the trial.
        """
        trial_number = expr.next_trial_number()
        LOGGER.debug("New trial number is %d", trial_number)
        trial = self.create({'number': trial_number,
                             'experiment': expr.eid,
                             'command': ' '.join(cmd),
                             'cwd': cwd,
                             'environment': 'FIXME',
                             'begin_time': str(datetime.utcnow())})

        # Tell TAU to send profiles and traces to the trial prefix
        env['PROFILEDIR'] = trial.prefix
        env['TRACEDIR'] = trial.prefix
        measurement = expr.populate('measurement')
        if measurement['trace'] == 'otf2':
            env['SCOREP_EXPERIMENT_DIRECTORY'] = trial.prefix

        targ = expr.populate('target')
        is_bluegene = targ['host_arch'] in [str(x) for x in IBM_BGQ_ARCH, IBM_BGP_ARCH]
        if is_bluegene:
            return self._perform_bluegene(expr, trial, cmd, cwd, env)
        else:
            return self._perform_interactive(expr, trial, cmd, cwd, env)


class Trial(Model):
    """Trial data model."""

    __attributes__ = attributes

    __controller__ = TrialController

    @property
    def prefix(self):
        experiment = self.populate('experiment')
        return os.path.join(experiment.prefix, str(self['number']))

    def on_create(self):
        try:
            util.mkdirp(self.prefix)
        except Exception as err:
            raise ConfigurationError('Cannot create directory %r: %s' % (self.prefix, err),
                                     'Check that you have `write` access')

    def on_delete(self):
        # pylint: disable=broad-except
        try:
            util.rmtree(self.prefix)
        except Exception as err:
            if os.path.exists(self.prefix):
                LOGGER.error("Could not remove trial data at '%s': %s", self.prefix, err)

    def profile_files(self):
        """Get this trial's profile files.

        Returns paths to profile files (profile.X.Y.Z).  If the trial produced 
        MULTI__ directories then paths to every profile below every MULTI__ 
        directory are returned. 

        Returns:
            list: Paths to profile files.
        """
        list_profiles = lambda path: glob.glob(os.path.join(path, 'profile.*.*.*'))
        profiles = []
        for multi_dir in glob.iglob(os.path.join(self.prefix, 'MULTI__*')):
            profiles.extend(list_profiles(multi_dir))
        profiles.extend(list_profiles(self.prefix))
        return profiles

    def trace_files(self):
        """Get this trial's trace files.

        Returns paths to trace files: *.[trc,edf,def,evt].

        Returns:
            list: Paths to trace files.
        """
        print self.prefix
        trc_files = glob.glob(os.path.join(self.prefix, '*.trc'))
        edf_files = glob.glob(os.path.join(self.prefix, '*.edf'))
        def_files = glob.glob(os.path.join(self.prefix, 'traces/*.def'))
        evt_files = glob.glob(os.path.join(self.prefix, 'traces/*.evt'))
        return trc_files + edf_files + def_files + evt_files

    def execute_command(self, expr, cmd, cwd, env):
        """Execute a command as part of an experiment trial.

        Creates a new subprocess for the command and checks for TAU data files
        when the subprocess exits.

        Args:
            expr (Experiment): Experiment data.
            cmd (str): Command to profile, with command line arguments.
            cwd (str): Working directory to perform trial in.
            env (dict): Environment variables to set before performing the trial.

        Returns:
            int: Subprocess return code.
        """
        cmd_str = ' '.join(cmd)
        LOGGER.info(cmd_str)
        try:
            retval = util.create_subprocess(cmd, cwd=cwd, env=env)
        except OSError as err:
            target = expr.populate('target')
            errno_hint = {errno.EPERM: "Check filesystem permissions",
                          errno.ENOENT: "Check paths and command line arguments",
                          errno.ENOEXEC: "Check that this host supports '%s'" % target['host_arch']}
            raise TrialError("Couldn't execute %s: %s" % (cmd_str, err), errno_hint.get(err.errno, None))
        if retval:
            LOGGER.warning("Return code %d from '%s'", retval, cmd_str)
        return retval

