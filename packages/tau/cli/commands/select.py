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
"""``tau select`` subcommand."""

from tau import EXIT_SUCCESS
from tau.cli import arguments
from tau.error import ConfigurationError, InternalError
from tau.storage.levels import PROJECT_STORAGE
from tau.model.project import Project, ProjectSelectionError, ExperimentSelectionError
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.model.experiment import Experiment
from tau.cli.command import AbstractCommand


class SelectCommand(AbstractCommand):
    """``tau select`` subcommand."""

    def _parse_implicit(self, args):
        projects = set()
        targets = set()
        applications = set()
        measurements = set()
        proj_ctrl = Project.controller()
        targ_ctrl = Target.controller(PROJECT_STORAGE)
        app_ctrl = Application.controller(PROJECT_STORAGE)
        meas_ctrl = Measurement.controller(PROJECT_STORAGE)
        for flag in 'impl_project', 'impl_target', 'impl_application', 'impl_measurement':
            for name in getattr(args, flag, []):
                prj = proj_ctrl.one({"name": name})
                tar = targ_ctrl.one({"name": name})
                app = app_ctrl.one({"name": name})
                mes = meas_ctrl.one({"name": name})
                ptam = set([prj, tar, app, mes]) - set([None])
                if len(ptam) > 1:
                    self.parser.error("'%s' is ambiguous.  Please use --project, --target, --application,"
                                      " or --measurement to specify configuration type." % name)
                elif len(ptam) == 0:
                    self.parser.error("'%s' is not a project, target, application, or measurement." % name)
                elif prj:
                    projects.add(prj)
                elif tar:
                    targets.add(tar)
                elif app:
                    applications.add(app)
                elif mes:
                    measurements.add(mes)
        return projects, targets, applications, measurements

    def _parse_explicit_project(self, args, acc):
        proj_ctrl = Project.controller()
        try:
            name = getattr(args, 'project')
        except AttributeError:
            pass
        else:
            found = proj_ctrl.one({"name": name})
            if not found:
                self.parser.error("There is no project configuration named '%s.'" % name)
            else:
                acc.add(found)
        if len(acc) == 0:
            try:
                return proj_ctrl.selected()
            except ProjectSelectionError:
                self.parser.error("No project configuration selected.  Please use --project to specify one.")
        elif len(acc) > 1:
            self.parser.error("Multiple project configurations specified: %s.  Please specify at most one." % 
                              ', '.join(acc))
        elif len(acc) == 1:
            return acc.pop()

    def _parse_explicit(self, args, model, acc, proj, attr):
        model_name = model.name.lower()
        try:
            name = getattr(args, model_name)
        except AttributeError:
            pass
        else:
            ctrl = model.controller(PROJECT_STORAGE)
            found = ctrl.one({"name": name})
            if not found:
                self.parser.error('There is no %s named %s.' % (model_name, name))
            else:
                acc.add(found)
        if not acc:
            acc = set(proj.populate(attr))
        if not acc:
            return None
        if len(acc) > 1:
            self.parser.error("Project '%s' has multiple %ss. Please specify which to use." % 
                              (proj['name'], model_name))
        elif len(acc) == 1:
            return acc.pop()

    def _check_compatibility(self, proj, targ, app, meas):
        from tau.cli.commands.project.edit import COMMAND as project_edit
        for model in targ, app, meas:
            if proj.eid not in model['projects']:
                raise ConfigurationError("%s '%s' is not a member of project configuration '%s'." % 
                                         (model.name, model['name'], proj['name']), 
                                         "Use `%s %s --add-%s %s` to add it to the project configuration." % 
                                         (project_edit.command, proj['name'], model.name.lower(), model['name']))
        for lhs in [targ, app, meas]:
            for rhs in [targ, app, meas]:
                lhs.check_compatibility(rhs)

    def construct_parser(self):
        usage = "%s [project] [target] [application] [measurement] [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('impl_project',
                            help="Project configuration name",
                            metavar='[project]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_target',
                            help="Target configuration name",
                            metavar='[target]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_application',
                            help="Application configuration name",
                            metavar='[application]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_measurement',
                            help="Measurement configuration name",
                            metavar='[measurement]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('--project',
                            help="Project configuration name",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--target',
                            help="Target configuration name",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--application',
                            help="Application configuration name",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--measurement',
                            help="Measurement configuration name",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        proj, targ, app, meas = self._parse_implicit(args)
        proj = self._parse_explicit_project(args, proj)
        targ = self._parse_explicit(args, Target, targ, proj, 'targets')
        app = self._parse_explicit(args, Application, app, proj, 'applications')
        meas = self._parse_explicit(args, Measurement, meas, proj, 'measurements')

        proj_ctrl = Project.controller()
        rebuild_required = False
        try:
            meas_old = proj_ctrl.selected().experiment().populate('measurement')
        except (ProjectSelectionError, ExperimentSelectionError):
            pass
        else:
            new_attrs = set(meas.keys())
            old_attrs = set(meas_old.keys())
            parts = ["Application rebuild required:"]
            for attr in (new_attrs - old_attrs):
                if Measurement.attributes[attr]['application_rebuild']:
                    parts.append("%s in measurement is now '%s'." % (attr, meas[attr]))
                    rebuild_required = True
                    break
            for attr in (old_attrs - new_attrs):
                if Measurement.attributes[attr]['application_rebuild']:
                    parts.append("%s in measurement is now unset." % attr)
                    rebuild_required = True
                    break
            for attr in (new_attrs & old_attrs):
                if meas[attr] != meas_old[attr] and Measurement.attributes[attr]['application_rebuild']:
                    parts.append("%s in measurement changed from '%s' to '%s'." % (attr, meas_old[attr], meas[attr]))
                    rebuild_required = True
                    break
            parts.append("Please rebuild your application.")
            msg = '\n    '.join(parts)

        if not (targ and app and meas):
            proj_ctrl.select(proj)
            self.logger.info("Selected project '%s'. No experiment.", proj['name'])
        else:
            self._check_compatibility(proj, targ, app, meas)
            expr_ctrl = Experiment.controller()
            data = {'project': proj.eid, 'target': targ.eid, 'application': app.eid, 'measurement': meas.eid}
            matching = expr_ctrl.search(data)
            if not matching:
                self.logger.debug('Creating new experiment')
                expr = expr_ctrl.create(data)
            elif len(matching) > 1:
                raise InternalError('More than one experiment with data %r exists!' % data)
            else:
                self.logger.debug('Reusing existing experiment')
                expr = matching[0]
            proj_ctrl.select(proj, expr)
            populated = expr.populate()
            self.logger.info("Selected project '%s' with experiment (%s, %s, %s).",
                             proj['name'],
                             populated['target']['name'],
                             populated['application']['name'],
                             populated['measurement']['name'])

            if rebuild_required:
                self.logger.info(msg)
        return EXIT_SUCCESS


COMMAND = SelectCommand(__name__, 
                        summary_fmt=("Select project components for the next experiment.\n"
                                     "Available components may be viewed via the `dashboard` subcommand."))
