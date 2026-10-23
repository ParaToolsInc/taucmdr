#
# Copyright (c) 2026, ParaTools, Inc.
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
"""``system configure`` subcommand."""

import os
import glob
from taucmdr import logger, util, EXIT_SUCCESS
from taucmdr.error import Error, InternalError
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cli.commands.initialize import COMMAND as initialize_cmd
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.cli.commands.measurement.copy import COMMAND as measurement_copy_cmd
from taucmdr.model.project import Project
from taucmdr.cf.software.tau_installation import TauInstallation, complete_nightly_names
from taucmdr.cf.storage.levels import PROJECT_STORAGE, build_level, writable_system_storage
from taucmdr.cf.storage.project import ProjectStorageError
from taucmdr.cf.platforms import HOST_OS, DARWIN


LOGGER = logger.get_logger(__name__)


class ParseTauAction(arguments.Action):
    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, value, unused_option_string=None):
        value_keywords = 'minimal', 'full'
        if value not in value_keywords:
            value = os.path.abspath(os.path.expanduser(value))
            if not (os.path.isdir(value) or util.path_accessible(value)):
                raise arguments.ArgumentError(self, "'minimal', 'full', or valid path required: %s" % value)
        setattr(namespace, self.dest, value)


def _translate_arg(flag, arg):
    # Handle OpenMP special case, see https://github.com/ParaToolsInc/taucmdr/issues/209
    if flag == '--openmp':
        if arg is True:
            return [flag]
        if arg is False:
            return [flag, 'ignore']
        return [flag, arg]
    if isinstance(arg, str):
        return [flag, arg]
    if isinstance(arg, bool):
        return [f'{flag}={arg}']
    try:
        return [flag] + list(arg)
    except TypeError:
        pass
    return [flag, str(arg)]


def _execute(cmd, argv):
    LOGGER.info('%s %s', str(cmd), ' '.join(argv))
    return cmd.main(argv)


def reset_project(workdir):
    """Delete the project that configuring an earlier set of options left in `workdir`.

    Args:
        workdir (str): The working directory of this command.

    Raises:
        InternalError: Project storage not found in `workdir`.
    """
    try:
        prefix = PROJECT_STORAGE.prefix
    except ProjectStorageError:
        return
    if os.path.dirname(os.path.realpath(prefix)) != os.path.realpath(workdir):
        raise InternalError(f"Project storage '{prefix}' is not found in the working directory '{workdir}'")
    PROJECT_STORAGE.destroy()


def project_argv(args):
    """Return the ``tau initialize`` arguments for the project that configures TAU for `args`."""
    argv = []
    for key, val in vars(args).items():
        for action in initialize_cmd.parser.actions:
            if key == action.dest:
                argv.extend(_translate_arg(action.option_strings[0], val))
                break
    return argv


def _configure_project(args):
    reset_project(os.getcwd())
    argv = project_argv(args)

    # Initialize all default measurements for this set of arguments.
    # Initializing also selects the default experiment, which may build TAU, so it can fail
    # for the same reasons as the select command below.
    try:
        retval = _execute(initialize_cmd, argv)
    except Error as err:
        LOGGER.warning("An error occurred while creating a TAU project with options: %s: %s.\n\n"
                       "See '%s' for details.", argv, err, logger.LOG_FILE)
        return
    if retval != EXIT_SUCCESS:
        LOGGER.warning("An error occurred while creating a TAU project with options: %s.\n\n"
                       "See '%s' for details.", argv, logger.LOG_FILE)
        return
    proj_ctrl = Project.controller()
    proj = proj_ctrl.selected().populate()

    # Add measurements requiring various features to create TAU configurations providing those features
    # **Be sure to repopulate the project** after creating new measurements.
    if getattr(args, 'papi', False):
        for meas in proj['measurements']:
            if meas['name'] != 'baseline':
                _execute(measurement_copy_cmd, [meas['name'], meas['name']+'-papi', '--metrics=TIME,PAPI_TOT_CYC'])
    proj = proj_ctrl.selected().populate()
    if getattr(args, 'openmp', False):
        for meas in proj['measurements']:
            if meas['name'] != 'baseline':
                for pkg in 'ompt', 'opari':
                    _execute(measurement_copy_cmd, [meas['name'], meas['name']+'-'+pkg, '--openmp='+pkg])
    proj = proj_ctrl.selected().populate()

    # Select each measurement to trigger TAU reconfiguration.
    for targ in proj['targets']:
        targ.acquire_sources()
        for app in proj['applications']:
            for meas in proj['measurements']:
                targ_name = targ['name']
                app_name = app['name']
                meas_name = meas['name']
                try:
                    _execute(select_cmd, ['--target', targ_name,
                                          '--application', app_name,
                                          '--measurement', meas_name])
                except Error as err:
                    LOGGER.warning("An error occurred configuring TAU for experiment %s-%s-%s: %s.\n\n"
                                   "See '%s' for details.",
                                   targ_name, app_name, meas_name, err, logger.LOG_FILE)


