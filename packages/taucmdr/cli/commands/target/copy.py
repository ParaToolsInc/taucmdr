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
"""``target copy`` subcommand."""

from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CopyCommand
from taucmdr.cli.commands.target.create import COMMAND as target_create_cmd
from taucmdr.model.target import Target
from taucmdr.model.compiler import Compiler
from taucmdr.cf.compiler import InstalledCompilerFamily
from taucmdr.cf.compiler.host import HOST_COMPILERS
from taucmdr.cf.compiler.mpi import MPI_COMPILERS
from taucmdr.cf.compiler.shmem import SHMEM_COMPILERS
from taucmdr.cf.software.tau_installation import TauInstallation


class TargetCopyCommand(CopyCommand):
    """```target copy``` subcommand."""

    @staticmethod
    def _compiler_flag_action_call(family_attr):
        def call(self, parser, namespace, value, *args, **kwargs):
            try:
                delattr(namespace, family_attr)
            except AttributeError:
                pass
            return self.__action_call__(parser, namespace, value, *args, **kwargs)
        return call

    @staticmethod
    def _family_flag_action(kbase, family_attr):
        class Action(arguments.Action):
            # pylint: disable=too-few-public-methods
            def __call__(self, parser, namespace, value, *args, **kwargs):
                try:
                    delattr(namespace, family_attr)
                except AttributeError:
                    pass
                family = InstalledCompilerFamily(kbase.families[value])
                for comp in family:
                    setattr(namespace, comp.info.role.keyword, comp.absolute_path)
        return Action

    def _configure_argument_group(self, group, kbase, family_flag, family_attr):
        # Add the compiler family flag. If the knowledgebase keyword isn't all-caps then show in lower case.
        keyword = kbase.keyword
        if keyword.upper() != keyword:
            keyword = keyword.lower()
        group.add_argument(family_flag,
                           help=("select all %(kw)s compilers automatically from the given family, "
                                 "ignored if at least one %(kw)s compiler is specified") % {'kw': keyword},
                           metavar='<family>',
                           dest=family_attr,
                           default=arguments.SUPPRESS,
                           choices=kbase.family_names(),
                           action=TargetCopyCommand._family_flag_action(kbase, family_attr))

        # Monkey-patch default actions for compiler arguments
        # pylint: disable=protected-access
        for role in kbase.roles.itervalues():
            action = next(act for act in group._actions if act.dest == role.keyword)
            action.__action_call__ = action.__call__
            action.__call__ = TargetCopyCommand._compiler_flag_action_call(family_attr)

    def _construct_parser(self):
        parser = super(TargetCopyCommand, self)._construct_parser()
        group = parser.add_argument_group('host arguments')
        self._configure_argument_group(group, HOST_COMPILERS, '--compilers', 'host_family')

        group = parser.add_argument_group('Message Passing Interface (MPI) arguments')
        self._configure_argument_group(group, MPI_COMPILERS, '--mpi-wrappers', 'mpi_family')

        group = parser.add_argument_group('Symmetric Hierarchical Memory (SHMEM) arguments')
        self._configure_argument_group(group, SHMEM_COMPILERS, '--shmem-compilers', 'shmem_family')
        return parser

    def main(self, argv):
        TauInstallation.check_env_compat()
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        compilers = target_create_cmd.parse_compiler_flags(args)
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for keyword, comp in compilers.iteritems():
            self.logger.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid
        key_attr = self.model.key_attribute
        try:
            data[key_attr] = getattr(args, 'copy_%s' % key_attr)
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        return self._copy_record(store, data, key)

COMMAND = TargetCopyCommand(Target, __name__)
