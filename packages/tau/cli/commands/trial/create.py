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
"""``tau trial create`` subcommand."""

from tau import util
from tau.error import ConfigurationError
from tau.cli import arguments
from tau.cli.cli_view import CreateCommand
from tau.model.trial import Trial
from tau.model.project import Project


LAUNCHERS = ['mpirun', 'mpiexec', 'ibrun', 'aprun', 'qsub', 'srun']


class TrialCreateCommand(CreateCommand):
    """``tau trial create`` subcommand."""

    @staticmethod
    def is_compatible(cmd):
        """Check if this subcommand can work with the given command.
        
        Args:
            cmd (str): A command from the command line, e.g. sys.argv[1].
            
        Returns:
            bool: True if this subcommand is compatible with `cmd`.
        """
        return bool(util.which(cmd))

    def _construct_parser(self):
        usage = "%s [arguments] [--] <command> [command_arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('cmd',
                            help="Executable command, e.g. './a.out'",
                            metavar='<command>')
        parser.add_argument('cmd_args', 
                            help="Executable command arguments",
                            metavar='[command_arguments]',
                            nargs=arguments.REMAINDER)
        parser.add_argument('--launcher',
                            help="Launcher command with arguments, e.g. 'mpirun -np 4'",
                            metavar='<command>',
                            nargs=arguments.REMAINDER,
                            default=arguments.SUPPRESS)
        return parser
    
    def _detect_launcher(self, application_cmd):
        cmd = application_cmd[0]
        launcher_cmd = [] 
        if cmd in LAUNCHERS:
            try:
                idx = application_cmd.index('--')
            except ValueError:
                exes = [item for item in enumerate(application_cmd[1:], 1) if util.which(item[1])]
                self.logger.debug("Executables on command line: %s", exes)
                if len(exes) == 1:
                    idx = exes[0][0]
                    launcher_cmd = application_cmd[:idx]
                    application_cmd = application_cmd[idx:]
                else:
                    raise ConfigurationError("TAU is having trouble parsing the command line arguments",
                                             "Check that the command is correct, i.e. does it work without TAU?",
                                             ("Use '--' to seperate %s and its arguments from the application"
                                              " command, e.g. `mpirun -np 4 -- ./a.out -l hello`" % cmd))
            else:
                launcher_cmd = application_cmd[:idx]
                application_cmd = application_cmd[idx+1:]
        self.logger.debug('Launcher: %s', launcher_cmd)
        self.logger.debug('Application: %s', application_cmd)
        return launcher_cmd, application_cmd

    def main(self, argv):
        args = self._parse_args(argv)
        application_cmd = [args.cmd] + args.cmd_args
        try:
            launcher_cmd = args.launcher
        except AttributeError:
            launcher_cmd, application_cmd = self._detect_launcher(application_cmd)

        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        expr = proj.experiment()
        return expr.managed_run(launcher_cmd, application_cmd)


COMMAND = TrialCreateCommand(Trial, __name__, summary_fmt="Run an application under a new experiment trial.")