def full_features(args, host_os):
    """Return the features that the full set of TAU configurations is built with and without.

    Args:
        args: Parsed command line arguments.
        host_os (OperatingSystem): The host operating system.

    Returns:
        dict: Feature names (``papi``, ``openmp``, ``mpi``, ``shmem``, ``cuda``) mapped to True if
        configurations are built both with and without the feature, or False if only without it.
    """
    return {'papi': host_os is not DARWIN,
            'openmp': host_os is not DARWIN,
            'mpi': bool(getattr(args, 'MPI_CC', False) and
                        getattr(args, 'MPI_CXX', False) and
                        getattr(args, 'MPI_FC', False)),
            'shmem': bool(getattr(args, 'SHMEM_CC', False) and
                          getattr(args, 'SHMEM_CXX', False) and
                          getattr(args, 'SHMEM_FC', False)),
            'cuda': bool(getattr(args, 'CUDA_CXX', False) and
                         getattr(args, 'cuda_toolkit', False))}


def _configure_full(args):
    """Procedurally generated TAU configurations.

    Iterate over as many valid TAU projects as possible for the provided command line arguments.
    For each project, iterate over possible experiments and select them to trigger TAU rebuild.
    """
    # If ``features[key]==False`` then only projects without feature `key` will be generated.
    # If True then projects both with and without the feature will be generated.
    # There is a maximum of 2^len(features) possible TAU project configurations.
    features = full_features(args, HOST_OS)

    # Build a bitmask to filter out TAU project configurations where ``features[key] == False``.
    mask = 0
    for i, val in enumerate(features.values()):
        mask |= (not val) << i
    for j in range(1 << len(features)):
        if not j & mask:
            for i, key in enumerate(features.keys()):
                setattr(args, key, bool(j & (1 << i)))
            _configure_project(args)
    return _configure_minimal(args)


def _configure_minimal(_):
    tau = TauInstallation.get_minimal()
    tau.install()
    return tau.install_prefix


def _configure_override_tau_source(storage, args):
    """Per Sameer's request, override managed TAU installation with an existing unmanaged TAU installation."""
    with open(os.path.join(storage.prefix, 'override_tau_source'), 'w') as fout:
        fout.write(args.tau_config)
    LOGGER.info("By default, targets will use '%s' as the TAU installation.", args.tau_config)
    return args.tau_config


class ConfigureCommand(AbstractCommand):
    """Builds TAU configurations in system-level storage."""

    def _construct_parser(self):
        usage = "%s [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--tau-config', help="TAU configurations to build, or a TAU installation to use instead",
                            metavar='(minimal|full|<path>)', default='full', action=ParseTauAction)
        parser.merge(initialize_cmd.parser, include_positional=False,
                     exclude_groups=['project arguments'],
                     exclude_arguments=['project-name', 'target-name', 'application-name', 'measurement-name',
                                        'tau-options', 'from-tau-makefile', 'bare', 'tag'])
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        storage = writable_system_storage()
        TauInstallation.check_env_compat()
        self.logger.info("Building TAU configurations in '%s'", storage.prefix)
        cwd = os.getcwd()
        try:
            with build_level(storage):
                # The projects made while configuring stay out of the user's directories.
                os.chdir(util.mkdtemp().name)
                if args.tau_config == 'minimal':
                    tau_prefix = _configure_minimal(args)
                elif args.tau_config == 'full':
                    tau_prefix = _configure_full(args)
                else:
                    tau_prefix = _configure_override_tau_source(storage, args)
        finally:
            os.chdir(cwd)
            for name in complete_nightly_names(os.path.join(storage.prefix, 'src')):
                self.logger.info("Added '%s' to '%s'", name, os.path.join(storage.prefix, 'src'))
        tau_makefiles = glob.glob('%s/*/lib/Makefile.tau*' % tau_prefix)
        self.logger.info('\n'.join(tau_makefiles))
        self.logger.info("%s TAU makefiles are available at %s", len(tau_makefiles), tau_prefix)
        return EXIT_SUCCESS


COMMAND = ConfigureCommand(__name__, summary_fmt="Build TAU configurations in system-level storage.")
