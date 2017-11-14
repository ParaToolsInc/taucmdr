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
"""``initialize`` subcommand."""

import os
import platform
from taucmdr import util
from taucmdr import EXIT_SUCCESS, EXIT_WARNING
from taucmdr.error import InternalError, ConfigurationError, ProjectSelectionError
from taucmdr.model.project import Project
from taucmdr.model.target import Target
from taucmdr.model.application import Application
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cli.arguments import ParseBooleanAction, ArgumentsNamespace
from taucmdr.cli.commands.target.create import COMMAND as target_create_cmd
from taucmdr.cli.commands.application.create import COMMAND as application_create_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.project.create import COMMAND as project_create_cmd
from taucmdr.cli.commands.project.select import COMMAND as project_select_cmd
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.cli.commands.dashboard import COMMAND as dashboard_cmd
from taucmdr.cf.storage.project import ProjectStorageError
from taucmdr.cf.storage.levels import PROJECT_STORAGE, STORAGE_LEVELS

HELP_PAGE = """
TAU Commander Initialize:
============================================================================

To begin Initialize TAU Commander, enter: `tau initialize` or simply 
`tau init`.  
This first initialization will take quite a bit of time.  Not only is this 
command creating a project it is also downloading and building the 
TAU Performance System® and associated libraries that it depends on.  
Let this run and check for successful completion. When it completes it will 
display the tau dashboard (which can be viewed at anytime by entering: 
'tau dashboard').

Many parameters may be defined at initialization.  The full list of options is 
displayed below this help section.   It is easier to define options at 
initialization (eg. tau init --MPI T) than it is to edit application and 
measurement later.
___________________________________________________________________________

"""


