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
"""``tau initialize`` subcommand."""

import os
import platform
from tau import EXIT_SUCCESS
from tau import cli
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.model.project import Project
from tau.storage.project import UninitializedProjectError
from tau.storage.levels import PROJECT_STORAGE
from tau.cli.arguments import ParseBooleanAction
from tau.cli.commands.target.create import COMMAND as target_create_cmd
from tau.cli.commands.application.create import COMMAND as application_create_cmd
from tau.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from tau.cli.commands.project.create import COMMAND as project_create_cmd

class InitializeCommand(AbstractCommand):
    """``tau initialize`` subcommand."""
    
    def construct_parser(self):
        usage = "%s [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        
        default_project_name = os.path.basename(os.getcwd()) or 'default_project'
        project_group = parser.add_argument_group('project arguments')
        project_group.add_argument('--project-name',
                                   help="Name of the new project",
                                   metavar='<name>',
                                   default=default_project_name)
        
        parser.merge(target_create_cmd.parser, group_title='target arguments', include_positional=False)
        default_target_name = platform.node() or 'default_target'
        target_group = parser.add_argument_group('target arguments')
        target_group.add_argument('--target-name',
                                  help="Name of the new target configuration",
                                  metavar='<name>',
                                  default=default_target_name)

        parser.merge(application_create_cmd.parser, group_title='application arguments', include_positional=False)
        default_application_name = os.path.basename(os.getcwd()) or 'default_application'
        application_group = parser.add_argument_group('application arguments')
        application_group.add_argument('--application-name',
                                       help="Name of the new application configuration",
                                       metavar='<name>',
                                       default=default_application_name)

        measurement_group = parser.add_argument_group('measurement arguments')
        measurement_group.add_argument('--profile',
                                       help="Create measurement configurations for profiling",
                                       metavar='T/F',
                                       nargs='?',
                                       const=True,
                                       default=True,
                                       action=ParseBooleanAction)
        measurement_group.add_argument('--trace',
                                       help="Create measurement configurations for tracing",
                                       metavar='T/F',
                                       nargs='?',
                                       const=True,
                                       default=True,
                                       action=ParseBooleanAction)
        measurement_group.add_argument('--sample',
                                       help="Create measurement configurations for event-based sampling",
                                       metavar='T/F',
                                       nargs='?',
                                       const=True,
                                       default=True,
                                       action=ParseBooleanAction)
        return parser

    def _initialize_target(self, target_name, argv):
        target_argv = [target_name] + argv
        _, unknown = target_create_cmd.parser.parse_known_args(args=target_argv)
        return target_create_cmd.main([arg for arg in target_argv if arg not in unknown])           

    def _initialize_application(self, application_name, argv):
        application_argv = [application_name] + argv
        _, unknown = application_create_cmd.parser.parse_known_args(args=application_argv)
        return application_create_cmd.main([arg for arg in application_argv if arg not in unknown])
        
    def _initialize_measurements(self, args):
        main = measurement_create_cmd.main
        measurement_names = []
        if args.sample:
            retval = main(['profile-sample', '--profile=True', '--trace=False', '--sample=True',
                           '--source-inst=never', '--compiler-inst=never', '--link-only=False'])
            if retval != EXIT_SUCCESS:
                return retval
            measurement_names.extend(['profile-sample'])
        if args.profile:
            retval = main(['profile-automatic', '--profile=True', '--trace=False', '--sample=False',
                           '--source-inst=automatic', '--compiler-inst=fallback', '--link-only=False'])
            if retval != EXIT_SUCCESS:
                return retval
            retval = main(['profile-manual', '--profile=True',  '--trace=False', '--sample=False',
                           '--source-inst=never', '--compiler-inst=never', '--link-only=True'])
            if retval != EXIT_SUCCESS:
                return retval
            measurement_names.extend(['profile-automatic', 'profile-manual'])
        if args.trace:
            retval = main(['trace-automatic', '--profile=False', '--trace=True', 
                           '--source-inst=automatic', '--compiler-inst=fallback'])
            if retval != EXIT_SUCCESS:
                return retval
            retval = main(['trace-manual', '--profile=False',  '--trace=True',
                           '--source-inst=never', '--compiler-inst=never', '--link-only=True'])
            if retval != EXIT_SUCCESS:
                return retval
            measurement_names.extend(['trace-automatic', 'trace-manual'])
        return measurement_names
    
    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        if not (args.profile or args.trace or args.sample):
            self.parser.error('You must specify at least one measurement.')
        
        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except UninitializedProjectError:
            self.logger.debug("No project found, initializing a new project.")
            PROJECT_STORAGE.connect_filesystem()
            project_name = args.project_name
            target_name = args.target_name
            application_name = args.application_name
            measurement_names = self._initialize_measurements(args)
            self._initialize_target(target_name, argv)
            self._initialize_application(application_name, argv)
            project_create_cmd.main([project_name, target_name, application_name] + measurement_names)
            cli.execute_command(['select'], [project_name, measurement_names[0]])
            cli.execute_command(['dashboard'])
        else:
            if proj:
                self.logger.info("Selected project: '%s'", proj['name'])
            else:
                from tau.cli.commands.select import COMMAND as select_command
                self.logger.info("No project selected.  Try `%s`.", 
                                 select_command.command)
        return EXIT_SUCCESS

COMMAND = InitializeCommand(__name__, summary_fmt="Initialize TAU Commander.")
