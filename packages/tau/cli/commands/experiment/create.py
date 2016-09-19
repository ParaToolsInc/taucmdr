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
"""``tau experiment create`` subcommand."""

from tau import EXIT_SUCCESS
from tau.cli import arguments
from tau.error import UniqueAttributeError
from tau.cf.storage.levels import PROJECT_STORAGE
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.model.experiment import Experiment
from tau.cli.command import AbstractCommand


class ExperimentCreateCommand(AbstractCommand):
    """``tau experiment create`` subcommand."""

    def _parse_implicit(self, args):
        targets = set()
        applications = set()
        measurements = set()
        targ_ctrl = Target.controller(PROJECT_STORAGE)
        app_ctrl = Application.controller(PROJECT_STORAGE)
        meas_ctrl = Measurement.controller(PROJECT_STORAGE)
        for flag in 'impl_target', 'impl_application', 'impl_measurement':
            for name in getattr(args, flag, []):
                tar = targ_ctrl.one({"name": name})
                app = app_ctrl.one({"name": name})
                mes = meas_ctrl.one({"name": name})
                tam = set([tar, app, mes]) - set([None])
                if len(tam) > 1:
                    self.parser.error("'%s' is ambiguous.  Please use --target, --application,"
                                      " or --measurement to specify configuration type." % name)
                elif len(tam) == 0:
                    self.parser.error("'%s' is not a target, application, or measurement." % name)
                elif tar:
                    targets.add(tar)
                elif app:
                    applications.add(app)
                elif mes:
                    measurements.add(mes)
        return targets, applications, measurements

    def _parse_explicit(self, args, model, acc, proj, attr):
        model_name = model.name.lower()
        if hasattr(args, model_name):
            name = getattr(args, model_name)
            ctrl = model.controller(PROJECT_STORAGE)
            found = ctrl.one({"name": name})
            if not found:
                self.parser.error('There is no %s named %s.' % (model_name, name))
            else:
                acc.add(found)
        if not acc:
            acc = set(proj.populate(attr))
        if not acc:
            self.parser.error("Project '%s' has no %ss." % (proj['name'], model_name))
        if len(acc) > 1:
            self.parser.error("Project '%s' has multiple %ss. Please specify which to use." % 
                              (proj['name'], model_name))
        elif len(acc) == 1:
            return acc.pop()

    def _construct_parser(self):
        usage = "%s [target] [application] [measurement] [arguments]" % self.command
        parser = arguments.get_parser_from_model(Experiment, prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('impl_target',
                            help="Target configuration name",
                            metavar='target',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_application',
                            help="Application configuration name",
                            metavar='application',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_measurement',
                            help="Measurement configuration name",
                            metavar='measurement',
                            nargs='*',
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

    def _parse_models_from_args(self, argv):
        if not argv:
            self.parser.error("At least one target, application, or measurement must be specified.")
        args = self._parse_args(argv)
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        targ, app, meas = self._parse_implicit(args)
        targ = self._parse_explicit(args, Target, targ, proj, 'targets')
        app = self._parse_explicit(args, Application, app, proj, 'applications')
        meas = self._parse_explicit(args, Measurement, meas, proj, 'measurements')
        name = getattr(args, 'name', "%s-%s-%s" % (targ['name'], app['name'], meas['name']))
        return proj, targ, app, meas, name
    
    def main(self, argv):
        proj, targ, app, meas, name = self._parse_models_from_args(argv)
        expr_ctrl = Experiment.controller()
        data = {'name': name}
        matching = expr_ctrl.search(data)
        if matching:
            raise UniqueAttributeError(Experiment, "name="+name)
        self.logger.debug('Creating new experiment')
        data.update({'project': proj.eid, 'target': targ.eid, 'application': app.eid, 'measurement': meas.eid})
        expr_ctrl.create(data)
        self.logger.info("Created a new experiment named '%s'.", name)
        return EXIT_SUCCESS


COMMAND = ExperimentCreateCommand(__name__, 
                                  summary_fmt=("Create a new experiment from project components.\n"
                                               "Available components may be viewed via the `dashboard` subcommand."))
