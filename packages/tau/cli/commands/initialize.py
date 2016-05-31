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
from tau import util
from tau import EXIT_SUCCESS, EXIT_WARNING
from tau.error import InternalError, ConfigurationError
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.model.project import Project, ProjectSelectionError
from tau.storage.project import ProjectStorageError
from tau.storage.levels import PROJECT_STORAGE, STORAGE_LEVELS
from tau.cli.arguments import ParseBooleanAction
from tau.cli.commands.target.create import COMMAND as target_create_cmd
from tau.cli.commands.application.create import COMMAND as application_create_cmd
from tau.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from tau.cli.commands.project.create import COMMAND as project_create_cmd
from tau.cli.commands.select import COMMAND as select_cmd
from tau.cli.commands.dashboard import COMMAND as dashboard_cmd
from tau.cf.target import host, DARWIN_OS


class InitializeCommand(AbstractCommand):
    """``tau initialize`` subcommand."""

    def construct_parser(self):

        def _default_target_name():
            node_name = platform.node()
            if not node_name:
                return 'default_target'
            return node_name.split('.')[0]

        usage = "%s [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--bare',
                            help="Initialize project storage but don't configure anything",
                            nargs='?',
                            const=True,
                            default=False,
                            metavar='T/F',
                            action=ParseBooleanAction)

        default_project_name = os.path.basename(os.getcwd()) or 'default_project'
        project_group = parser.add_argument_group('project arguments')
        project_group.add_argument('--project-name',
                                   help="Name of the new project",
                                   metavar='<name>',
                                   default=default_project_name)
        project_group.add_argument('--storage-level',
                                   help='location of installation directory',
                                   choices=STORAGE_LEVELS.keys(),
                                   metavar='<levels>', default=arguments.SUPPRESS)

        parser.merge(target_create_cmd.parser, group_title='target arguments', include_positional=False)
        target_group = parser.add_argument_group('target arguments')
        target_group.add_argument('--target-name',
                                  help="Name of the new target configuration",
                                  metavar='<name>',
                                  default=_default_target_name())

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

    def _create_project(self, argv, args):
        def _safe_execute(cmd, argv):
            retval = cmd.main(argv)
            if retval != EXIT_SUCCESS:
                raise InternalError("return code %s: %s %s" % (retval, cmd, ' '.join(argv)))

        if host.operating_system() is DARWIN_OS:
            self.logger.info("Darwin OS detected: disabling PAPI, binutils, "
                             "compiler-based instrumentation, and sampling.")
            papi = False
            binutils = False
            sample = False
            comp_inst = 'never'
        else:
            papi = True
            binutils = True
            sample = True
            comp_inst = 'fallback'

        project_name = args.project_name
        target_name = args.target_name
        application_name = args.application_name
        if hasattr(args, 'storage_level'):
            project_create_cmd.main([project_name, '--storage-level', args.storage_level])
        else:
            project_create_cmd.main([project_name])

        select_cmd.main(['--project', project_name])

        target_argv = [target_name] + argv
        _, unknown = target_create_cmd.parser.parse_known_args(args=target_argv)
        target_argv = [target_name] + [arg for arg in argv if arg not in unknown]
        if not binutils:
            target_argv.append('--binutils=False')
        if not papi:
            target_argv.append('--papi=False')
        _safe_execute(target_create_cmd, target_argv)

        application_argv = [application_name] + argv
        application_args, unknown = application_create_cmd.parser.parse_known_args(args=application_argv)
        application_argv = [application_name] + [arg for arg in argv if arg not in unknown]
        _safe_execute(application_create_cmd, application_argv)

        measurement_names = []
        measurement_args = ['--%s=True' % attr 
                            for attr in 'cuda', 'mpi', 'opencl' if getattr(application_args, attr, False)]

        if args.sample and sample:
            _safe_execute(measurement_create_cmd, 
                          ['sample', '--profile=True', '--trace=False', '--sample=True',
                           '--source-inst=never', '--compiler-inst=never',
                           '--link-only=False'] + measurement_args)
            measurement_names.extend(['sample'])
        if args.profile:
            _safe_execute(measurement_create_cmd, 
                          ['instrument', '--profile=True', '--trace=False', '--sample=False',
                           '--source-inst=automatic', '--compiler-inst=%s' % comp_inst, 
                           '--link-only=False'] + measurement_args)
            measurement_names.append('instrument')
        if args.trace:
            _safe_execute(measurement_create_cmd, 
                          ['trace', '--profile=False', '--trace=True', '--sample=False', 
                           '--source-inst=automatic', '--compiler-inst=%s' % comp_inst, 
                           '--link-only=False'] + measurement_args)
            measurement_names.append('trace')

        select_cmd.main(['--project', project_name, '--target', target_name, 
                         '--application', application_name, '--measurement', measurement_names[0]])

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        if not (args.profile or args.trace or args.sample):
            self.parser.error('You must specify at least one measurement.')

        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except ProjectStorageError:
            self.logger.debug("No project found, initializing a new project.")
            PROJECT_STORAGE.connect_filesystem()
            if not args.bare:
                try:
                    self._create_project(argv, args)
                except ConfigurationError:
                    PROJECT_STORAGE.disconnect_filesystem()
                    util.rmtree(proj_ctrl.storage.prefix, ignore_errors=True)
                    raise
            return dashboard_cmd.main([])
        except ProjectSelectionError as err:
            err.value = "The project has been initialized but no project configuration is selected."
            raise err
        else:
            self.logger.warning("Tau is already initialized and the selected project is '%s'. Use commands like"
                                " `tau application edit` to edit the selected project or delete"
                                " '%s' to reset to a fresh environment.", proj['name'], proj_ctrl.storage.prefix)
            return EXIT_WARNING

COMMAND = InitializeCommand(__name__, summary_fmt="Initialize TAU Commander.")
