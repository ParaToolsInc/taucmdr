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

from tau import util
from tau.error import ImmutableRecordError, IncompatibleRecordError
from tau.cli import arguments
from tau.cli.cli_view import EditCommand
from tau.cli.commands.target.copy import COMMAND as target_copy_cmd
from tau.cli.commands.experiment.delete import COMMAND as experiment_delete_cmd
from tau.model.target import Target
from tau.model.experiment import Experiment
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole
from tau.cf.compiler.mpi import MpiCompilerFamily
from tau.cf.compiler.shmem import ShmemCompilerFamily
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
        compilers = {}

        for family_attr, family_cls in [('host_family', CompilerFamily), 
                                        ('mpi_family', MpiCompilerFamily),
                                        ('shmem_family', ShmemCompilerFamily)]:
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
                compilers[comp.info.role] = comp

        compiler_keys = set(CompilerRole.keys())
        all_keys = set(args.__dict__.keys())
        given_keys = compiler_keys & all_keys
        family_keys = set(role.keyword for role in compilers)
        self.logger.debug("Given compilers: %s", given_keys)
        self.logger.debug("Family compilers: %s", family_keys)

        for key in given_keys - family_keys:
            absolute_path = util.which(getattr(args, key))
            if not absolute_path:
                self.parser.error("Invalid compiler command: %s")
            role = CompilerRole.find(key)
            compilers[role] = InstalledCompiler.probe(absolute_path, role=role)
        return compilers

    def _construct_parser(self):
        parser = super(TargetEditCommand, self)._construct_parser()
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
        group = parser.add_argument_group('Symmetric Hierarchical Memory (SHMEM) arguments')
        group.add_argument('--shmem-compilers', 
                           help="select all SHMEM compilers automatically from the given family",
                           metavar='<family>',
                           dest='shmem_family',
                           default=arguments.SUPPRESS,
                           choices=ShmemCompilerFamily.family_names())
        return parser
    
    def _update_record(self, store, data, key):
        try:
            retval = super(TargetEditCommand, self)._update_record(store, data, key)
        except (ImmutableRecordError, IncompatibleRecordError) as err:
            err.hints = ["Use `%s` to create a modified copy of the target" % target_copy_cmd,
                         "Use `%s` to delete the experiments." % experiment_delete_cmd]
            raise err
        if not retval:
            self.logger.info(Experiment.rebuild_required())
        return retval

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        
        compilers = self.parse_compiler_flags(args)
        self.logger.debug('Arguments after parsing compiler flags: %s', args)
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for keyword, comp in compilers.iteritems():
            self.logger.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid

        key_attr = self.model.key_attribute
        try:
            data[key_attr] = args.new_key
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        return self._update_record(store, data, key)


COMMAND = TargetEditCommand(Target, __name__)
