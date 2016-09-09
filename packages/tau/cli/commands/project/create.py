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
"""``tau project create`` subcommand."""

from tau import EXIT_SUCCESS
from tau.error import UniqueAttributeError
from tau.cli import arguments
from tau.cli.cli_view import CreateCommand
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.cf.storage.levels import PROJECT_STORAGE


class ProjectCreateCommand(CreateCommand):
    """``tau project create`` subcommand."""
    
    def _parse_implicit(self, args, targets, applications, measurements):
        targ_ctrl = Target.controller(PROJECT_STORAGE)
        app_ctrl = Application.controller(PROJECT_STORAGE)
        meas_ctrl = Measurement.controller(PROJECT_STORAGE)
        for flag in 'impl_targets', 'impl_applications', 'impl_measurements':
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

    def _parse_explicit(self, args, model, acc):
        ctrl = model.controller(PROJECT_STORAGE)
        model_name = model.name.lower()
        try:
            names = getattr(args, model_name)
        except AttributeError:
            pass
        else:
            for name in names: 
                found = ctrl.one({"name": name})
                if not found:
                    self.parser.error('There is no %s named %s.' % (model_name, name))
                else:
                    acc.add(found)
    
    def construct_parser(self):
        usage = "%s <project_name> [targets] [applications] [measurements] [arguments]" % self.command
        parser = arguments.get_parser_from_model(self.model, prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('impl_targets',
                            help="Target configurations in this project",
                            metavar='[targets]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_applications',
                            help="Application configurations in this project",
                            metavar='[applications]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('impl_measurements',
                            help="Measurement configurations in this project",
                            metavar='[measurements]',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('--targets',
                            help="Target configurations in this project",
                            metavar='t',
                            nargs='+',
                            default=arguments.SUPPRESS,
                            dest='target')
        parser.add_argument('--applications',
                            help="Application configurations in this project",
                            metavar='a',
                            nargs='+',
                            default=arguments.SUPPRESS,
                            dest='application')
        parser.add_argument('--measurements',
                            help="Measurement configurations in this project",
                            metavar='m',
                            nargs='+',
                            default=arguments.SUPPRESS,
                            dest='measurement')
        return parser


    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
    
        targets = set()
        applications = set()
        measurements = set()
        self._parse_implicit(args, targets, applications, measurements)
        self._parse_explicit(args, Target, targets)
        self._parse_explicit(args, Application, applications)
        self._parse_explicit(args, Measurement, measurements)
    
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        data['targets'] = [model.eid for model in targets]
        data['applications'] = [model.eid for model in applications]
        data['measurements'] = [model.eid for model in measurements]
        try:
            self.model.controller().create(data)
        except UniqueAttributeError:
            self.parser.error("A project named '%s' already exists." % args.name)
    
        self.logger.info("Created a new project named '%s'.", args.name)
        return EXIT_SUCCESS

COMMAND = ProjectCreateCommand(Project, __name__)    
