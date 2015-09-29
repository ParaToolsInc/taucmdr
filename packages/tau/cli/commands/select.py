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

from tau import EXIT_SUCCESS, TAU_SCRIPT
from tau.cli import arguments
from tau.error import InternalError, ConfigurationError
from tau.core.storage import PROJECT_STORAGE
from tau.core.project import Project
from tau.core.target import Target
from tau.core.application import Application
from tau.core.measurement import Measurement
from tau.core.experiment import Experiment
from tau.cli.command import AbstractCommand


class SelectCommand(AbstractCommand):
    """``tau select`` subcommand."""

    def _parse_implicit(self, args, targets, applications, measurements):
        targ_ctrl = Target(PROJECT_STORAGE)
        app_ctrl = Application(PROJECT_STORAGE)
        meas_ctrl = Measurement(PROJECT_STORAGE)
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

    def _parse_explicit(self, args, controller_cls, acc):
        ctrl = controller_cls(PROJECT_STORAGE)
        model_name = ctrl.model_name.lower()
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
            acc = set(ctrl.all())
        if not acc:
            raise ConfigurationError("There are no %s configurations.",
                                     "Use `%s %s create` to create a new one" % TAU_SCRIPT, model_name)
        if len(acc) > 1:
            names = ', '.join([m['name'] for m in list(acc)])
            self.parser.error('Multiple %ss given (%s). Please specify exactly one.' % (model_name, names))
        elif len(acc) == 1:
            return list(acc)[0]

    def construct_parser(self):
        usage = "%s [target] [application] [measurement] [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('impl_target',
                            help="Target configuration to select",
                            metavar='[target]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_application',
                            help="Application configuration to select",
                            metavar='[application]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_measurement',
                            help="Measurement configuration to select",
                            metavar='[measurements]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('--target',
                            help="Target configuration to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--application',
                            help="Application configuration to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        parser.add_argument('--measurement',
                            help="Measurement configuration to select",
                            metavar='<name>',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        targets = set()
        applications = set()
        measurements = set()
        self._parse_implicit(args, targets, applications, measurements)
        targ = self._parse_explicit(args, Target, targets)
        app = self._parse_explicit(args, Application, applications)
        meas = self._parse_explicit(args, Measurement, measurements)
        for lhs in [targ, app, meas]:
            for rhs in [targ, app, meas]:
                lhs.check_compatibility(rhs)

        project = Project.get_project()
        expr_ctrl = Experiment(PROJECT_STORAGE)
        data = {'project': project.eid, 'target': targ.eid, 'application': app.eid, 'measurement': meas.eid}
        matching = expr_ctrl.search(data)
        if not matching:
            self.logger.debug('Creating new experiment')
            found = expr_ctrl.create(data)
        elif len(matching) > 1:
            raise InternalError('More than one experiment with data %r exists!' % data)
        else:
            self.logger.debug('Using existing experiment')
            found = matching[0]
    
        populated = found.populate()
        self.logger.debug("'%s' on '%s' measured by '%s'",
                          populated['application']['name'],
                          populated['target']['name'],
                          populated['measurement']['name'])
        found.select()

        return EXIT_SUCCESS


COMMAND = SelectCommand(__name__, summary_fmt="Select project components for the next experiment.")
