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
"""``tau measurement`` subcommand."""

from texttable import Texttable
from tau import logger, util
from tau.cli.arguments import STORAGE_LEVEL_FLAG
from tau.cli.cli_view import ListCommand
from tau.cli.commands.target.list import COMMAND as target_list_cmd
from tau.cli.commands.application.list import COMMAND as application_list_cmd
from tau.cli.commands.measurement.list import COMMAND as measurement_list_cmd
from tau.cli.commands.select import COMMAND as select_cmd
from tau.storage.levels import STORAGE_LEVELS
from tau.model.project import Project, ExperimentSelectionError


class ProjectListCommand(ListCommand):
    """Base class for the `list` subcommand of command line views."""

    def __init__(self):
        def _name_list(attr):
            return lambda x: ', '.join([p['name'] for p in x[attr]])
        dashboard_columns = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                             {'header': 'Targets', 'function': _name_list('targets')},
                             {'header': 'Applications', 'function': _name_list('applications')},
                             {'header': 'Measurements', 'function': _name_list('measurements')},
                             {'header': '# Experiments', 'function': lambda x: len(x['experiments'])}]
        super(ProjectListCommand, self).__init__(Project, __name__, dashboard_columns=dashboard_columns)

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
            if expr:
                current = util.color_text('Current experiment: ', 'cyan') + expr.title()
            else:
                current = (util.color_text('No experiment: ', 'red') + 
                           ('Use `%s` to configure a new experiment' % select_cmd))  
            parts.append(current)
        print '\n'.join(parts)

    def main(self, argv):
        """Command program entry point.

        Args:
            argv (list): Command line arguments.

        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        keys = getattr(args, 'keys', [])
        levels = getattr(args, STORAGE_LEVEL_FLAG, [])
        single = (len(keys) == 1 and len(levels) == 1)

        if single:
            proj_name = keys[0]
            self.title_fmt = "Project Configuration (%(storage_path)s)"
            target_list_cmd.title_fmt = "Targets in project '%s'" % proj_name
            application_list_cmd.title_fmt = "Applications in project '%s'" % proj_name
            measurement_list_cmd.title_fmt = "Measurements in project '%s'" % proj_name

        retval = super(ProjectListCommand, self).main(argv)

        if single:
            storage = STORAGE_LEVELS[levels[0]]
            ctrl = Project.controller(storage)
            proj = ctrl.one({'name': keys[0]})
            for cmd, prop in ((target_list_cmd, 'targets'),
                              (application_list_cmd, 'applications'),
                              (measurement_list_cmd, 'measurements')):
                records = proj.populate(prop)
                if records:
                    cmd.main([record['name'] for record in records])
                else:
                    label = util.color_text('%s: No %s' % (proj['name'], prop), color='red', attrs=['bold'])
                    print "%s.  Use `%s` to view available %s.\n" % (label, cmd, prop)
            self._print_experiments(proj)
            if proj.get('force_tau_options', False):
                self.logger.warning("Project '%s' will add '%s' to TAU_OPTIONS without error checking.", 
                                    proj['name'], ' '.join(proj['force_tau_options']))
        return retval

COMMAND = ProjectListCommand()

