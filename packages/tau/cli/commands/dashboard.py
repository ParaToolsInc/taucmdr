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
"""``tau dashboard`` subcommand."""

from tau import EXIT_SUCCESS
from tau import cli
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.cli.commands.select import COMMAND as select_command
from tau.model.project import Project


class DashboardCommand(AbstractCommand):
    
    def construct_parser(self):
        usage = "%s [arguments]" % self.command
        return arguments.get_parser(prog=self.command, usage=usage, description=self.summary)

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        subargs = ['--dashboard']
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        if proj:
            cli.execute_command(['target', 'list'], [targ['name'] for targ in proj.populate('targets')])
            cli.execute_command(['application', 'list'], [targ['name'] for targ in proj.populate('applications')])
            cli.execute_command(['measurement', 'list'], [targ['name'] for targ in proj.populate('measurements')])
            cli.execute_command(['trial', 'list'])
        else:
            cli.execute_command(['project', 'list'], subargs)
            cli.execute_command(['target', 'list'], subargs)
            cli.execute_command(['application', 'list'], subargs)
            cli.execute_command(['measurement', 'list'], subargs)
            print "No project selected.  Try `%s`." % select_command.command
        print 
        return EXIT_SUCCESS

COMMAND = DashboardCommand(__name__, summary_fmt="Show all project components.")