class InitializeCommand(AbstractCommand):
    """``tau initialize`` subcommand."""
       
    def _construct_parser(self):
        usage = "%s [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--bare',
                            help="Initialize project but don't create target, application, or measurement objects",
                            nargs='?',
                            const=True,
                            default=False,
                            metavar='T/F',
                            action=ParseBooleanAction)
        project_group = parser.add_argument_group('project arguments')
        project_group.add_argument('--project-name',
                                   help="Name of the new project",
                                   metavar='<name>',
                                   default=(os.path.basename(os.getcwd()) or 'default_project'))
        project_group.add_argument('--storage-level',
                                   help='location of installation directory',
                                   choices=STORAGE_LEVELS.keys(),
                                   metavar='<levels>', default=arguments.SUPPRESS)
        target_group = parser.add_argument_group('target arguments')
        target_group.add_argument('--target-name',
                                  help="Name of the new target configuration",
                                  metavar='<name>',
                                  default=(platform.node() or 'default_target').split('.')[0])
        application_group = parser.add_argument_group('application arguments')
        application_group.add_argument('--application-name',
                                       help="Name of the new application configuration",
                                       metavar='<name>',
                                       default=(os.path.basename(os.getcwd()) or 'default_application'))
        
        # If an argument appears in both application and measurement (e.g. --mpi, --openmp, --cuda, etc.) 
        # then use the measurement form instead of the application form.
        excluded = []
        for action in measurement_create_cmd.parser.actions:
            excluded.extend(action.option_strings)
        
        parser.merge(target_create_cmd.parser)
        parser.merge(application_create_cmd.parser, exclude_arguments=excluded)
        parser.merge(measurement_create_cmd.parser)
        
        # OpenMP is a special case, see https://github.com/ParaToolsInc/taucmdr/issues/209
        for action in parser.actions:
            if action.dest == 'openmp':
                action.default = None
                action.const = 'ignore'
                break

        # Change defaults so that measurements are created unless explicitly disabled
        measurement_group = parser.add_argument_group('measurement arguments')
        measurement_group['--source-inst'].default = 'automatic'
        measurement_group['--compiler-inst'].default = 'fallback'
        measurement_group['--profile'].default = 'tau'
        measurement_group['--trace'].default = 'otf2'
        measurement_group['--sample'].default = True
        return parser

    def _create_project(self, args):
        project_name = args.project_name
        options = [project_name]
        try:
            project_create_cmd.main(options)
        except ConfigurationError:
            PROJECT_STORAGE.disconnect_filesystem()
            util.rmtree(PROJECT_STORAGE.prefix, ignore_errors=True)
            raise
        else:
            project_select_cmd.main([project_name])
            
    def _create_measurement(self, name, args, **kwargs):
        args = ArgumentsNamespace(**dict(vars(args), **kwargs))
        args.name = name
        self._safe_execute(measurement_create_cmd, args)
        return name

    def _safe_execute(self, cmd, argv):
        retval = cmd.main(argv)
        if retval != EXIT_SUCCESS:
            raise InternalError("return code %s: %s %s" % (retval, cmd, ' '.join(argv)))

    def _populate_project(self, args):
        # Create default application
        application_name = args.application_name
        cmd_args = Application.filter_arguments(args)
        cmd_args.name = application_name
        cmd_args.openmp = bool(args.openmp)
        if args.openmp is None:
            args.openmp = 'ignore'
        self._safe_execute(application_create_cmd, cmd_args)
        
        # Create default target
        target_name = args.target_name
        cmd_args = Target.filter_arguments(args)
        cmd_args.name = target_name
        self._safe_execute(target_create_cmd, cmd_args)

        # Target was created so let's see if we can use binutils on this target.
        targ = Target.controller(PROJECT_STORAGE).one({'name': target_name})
        if not targ['binutils_source']:
            self.logger.info("GNU binutils unavailable: disabling sampling and compiler-based instrumentation")
            args.sample = False
            args.compiler_inst = 'never'

        # Create default measurements
        measurements = []
        if args.profile != 'none':
            self._create_measurement(
                'baseline', args, baseline=True, profile='tau', trace='none', 
                sample=False, source_inst='never', compiler_inst='never',
                mpi=False, cuda=False, opencl=False, openmp='ignore', shmem=False)
            if args.sample:
                measurements.append(self._create_measurement(
                    'sample', args, profile=args.profile, trace='none',
                    sample=True, source_inst='never', compiler_inst='never'))
            if args.source_inst != 'never' or args.compiler_inst != 'never':
                measurements.append(self._create_measurement(
                    'profile', args, profile=args.profile, trace='none',
                    sample=False, source_inst=args.source_inst, compiler_inst=args.compiler_inst))
            if args.source_inst != 'never':
                measurements.append(self._create_measurement(
                    'source-inst', args, profile=args.profile, trace='none',
                    sample=False, source_inst=args.source_inst, compiler_inst='never'))
            if args.compiler_inst != 'never':
                measurements.append(self._create_measurement(
                    'compiler-inst', args, profile=args.profile, trace='none',
                    sample=False, source_inst='never', compiler_inst='always'))
        if args.trace != 'none':
            if args.source_inst != 'never' or args.compiler_inst != 'never':
                measurements.append(self._create_measurement(
                    'trace', args, profile='none', trace=args.trace, callpath=0,
                    sample=False, source_inst=args.source_inst, compiler_inst=args.compiler_inst))
        try:
            measurement_name = measurements[0]
        except IndexError:
            measurement_name = 'baseline'
        
        # Create default experiment
        select_cmd.main(['--target', target_name, 
                         '--application', application_name, 
                         '--measurement', measurement_name])

    def main(self, argv):
        args = self._parse_args(argv)
        if not (args.baseline or args.profile or args.trace or args.sample):
            self.parser.error('You must specify at least one measurement.')

        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except ProjectStorageError:
            self.logger.debug("No project found, initializing a new project.")
            PROJECT_STORAGE.connect_filesystem()
            try:
                self._create_project(args)
                if not args.bare:
                    self._populate_project(args)
            except:
                PROJECT_STORAGE.destroy()
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


COMMAND = InitializeCommand(__name__, help_page_fmt=HELP_PAGE, summary_fmt="Initialize TAU Commander.")
