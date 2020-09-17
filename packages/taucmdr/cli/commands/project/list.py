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
"""``measurement list`` subcommand."""

from types import NoneType
from taucmdr import util, logger
from taucmdr.error import ExperimentSelectionError
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import ListCommand
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.cli.commands.target.list import COMMAND as target_list_cmd
from taucmdr.cli.commands.application.list import COMMAND as application_list_cmd
from taucmdr.cli.commands.measurement.list import COMMAND as measurement_list_cmd
from taucmdr.cli.commands.experiment.list import COMMAND as experiment_list_cmd
from taucmdr.model.project import Project

LOGGER = logger.get_logger(__name__)

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

    def main(self, argv):
        """Command program entry point.

        Args:
            argv (list): Command line arguments.

        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self._parse_args(argv)
        style_args = ['--' + args.style] if hasattr(args, 'style') else []
        levels = arguments.parse_storage_flag(args)
        keys = getattr(args, 'keys', [])
        single = (len(keys) == 1 and len(levels) == 1)

        if single:
            proj_name = keys[0]
            self.title_fmt = "Project Configuration (%(storage_path)s)"
            target_list_cmd.title_fmt = "Targets in project '%s'" % proj_name
            application_list_cmd.title_fmt = "Applications in project '%s'" % proj_name
            measurement_list_cmd.title_fmt = "Measurements in project '%s'" % proj_name
            experiment_list_cmd.title_fmt = "Experiments in project '%s'" % proj_name

        retval = super(ProjectListCommand, self).main(argv)

        if single:
            storage = levels[0]
            ctrl = Project.controller(storage)
            proj = ctrl.one({'name': keys[0]}, context=False)
            for cmd, prop in ((target_list_cmd, 'targets'),
                              (application_list_cmd, 'applications'),
                              (measurement_list_cmd, 'measurements'),
                              (experiment_list_cmd, 'experiments')):
                primary_key = proj.attributes[prop]['collection'].key_attribute
                records = proj.populate(prop, context=False)
                if records:
                    cmd.main([record[primary_key] for record in records] + ['-p'] + [proj['name']] + style_args)
                else:
                    label = util.color_text('%s: No %s' % (proj['name'], prop), color='red', attrs=['bold'])
                    print "%s.  Use `%s` to view available %s.\n" % (label, cmd, prop)
            try:
                expr = proj.experiment()
                if not isinstance(expr, NoneType):
                    print util.color_text("Selected Experiment: ", 'cyan') + expr['name']
            except ExperimentSelectionError:
                print (util.color_text('No selected experiment: ', 'red') +
                       'Use `%s` to create or select an experiment.' % select_cmd)

        return retval

COMMAND = ProjectListCommand()
