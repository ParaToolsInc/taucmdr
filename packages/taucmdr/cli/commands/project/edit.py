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
"""``project edit`` subcommand."""

from taucmdr import EXIT_SUCCESS
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import EditCommand
from taucmdr.model.project import Project
from taucmdr.model.target import Target
from taucmdr.model.application import Application
from taucmdr.model.measurement import Measurement


class ProjectEditCommand(EditCommand):
    """``project edit`` subcommand."""

    def _construct_parser(self):
        usage = "%s <project_name> [arguments]" % self.command
        parser = arguments.get_parser_from_model(self.model,
                                                 use_defaults=False,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        parser.add_argument('--new-name',
                            help="change the project's name",
                            metavar='<new_name>', 
                            dest='new_name',
                            default=arguments.SUPPRESS)
        parser.add_argument('--add',
                            help="Add target, application, or measurement configurations to the project",
                            metavar='<conf>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--remove',
                            help="Remove target, application, or measurement configurations from the project",
                            metavar='<conf>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--add-targets',
                            help="Add target configurations to the project",
                            metavar='<target>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--add-applications',
                            help="Add application configurations to the project",
                            metavar='<application>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--add-measurements',
                            help="Add measurement configurations to the project",
                            metavar='<measurement>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--remove-targets',
                            help="Remove target configurations from the project",
                            metavar='<target>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--remove-applications',
                            help="Remove application configurations from the project",
                            metavar='<application>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--remove-measurements',
                            help="Remove measurement configurations from the project",
                            metavar='<measurement>',
                            nargs='+',
                            default=arguments.SUPPRESS)
        return parser

    def _parse_add_args(self, args, tar_ctrl, app_ctrl, meas_ctrl, targets, applications, measurements):
        added = set()
        for attr, ctrl, dest in [('add_targets', tar_ctrl, targets),
                                 ('add_applications', app_ctrl, applications),
                                 ('add_measurements', meas_ctrl, measurements)]:
            names = getattr(args, attr, [])
            for name in names:
                found = ctrl.one({'name': name})
                if not found:
                    self.parser.error("There is no %s named '%s'" % (ctrl.model.name, name))
                dest.add(found.eid)
                added.add(found)
    
        for name in set(getattr(args, "add", [])):
            tar = tar_ctrl.one({'name': name})
            app = app_ctrl.one({'name': name})
            mes = meas_ctrl.one({'name': name})
            tam = set([tar, app, mes]) - set([None])
            if len(tam) > 1:
                self.parser.error("'%s' is ambiguous. Use --add-targets, --add-applications,"
                                  " or --add-measurements to specify configuration type" % name)
            elif len(tam) == 0:
                self.parser.error("'%s' is not a target, application, or measurement" % name)
            else:
                added.update(tam)
            if tar:
                targets.add(tar.eid)
            elif app:
                applications.add(app.eid)
            elif mes:
                measurements.add(mes.eid)
        return added

    def _parse_remove_args(self, args, tar_ctrl, app_ctrl, meas_ctrl, targets, applications, measurements):
        removed = set()
        for attr, ctrl, dest in [('remove_targets', tar_ctrl, targets),
                                 ('remove_applications', app_ctrl, applications),
                                 ('remove_measurements', meas_ctrl, measurements)]:
            names = getattr(args, attr, [])
            for name in names:
                found = ctrl.one({'name': name})
                if not found:
                    self.parser.error('There is no %s named %r' % (ctrl.model.name, name))
                dest.remove(found.eid)
                removed.add(found)
    
        for name in set(getattr(args, "remove", [])):
            tar = tar_ctrl.one({'name': name})
            app = app_ctrl.one({'name': name})
            mes = meas_ctrl.one({'name': name})
            tam = set([tar, app, mes]) - set([None])
            if len(tam) > 1:
                self.parser.error("'%s' is ambiguous. Use --remove-targets, --remove-applications,"
                                  " or --remove-measurements to specify configuration type" % name)
            elif len(tam) == 0:
                self.parser.error("'%s' is not a target, application, or measurement" % name)
            else:
                removed.update(tam)
            if tar:
                targets.remove(tar.eid)
            elif app:
                applications.remove(app.eid)
            elif mes:
                measurements.remove(mes.eid)
        return removed

    def main(self, argv):
        from taucmdr.cli.commands.project.list import COMMAND as project_list
        args = self._parse_args(argv)
    
        tar_ctrl = Target.controller(PROJECT_STORAGE)
        app_ctrl = Application.controller(PROJECT_STORAGE)
        meas_ctrl = Measurement.controller(PROJECT_STORAGE)
        proj_ctrl = Project.controller()
    
        project_name = args.name
        project = proj_ctrl.one({'name': project_name})
        if not project:
            self.parser.error("'%s' is not a project name. Type `%s` to see valid names." % 
                              (project_name, project_list.command))
    
        updates = dict(project.element)
        updates['name'] = getattr(args, 'new_name', project_name)
        targets = set(project['targets'])
        applications = set(project['applications'])
        measurements = set(project['measurements'])
        
        added = self._parse_add_args(args, tar_ctrl, app_ctrl, meas_ctrl, targets, applications, measurements)
        removed = self._parse_remove_args(args, tar_ctrl, app_ctrl, meas_ctrl, targets, applications, measurements)
    
        updates['targets'] = list(targets)
        updates['applications'] = list(applications)
        updates['measurements'] = list(measurements)
        
        try:
            force_tau_options = args.force_tau_options
        except AttributeError:
            pass
        else:
            # Unset force_tau_options if it was already set and --force-taucmdr-options=none 
            if updates.pop('force_tau_options', False) and [i.lower().strip() for i in force_tau_options] == ['none']:
                proj_ctrl.unset(['force_tau_options'], {'name': project_name})
                self.logger.info("Removed 'force-taucmdr-options' from project configuration '%s'.", project_name)
            else:
                updates['force_tau_options'] = force_tau_options
                self.logger.info("Added 'force-taucmdr-options' to project configuration '%s'.", project_name)

        proj_ctrl.update(updates, {'name': project_name})
        for model in added:
            self.logger.info("Added %s '%s' to project configuration '%s'.", 
                             model.name.lower(), model[model.key_attribute], project_name)
        for model in removed:
            self.logger.info("Removed %s '%s' from project configuration '%s'.", 
                             model.name.lower(), model[model.key_attribute], project_name)
        return EXIT_SUCCESS

COMMAND = ProjectEditCommand(Project, __name__)
