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
"""``select`` subcommand."""

from __future__ import absolute_import
from taucmdr import EXIT_SUCCESS
from taucmdr.error import ExperimentSelectionError
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.project import Project
from taucmdr.model.target import Target
from taucmdr.model.application import Application
from taucmdr.model.measurement import Measurement
from taucmdr.model.experiment import Experiment


class SelectCommand(AbstractCommand):
    """``select`` subcommand."""

    def _construct_parser(self):
        usage = "%s [experiment] [target] [application] [measurement]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
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
        parser.add_argument('impl_experiment',
                            help="Experiment configuration name",
                            metavar='experiment',
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
        parser.add_argument('--experiment',
                            help="Experiment configuration name",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        return parser

    def _parse_implicit(self, args):
        targets = set()
        applications = set()
        measurements = set()
        experiments = set()
        targ_ctrl = Target.controller(PROJECT_STORAGE)
        app_ctrl = Application.controller(PROJECT_STORAGE)
        meas_ctrl = Measurement.controller(PROJECT_STORAGE)
        expr_ctrl = Experiment.controller(PROJECT_STORAGE)
        for flag in 'impl_experiment', 'impl_project', 'impl_target', 'impl_application', 'impl_measurement':
            for name in getattr(args, flag, []):
                tar = targ_ctrl.one({"name": name})
                app = app_ctrl.one({"name": name})
                mes = meas_ctrl.one({"name": name})
                expr = expr_ctrl.one({"name": name})
                found = {tar, app, mes, expr} - {None}
                if len(found) > 1:
                    self.parser.error("'%s' is ambiguous. "
                                      "Please use a command line flag to specify configuration type." % name)
                elif len(found) == 0:
                    self.parser.error("'%s' is not an experiment, target, application, or measurement." % name)
                elif tar:
                    targets.add(tar)
                elif app:
                    applications.add(app)
                elif mes:
                    measurements.add(mes)
                elif expr:
                    experiments.add(expr)
        return targets, applications, measurements, experiments

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

    def _parse_explicit_experiment(self, args, acc):
        model_name = 'experiment'
        if hasattr(args, model_name):
            name = getattr(args, model_name)
            ctrl = Experiment.controller(PROJECT_STORAGE)
            found = ctrl.one({"name": name})
            if not found:
                self.parser.error('There is no %s named %s.' % (model_name, name))
            else:
                acc.add(found)
        if len(acc) == 1:
            return acc.pop()
        return None

    def main(self, argv):
        if not argv:
            self.parser.error("too few arguments.")
        args = self._parse_args(argv)
        proj = Project.selected()
        targ, app, meas, expr = self._parse_implicit(args)
        expr = self._parse_explicit_experiment(args, expr)
        if expr:
            targ, app, meas = None, None, None
            name = expr['name']
        else:
            targ = self._parse_explicit(args, Target, targ, proj, 'targets')
            app = self._parse_explicit(args, Application, app, proj, 'applications')
            meas = self._parse_explicit(args, Measurement, meas, proj, 'measurements')
            name = getattr(args, 'name', "%s-%s-%s" % (targ['name'], app['name'], meas['name']))
        try:
            Experiment.select(name)
        except ExperimentSelectionError:
            args = [name,
                    '--target', targ['name'],
                    '--application', app['name'],
                    '--measurement', meas['name']]
            retval = experiment_create_cmd.main(args)
            if retval != EXIT_SUCCESS:
                return retval
            Experiment.select(name)
        self.logger.info("Selected experiment '%s'.", name)
        rebuild_required = Experiment.rebuild_required()
        if rebuild_required:
            self.logger.info(rebuild_required)
        return EXIT_SUCCESS


COMMAND = SelectCommand(__name__, summary_fmt="Create a new experiment or select an existing experiment.")
