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

import os
from tau import EXIT_SUCCESS, TAU_SCRIPT
from tau.cli import arguments
from tau.error import ConfigurationError, InternalError
from tau.storage.levels import PROJECT_STORAGE
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.model.experiment import Experiment
from tau.cli.command import AbstractCommand


class SelectCommand(AbstractCommand):
    """``tau select`` subcommand."""

    def _parse_implicit(self, args, targets, applications, measurements):
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
                                      " or --measurement to specify configuration type" % name)
                elif len(tam) == 0:
                    self.parser.error("'%s' is not a target, application, or measurement" % name)
                elif tar:
                    targets.add(tar)
                elif app:
                    applications.add(app)
                elif mes:
                    measurements.add(mes)

    def _parse_explicit(self, args, model, acc, proj, attr):
        ctrl = model.controller(PROJECT_STORAGE)
        model_name = model.name.lower()
        try:
            name = getattr(args, model_name)
        except AttributeError:
            pass
        else:
            found = ctrl.one({"name": name})
            if not found:
                self.parser.error('There is no %s named %s.' % (model_name, name))
            else:
                acc.add(found)
        if not acc:
            acc = set(proj.populate(attr))
        if not acc:
            err_fmt = "There are no %s configurations in project '%s'.  Use `%s %s create` to create a new one."
            err_msg = err_fmt % (model_name, proj['name'], os.path.basename(TAU_SCRIPT), model_name)
            raise ConfigurationError(err_msg)
        if len(acc) > 1:
            self.parser.error("Project '%s' has multiple %ss. Please specify which to use." % 
                              (proj['name'], model_name))
        elif len(acc) == 1:
            return list(acc)[0]

    def _check_compatibility(self, proj, targ, app, meas):
        from tau.cli.commands.project.edit import COMMAND as project_edit
        for model in targ, app, meas:
            if proj.eid not in model['projects']:
                raise ConfigurationError("%s '%s' is not a member of project '%s'.  See `%s --help`." %
                                         (model.name, model['name'], proj['name'], project_edit.command))
        for lhs in [targ, app, meas]:
            for rhs in [targ, app, meas]:
                lhs.check_compatibility(rhs)

    def construct_parser(self):
        usage = "%s [target] [application] [measurement] [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('impl_target',
                            help="Target to select",
                            metavar='[target]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_application',
                            help="Application to select",
                            metavar='[application]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_measurement',
                            help="Measurement to select",
                            metavar='[measurements]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('--target',
                            help="Target to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--application',
                            help="Application to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--measurement',
                            help="Measurement to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)        
        targets = set()
        applications = set()
        measurements = set()
        
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        if not proj:
            self.parser.error("No project is currently selected.  Please specify a project name.")

        self._parse_implicit(args, targets, applications, measurements)
        targ = self._parse_explicit(args, Target, targets, proj, 'targets')
        app = self._parse_explicit(args, Application, applications, proj, 'applications')
        meas = self._parse_explicit(args, Measurement, measurements, proj, 'measurements')
        self._check_compatibility(proj, targ, app, meas)
        
        expr_ctrl = Experiment.controller(PROJECT_STORAGE)
        data = {'project': proj.eid, 'target': targ.eid, 'application': app.eid, 'measurement': meas.eid}
        matching = expr_ctrl.search(data)
        if not matching:
            self.logger.info('Creating new experiment')
            expr = expr_ctrl.create(data)
        elif len(matching) > 1:
            raise InternalError('More than one experiment with data %r exists!' % data)
        else:
            self.logger.debug('Reusing existing experiment')
            expr = matching[0]

        proj_ctrl.select(proj, expr)
        populated = expr.populate()
        self.logger.debug("Selected project '%s': '%s' on '%s' measured by '%s'",
                          proj['name'],
                          populated['application']['name'],
                          populated['target']['name'],
                          populated['measurement']['name'])
        return EXIT_SUCCESS


COMMAND = SelectCommand(__name__, summary_fmt="Select project components for the next experiment.")
