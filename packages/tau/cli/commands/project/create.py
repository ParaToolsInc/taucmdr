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
from tau.cli import arguments
from tau.core import storage
from tau.core.mvc import UniqueAttributeError
from tau.core.target import Target
from tau.core.application import Application
from tau.core.measurement import Measurement
from tau.core.project import Project
from tau.cli.cli_view import CreateCommand


class ProjectCreateCommand(CreateCommand):
    """``tau project create`` subcommand."""
    
    def construct_parser(self):
        usage = "%s <project_name> [targets] [applications] [measurements] [arguments]" % self.command
        parser = arguments.get_parser_from_model(self.controller, 
                                                 prog=self.command, 
                                                 usage=usage, 
                                                 description=self.summary)
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
                            default=arguments.SUPPRESS)
        parser.add_argument('--applications',
                            help="Application configurations in this project",
                            metavar='a',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--measurements',
                            help="Measurement configurations in this project",
                            metavar='m',
                            nargs='+',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
    
        store = storage.PROJECT_STORAGE
        tar_ctl = Target(store)
        app_ctl = Application(store)
        mes_ctl = Measurement(store)
        
        targets = set()
        applications = set()
        measurements = set()
        for attr, model, dest in [('targets', Target, targets),
                                  ('applications', Application, applications),
                                  ('measurements', Measurement, measurements)]:
            # pylint: disable=no-member
            for name in getattr(args, attr, []):
                found = model.with_name(name)
                if not found:
                    self.parser.error("There is no %s named '%s'" % (model.model_name, name))
                dest.add(found.eid)

            for name in getattr(args, 'impl_' + attr, []):
                tar = tar_ctl.with_name(name)
                app = app_ctl.with_name(name)
                mes = mes_ctl.with_name(name)
                tam = set([tar, app, mes]) - set([None])
                if len(tam) > 1:
                    self.parser.error("'%s' is ambiguous, please use --targets, --applications,"
                                      " or --measurements to specify configuration type" % name)
                elif len(tam) == 0:
                    self.parser.error("'%s' is not a target, application, or measurement" % name)
                elif tar:
                    targets.add(tar.eid)
                elif app:
                    applications.add(app.eid)
                elif mes:
                    measurements.add(mes.eid)
    
            try:
                delattr(args, 'impl_' + attr)
            except AttributeError:
                pass
    
        args.targets = list(targets)
        args.applications = list(applications)
        args.measurements = list(measurements)
    
        ctrl = self.controller(store)
        data = {attr: getattr(args, attr) for attr in ctrl.attributes if hasattr(args, attr)}
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A %s named '%s' already exists" % (self.model_name, args.name))
        self.logger.info("Created a new %s named '%s'.", self.model_name, args.name)
        return EXIT_SUCCESS

COMMAND = ProjectCreateCommand(Project, __name__)
