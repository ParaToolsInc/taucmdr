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
"""``tau configure`` subcommand."""

from tau import EXIT_SUCCESS
from tau import configuration
from tau.error import InternalError
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.storage.levels import STORAGE_LEVELS, PROJECT_STORAGE, ORDERED_LEVELS
from tau.model.project import Project
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.model.experiment import Experiment
from tau.model.target import Target
from tau.cf.software import SoftwarePackageError


class ConfigureCommand(AbstractCommand):
    """``tau configure`` subcommand."""

    def construct_parser(self):
        """Constructs the command line argument parser.
          
        Returns:
            A command line argument parser instance.
        """
        usage = "%s [arguments] <key> <value>" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        arguments.add_storage_flags(parser, "Get or set", "configuration item")
        parser.add_argument('key',
                            help="option key",
                            metavar='<key>',
                            nargs='?',
                            default=arguments.SUPPRESS)
        parser.add_argument('value',
                            help="option value",
                            metavar='<value>',
                            nargs='?',
                            default=arguments.SUPPRESS)
        parser.add_argument('-u', '--unset',
                            help="unset configuration option",
                            action='store_const',
                            const=True,
                            default=arguments.SUPPRESS)
        parser.add_argument('--file',
                            help="Configuration input file",
                            metavar='/path/to/config.file',
                            nargs='?',
                            const=True)
        parser.add_argument('-i', '--install',
                            help="Install selected configurations",
                            action='store_const',
                            const=True,
                            default=arguments.SUPPRESS)
        return parser

    def get_target(self):
        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except ProjectSelectionError:
            self.parser.error("No project configuration selected.  Please use --project to specify one.")
        return proj.populate('targets')
        
    def get_appl(self):
        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except ProjectSelectionError:
            self.parser.error("No project configuration selected.  Please use --project to specify one.")
        return proj.populate('applications')
        
    def get_meas(self):
        proj_ctrl = Project.controller()
        try:
            proj = proj_ctrl.selected()
        except ProjectSelectionError:
            self.parser.error("No project configuration selected.  Please use --project to specify one.")
        return proj.populate('applications')
        


    def configure_tau_dependency(self, name, prefix, storage):
        """Installs dependency packages for TAU, e.g. PDT.
        
        Args:
            name (str): Name of the dependency to install.  
                        Must have a matching tau.cf.software.<name>_installation module.
            prefix (str): Installation prefix.
        
        Returns:
            Installation: A new installation instance for the installed dependency.
        """
        targ = self.get_target()
        target = targ.pop()
        cls_name = name.title() + 'Installation'
        pkg = __import__('tau.cf.software.%s_installation' % name.lower(), globals(), locals(), [cls_name], -1)
        cls = getattr(pkg, cls_name)
        opts = (target.get(name + '_source', None), target['host_arch'], target['host_os'], target.compilers())
#        for storage in reversed(ORDERED_LEVELS):
        inst = cls(storage.prefix, *opts)
        try:
            inst.verify()
        except SoftwarePackageError:
            pass
        else:
            return inst
        inst = cls(prefix, *opts)
        with inst:
            inst.install()
            return inst       


    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        storage = STORAGE_LEVELS[getattr(args, '@')[0]]
        if not hasattr(args, 'key') and args.file is None and not hasattr(args, 'install'):
            for key, val in configuration.get(storage=storage).iteritems():
                print '%s : %s' % (key, val)       
        elif not hasattr(args, 'key') and args.file is not None and not hasattr(args, 'install'):
            input_file = open(args.file, 'r')
            for line in input_file:
                [key, value] =line.split()
                configuration.put(key, value, storage)
        elif not hasattr(args, 'key') and hasattr(args, 'install'):
            all_dependencies = configuration.get('dependencies', storage=storage)
            all_dependencies = all_dependencies.encode('ascii', 'replace')
            all_dependencies = all_dependencies.split(',')
            dependencies = {}
            prefix = storage.prefix
            for name in all_dependencies:
                inst = self.configure_tau_dependency(name, prefix, storage)
                dependencies[name] = inst

        elif not (hasattr(args, 'value') or hasattr(args, 'unset')):
            try:
                print configuration.get(args.key, storage)
            except KeyError:
                self.parser.error('Invalid key: %s' % args.key)
        elif hasattr(args, 'unset'):
            try:
                configuration.delete(args.key, storage)
            except KeyError:
                self.parser.error('Invalid key: %s' % args.key)
        elif hasattr(args, 'value'):
            configuration.put(args.key, args.value, storage)
        else:
            raise InternalError("Unhandled arguments in %s" % COMMAND)
        return EXIT_SUCCESS


COMMAND = ConfigureCommand(__name__, summary_fmt="Configure TAU Commander.")
