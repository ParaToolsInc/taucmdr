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
"""``tau target edit`` subcommand."""

from tau import EXIT_SUCCESS
from tau import util
from tau.storage.levels import STORAGE_LEVELS
from tau.cli import arguments
from tau.cli.cli_view import EditCommand
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole
from tau.cf.compiler.mpi import MpiCompilerFamily, MPI_CXX_ROLE, MPI_CC_ROLE, MPI_FC_ROLE
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily


class TargetEditCommand(EditCommand):
    """``tau target edit`` subcommand."""

    def parse_compiler_flags(self, args):
        """Parses host compiler flags out of the command line arguments.

        Args:
            args: Argument namespace containing command line arguments.

        Returns:
            dict: Installed compilers by role keyword string.

        Raises:
            ConfigurationError: Invalid command line arguments specified
        """
        compiler_keys = set(CompilerRole.keys())
        all_keys = set(args.__dict__.keys())
        given_keys = compiler_keys & all_keys
        self.logger.debug("Given compilers: %s", given_keys)
        compilers = {}

        for family_attr, family_cls in [('host_family', CompilerFamily), ('mpi_family', MpiCompilerFamily)]:
            try:
                family_arg = getattr(args, family_attr)
            except AttributeError as err:
                # User didn't specify that argument, but that's OK
                self.logger.debug(err)
                continue
            else:
                delattr(args, family_attr)
            try:
                family_comps = InstalledCompilerFamily(family_cls(family_arg))
            except KeyError:
                self.parser.error("Invalid compiler family: %s" % family_arg)
            for comp in family_comps:
                self.logger.debug("args.%s=%r", comp.info.role.keyword, comp.absolute_path)
                setattr(args, comp.info.role.keyword, comp.absolute_path)

        for key in given_keys:
            absolute_path = util.which(getattr(args, key))
            if not absolute_path:
                self.parser.error("Invalid compiler command: %s")
            role = CompilerRole.find(key)
            compilers[role] = InstalledCompiler.probe(absolute_path, role=role)
        
        # Probe MPI compilers to discover wrapper flags
        mpi_keys = set([getattr(role, 'keyword') for role in MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE])
        for key in mpi_keys & given_keys:
            for args_attr, wrapped_attr in [('mpi_include_path', 'include_path'), 
                                            ('mpi_library_path', 'library_path'),
                                            ('mpi_libraries', 'libraries')]:
                if not hasattr(args, args_attr):
                    probed = set()
                    try:
                        comp = compilers[key]
                    except KeyError:
                        self.logger.debug("Not probing %s", key)
                    else:
                        probed.update(getattr(comp.wrapped, wrapped_attr))
                    setattr(args, args_attr, list(probed))
        return compilers

    def construct_parser(self):
        parser = super(TargetEditCommand, self).construct_parser()
        group = parser.add_argument_group('host arguments')
        group.add_argument('--compilers',
                           help="select all host compilers automatically from the given family",
                           metavar='<family>',
                           dest='host_family',
                           default=arguments.SUPPRESS,
                           choices=CompilerFamily.family_names())
        group = parser.add_argument_group('Message Passing Interface (MPI) arguments')
        group.add_argument('--mpi-compilers', 
                           help="select all MPI compilers automatically from the given family",
                           metavar='<family>',
                           dest='mpi_family',
                           default=arguments.SUPPRESS,
                           choices=MpiCompilerFamily.family_names())
        return parser
    
    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = STORAGE_LEVELS[getattr(args, arguments.STORAGE_LEVEL_FLAG)[0]]
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        key = getattr(args, key_attr)
        if not ctrl.exists({key_attr: key}):
            self.parser.error("No %s-level %s with %s='%s'." % (ctrl.storage.name, self.model_name, key_attr, key)) 

        compilers = self.parse_compiler_flags(args)
        self.logger.debug('Arguments after parsing compiler flags: %s', args)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for keyword, comp in compilers.iteritems():
            self.logger.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid
        try:
            data[key_attr] = args.new_key
        except AttributeError:
            pass
        ctrl.update(data, {key_attr: key})
        self.logger.info("Updated %s '%s'", self.model_name, key)
        return EXIT_SUCCESS

COMMAND = TargetEditCommand(Target, __name__)
