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

from texttable import Texttable
from tau import EXIT_SUCCESS
from tau import logger, util
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.cli.commands.select import COMMAND as select_cmd
from tau.cli.commands.project.list import COMMAND as project_list_cmd
from tau.cli.commands.target.list import COMMAND as target_list_cmd
from tau.cli.commands.application.list import COMMAND as application_list_cmd
from tau.cli.commands.measurement.list import COMMAND as measurement_list_cmd
from tau.model.project import Project, ProjectSelectionError, ExperimentSelectionError


class DashboardCommand(AbstractCommand):
    
    def construct_parser(self):
        usage = "%s [arguments]" % self.command
        return arguments.get_parser(prog=self.command, usage=usage, description=self.summary)

    def _print_experiments(self, proj):
        parts = []
        experiments = proj.populate('experiments')
        if not experiments:
            label = util.color_text('%s: No experiments' % proj['name'], color='red', attrs=['bold'])
            msg = "%s.  Use `%s` to create a new experiment." % (label, select_cmd) 
            parts.append(msg)
        if experiments:
            title = util.hline("Experiments in project '%s'" % proj['name'], 'cyan')
            header_row = ['Experiment', 'Trials', 'Data Size']
            rows = [header_row]
            for expr in experiments:
                rows.append([expr.title(), len(expr['trials']), util.human_size(expr.data_size())])
            table = Texttable(logger.LINE_WIDTH)
            table.add_rows(rows)
            parts.extend([title, table.draw(), ''])
        try:
            expr = proj.experiment()
        except ExperimentSelectionError:
            pass
        else:
            current = util.color_text('Current experiment: ', 'cyan') + expr.title()
            parts.append(current)
        print '\n'.join(parts)
    
    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        subargs = ['--dashboard']
        proj_ctrl = Project.controller()
        print
        try:
            proj = proj_ctrl.selected()
        except ProjectSelectionError as err:
            project_count = proj_ctrl.count()
            if project_count > 0:
                project_list_cmd.main(subargs)
                err.value = "No project configuration selected. There are %d configurations available." % project_count
            else:
                from tau.cli.commands.project.create import COMMAND as project_create_cmd
                err.value = "No project configurations exist."
                err.hints = ['Use `%s` to create a new project configuration.' % project_create_cmd]
            raise err
        else:
            project_list_cmd.main(subargs)
            target_list_cmd.main([targ['name'] for targ in proj.populate('targets')])
            application_list_cmd.main([targ['name'] for targ in proj.populate('applications')])
            measurement_list_cmd.main([targ['name'] for targ in proj.populate('measurements')])
            self._print_experiments(proj)
        print
        return EXIT_SUCCESS

COMMAND = DashboardCommand(__name__, summary_fmt="Show all project components.")
