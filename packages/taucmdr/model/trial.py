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
import fasteners
from datetime import datetime
from taucmdr import logger, util
from taucmdr.error import ConfigurationError, InternalError
from taucmdr.progress import ProgressIndicator
from taucmdr.mvc.controller import Controller
from taucmdr.mvc.model import Model
from taucmdr.cf.software.tau_installation import TauInstallation
from taucmdr.cf.storage.levels import PROJECT_STORAGE


LOGGER = logger.get_logger(__name__)


def attributes():
    from taucmdr.model.experiment import Experiment
    return {
        'number': {
            'primary_key': True,
            'type': 'integer',
            'required': True,
            'description': 'trial number'
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
        },
        'description': {
            'type': 'string',
            'argparse': {'flags': ('--description',),
                         'metavar': '<text>'},
            'description': "description of this trial"
        },
        'phase': {
            'type': 'string',
            'description': "phase of trial"
        },
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
            self.update({'phase': 'running'}, trial.eid)
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
            LOGGER.info("The job has been added to the queue.")
        return retval

    def _perform_interactive(self, expr, trial, cmd, cwd, env):
        def banner(mark, name, time):
            headline = '\n{:=<{}}\n'.format('== %s %s at %s ==' % (mark, name, time), logger.LINE_WIDTH)
            LOGGER.info(headline)

        banner('BEGIN', expr.name, trial['begin_time'])
        try:
            self.update({'phase': 'running'}, trial.eid)
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

        self.update({'phase': 'post-processing'}, trial.eid)
        data_size = 0
        for dir_path, _, file_names in os.walk(trial.prefix):
            for name in file_names:
                data_size += os.path.getsize(os.path.join(dir_path, name))
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
        LOGGER.info('Experiment: %s', expr['name'])
        LOGGER.info('Command: %s', ' '.join(cmd))
        LOGGER.info('Current working directory: %s', cwd)
        LOGGER.info('Data size: %s bytes', util.human_size(data_size))
        self.update({'phase': 'completed'}, trial.eid)
        return retval

    def perform(self, proj, cmd, cwd, env, description):
        """Performs a trial of an experiment.

        Args:
            expr (Experiment): Experiment data.
            proj (Project): Project data.
            cmd (str): Command to profile, with command line arguments.
            cwd (str): Working directory to perform trial in.
            env (dict): Environment variables to set before performing the trial.
            description (str): Description of this trial.
        """
        with fasteners.InterProcessLock(os.path.join(PROJECT_STORAGE.prefix, '.lock')):
            expr = proj.populate('experiment')
            trial_number = expr.next_trial_number()
            LOGGER.debug("New trial number is %d", trial_number)
            data = {'number': trial_number,
                    'experiment': expr.eid,
                    'command': ' '.join(cmd),
                    'cwd': cwd,
                    'environment': 'FIXME',
                    'phase': 'initializing',
                    'begin_time': str(datetime.utcnow())}
            if description is not None:
                data['description'] = str(description)
            trial = self.create(data)
        # Tell TAU to send profiles and traces to the trial prefix
        env['PROFILEDIR'] = trial.prefix
        env['TRACEDIR'] = trial.prefix
        measurement = expr.populate('measurement')
        if measurement['trace'] == 'otf2' or measurement['profile'] == 'cubex':
            env['SCOREP_EXPERIMENT_DIRECTORY'] = trial.prefix
        targ = expr.populate('target')
        if targ.architecture().is_bluegene():
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
                                     'Check that you have write access')

    def on_delete(self):
        try:
            util.rmtree(self.prefix)
        except Exception as err:  # pylint: disable=broad-except
            if os.path.exists(self.prefix):
                LOGGER.error("Could not remove trial data at '%s': %s", self.prefix, err)
                
    def _postprocess_slog2(self):
        slog2 = os.path.join(self.prefix, 'tau.slog2')
        if os.path.exists(slog2):
            return
        tau = TauInstallation.minimal()
        merged_trc = os.path.join(self.prefix, 'tau.trc')
        merged_edf = os.path.join(self.prefix, 'tau.edf')
        if not os.path.exists(merged_trc) or not os.path.exists(merged_edf):
            tau.merge_tau_trace_files(self.prefix)
        tau.tau_trace_to_slog2(merged_trc, merged_edf, slog2)
        trc_files = glob.glob(os.path.join(self.prefix, '*.trc'))
        edf_files = glob.glob(os.path.join(self.prefix, '*.edf'))
        count_trc_edf = len(trc_files) + len(edf_files)
        LOGGER.info('Cleaning up TAU trace files...')
        with ProgressIndicator(count_trc_edf) as progress_bar:
            count = 0
            for path in trc_files + edf_files:
                os.remove(path)
                count += 1
                progress_bar.update(count)

    def get_data_files(self):
        """Return paths to the trial's data files or directories maped by data type. 
        
        Post-process trial data if necessary and return a dictionary mapping the types of data produced 
        by this trial to paths to related data files or directories.  The paths should be suitable for 
        passing on a command line to one of the known data analysis tools. For example, a trial producing 
        SLOG2 traces and TAU profiles would return ``{"slog2": "/path/to/tau.slog2", "tau": "/path/to/directory/"}``.
        
        Returns:
            dict: Keys are strings indicating the data type; values are filesystem paths.
        """
        expr = self.populate('experiment')
        if self.get('data_size', 0) <= 0:
            raise ConfigurationError("Trial %s of experiment '%s' has no data" % (self['number'], expr['name']))
        meas = self.populate('experiment').populate('measurement')
        profile_fmt = meas.get('profile', 'none')
        trace_fmt = meas.get('trace', 'none')
        if trace_fmt == 'slog2':
            self._postprocess_slog2()
        data = {}
        if profile_fmt == 'tau':
            data[profile_fmt] = self.prefix
        elif profile_fmt == 'merged':
            data[profile_fmt] = os.path.join(self.prefix, 'tauprofile.xml')
        elif profile_fmt == 'cubex':
            data[profile_fmt] = os.path.join(self.prefix, 'profile.cubex')
        elif profile_fmt != 'none':
            raise InternalError("Unhandled profile format '%s'" % profile_fmt)
        trace_fmt = meas.get('trace', 'none')
        if trace_fmt == 'slog2':
            data[trace_fmt] = os.path.join(self.prefix, 'tau.slog2')
        elif trace_fmt == 'otf2':
            data[trace_fmt] = os.path.join(self.prefix, 'traces.otf2')
        elif trace_fmt != 'none':
            raise InternalError("Unhandled trace format '%s'" % trace_fmt)
        return data

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
        tau_env_opts = sorted('%s=%s' % (key, val) for key, val in env.iteritems() 
                              if (key.startswith('TAU_') or 
                                  key.startswith('SCOREP_') or 
                                  key in ('PROFILEDIR', 'TRACEDIR')))
        LOGGER.info('\n'.join(tau_env_opts))
        LOGGER.info(cmd_str)
        try:
            retval = util.create_subprocess(cmd, cwd=cwd, env=env, log=False)
        except OSError as err:
            target = expr.populate('target')
            errno_hint = {errno.EPERM: "Check filesystem permissions",
                          errno.ENOENT: "Check paths and command line arguments",
                          errno.ENOEXEC: "Check that this host supports '%s'" % target['host_arch']}
            raise TrialError("Couldn't execute %s: %s" % (cmd_str, err), errno_hint.get(err.errno, None))
        
        measurement = expr.populate('measurement')
        profiles = []
        for pat in 'profile.*.*.*', 'MULTI__*/profile.*.*.*', 'tauprofile.xml', '*.cubex':
            profiles.extend(glob.glob(os.path.join(self.prefix, pat)))
        
        if profiles:
            LOGGER.info("Trial %s produced %s profile files.", self['number'], len(profiles))
            negative_profiles = [prof for prof in profiles if 'profile.-1' in prof]
            if negative_profiles:
                LOGGER.warning("Trial %s produced a profile with negative node number!"
                               " This usually indicates that process-level parallelism was not initialized,"
                               " (e.g. MPI_Init() was not called) or there was a problem in instrumentation."
                               " Check the compilation output and verify that MPI_Init (or similar) was called.",
                               self['number'])
                for fname in negative_profiles:
                    new_name = fname.replace(".-1.", ".0.") 
                    if not os.path.exists(new_name):
                        LOGGER.info("Renaming %s to %s", fname, new_name)
                        os.rename(fname, new_name)
                    else:
                        raise ConfigurationError("The profile numbers for trial %d cannot be corrected.",
                                                 "Check that the application configuration is correct.",
                                                 "Check that the measurement configuration is correct.",
                                                 "Check for instrumentation failure in the compilation log.")
        elif measurement['profile'] != 'none':
            raise TrialError("Trial did not produce any profiles.")

        traces = []
        for pat in '*.slog2', '*.trc', '*.edf', 'traces/*.def', 'traces/*.evt', 'traces.otf2':
            traces.extend(glob.glob(os.path.join(self.prefix, pat)))
        
        if traces:
            LOGGER.info("Trial %s produced %s trace files.", self['number'], len(traces))
        elif measurement['trace'] != 'none':
            raise TrialError("Application completed successfuly but did not produce any traces.")            

        if retval:
            LOGGER.warning("Return code %d from '%s'", retval, cmd_str)
        return retval
    
    def export(self, dest):
        """Export experiment trial data.
 
        Args:
            dest (str): Path to directory to contain exported data.
 
        Raises:
            ConfigurationError: This trial has no data.
        """
        expr = self.populate('experiment')
        if self.get('data_size', 0) <= 0:
            raise ConfigurationError("Trial %s of experiment '%s' has no data" % (self['number'], expr['name']))
        data = self.get_data_files()
        stem = '%s.trial%d' % (expr['name'], self['number'])
        for fmt, path in data.iteritems(): 
            if fmt == 'tau':
                export_file = os.path.join(dest, stem+'.ppk')
                tau = TauInstallation.minimal()
                tau.create_ppk_file(export_file, path)
            elif fmt == 'merged':
                export_file = os.path.join(dest, stem+'.xml.gz')
                util.create_archive('gz', export_file, [path])
            elif fmt == 'cubex':
                export_file = os.path.join(dest, stem+'.cubex')
                LOGGER.info("Writing '%s'...", export_file)
                util.copy_file(path, export_file)
            elif fmt == 'slog2':
                export_file = os.path.join(dest, stem+'.slog2')
                LOGGER.info("Writing '%s'...", export_file)
                util.copy_file(path, export_file)
            elif fmt == 'otf2':
                export_file = os.path.join(dest, stem+'.tgz')
                expr_dir, trial_dir = os.path.split(os.path.dirname(path))
                items = [os.path.join(trial_dir, item) for item in 'traces', 'traces.def', 'traces.otf2']
                util.create_archive('tgz', export_file, items, expr_dir)
            elif fmt != 'none':
                raise InternalError("Unhandled data file format '%s'" % fmt)

