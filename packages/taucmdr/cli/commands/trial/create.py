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
"""``trial create`` subcommand."""

from taucmdr import util
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CreateCommand
from taucmdr.model.trial import Trial
from taucmdr.model.project import Project


class TrialCreateCommand(CreateCommand):
    """``trial create`` subcommand."""

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
        usage = "%s [arguments] [launcher] [launcher_arguments] [--] <command> [command_arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('launcher',
                            help="Application launcher command, e.g. mpirun",
                            metavar='launcher',
                            nargs='?')
        parser.add_argument('launcher_args',
                            help="Application launcher arguments",
                            metavar='launcher_arguments',
                            nargs=arguments.REMAINDER)
        parser.add_argument('cmd',
                            help="Executable command, e.g. './a.out'",
                            metavar='command')
        parser.add_argument('cmd_args',
                            help="Executable command arguments",
                            metavar='command_arguments',
                            nargs=arguments.REMAINDER)
        return parser
    
    def main(self, argv):
        self._parse_args(argv)
        launcher_cmd, application_cmds = Trial.parse_launcher_cmd(argv)
        self.logger.debug("Launcher command: %s", launcher_cmd)
        self.logger.debug("Application commands: %s", application_cmds)
        return Project.selected().experiment().managed_run(launcher_cmd, application_cmds)


COMMAND = TrialCreateCommand(Trial, __name__, summary_fmt="Create new trial of the selected experiment.")
