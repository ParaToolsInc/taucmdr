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
"""``tau initialize`` subcommand."""

from tau import EXIT_SUCCESS
from tau import cli
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.cli.commands.select import COMMAND as select_command
from tau.model.project import Project
from tau.storage.project import UninitializedProjectError
from tau.storage.levels import PROJECT_STORAGE

class InitializeCommand(AbstractCommand):
    """``tau initialize`` subcommand."""
    
    def construct_parser(self):
        components = 'project', 'target', 'application', 'measurement'
        usage = "%s %s" % (self.command, ' '.join('[%s_name]' % comp for comp in components))
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        for comp in components:
            parser.add_argument('%s_name' % comp,
                                help="New %s name" % comp,
                                metavar='%s_name' % comp,
                                nargs='?',
                                default='default_%s' % comp)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except UninitializedProjectError:
            self.logger.debug("No project found, initializing a new project.")
            PROJECT_STORAGE.connect_filesystem()
            project_name = args.project_name
            comp_names = []
            for comp in 'target', 'application', 'measurement':
                comp_name = getattr(args, '%s_name' % comp)
                comp_names.append(comp_name)
                cli.execute_command([comp, 'create'], [comp_name])
            cli.execute_command(['project', 'create'], [project_name] + comp_names)
            cli.execute_command(['select'], [project_name])
            cli.execute_command(['dashboard'])
        else:
            if proj:
                self.logger.info("Selected project: '%s'", proj['name'])
            else:
                self.logger.info("No project selected.  Try `%s`.", 
                                 select_command.command)
        
        return EXIT_SUCCESS

COMMAND = InitializeCommand(__name__, summary_fmt="Initialize TAU Commander.")
