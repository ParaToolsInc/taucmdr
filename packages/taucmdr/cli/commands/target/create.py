#
# Copyright (c) 2015-2026, ParaTools, Inc.
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
"""``target create`` subcommand."""

import os
from collections import Counter
from taucmdr.error import ConfigurationError
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CreateCommand
from taucmdr.model.target import Target
from taucmdr.model.compiler import Compiler
from taucmdr.cf.compiler import InstalledCompiler, InstalledCompilerFamily
from taucmdr.cf.compiler.host import HOST_COMPILERS, FC
from taucmdr.cf.compiler.mpi import MPI_COMPILERS
from taucmdr.cf.compiler.shmem import SHMEM_COMPILERS
from taucmdr.cf.compiler.cuda import CUDA_COMPILERS
from taucmdr.cf.compiler.caf import CAF_COMPILERS
from taucmdr.cf.compiler.python import PYTHON_INTERPRETERS
from taucmdr.cf.platforms import HOST_OS, CRAY_CNL
from taucmdr.cf.software.tau_installation import TauInstallation, TAU_MINIMAL_COMPILERS, tau_makefile_target



class TargetCreateCommand(CreateCommand):
    """``target create`` subcommand."""

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

    def parse_tau_makefile(self, args):
        """Set target arguments from the TAU Makefile in ``args.forced_makefile``.

        Args:
            args: A namespace of parsed command line arguments, updated in place.

        Raises:
            ConfigurationError: The makefile can't be read, or its ``TAU_ARCH`` is missing, unknown, or ambiguous.
        """
        found = tau_makefile_target(args.forced_makefile)
        self.logger.info("Parsing TAU Makefile '%s' to populate command line arguments:", args.forced_makefile)
        for attr, value in found.items():
            setattr(args, attr, value)
            self.logger.info("  %s='%s'", Target.attributes[attr]['argparse']['flags'][0], value)

    def _get_compiler_from_env(self, role):
        """If compiler environment variable set (e.g. CC) use that value to fill this role."""
        for var in role.envars:
            try:
                comp = InstalledCompiler.probe(os.environ[var], role=role)
            except KeyError:
                # Environment variable not set
                continue
            except ConfigurationError as err:
                self.logger.debug(err)
                continue
            else:
                return comp
        return None

    def _get_compiler_from_sibling(self, role, sibling):
        """If we know a compiler sibling then use its family information to fill this role."""
        for info in sibling.info.family.members.get(role, []):
            try:
                comp = InstalledCompiler.probe(info.command, family=sibling.info.family, role=role)
            except ConfigurationError as err:
                self.logger.debug(err)
                continue
            else:
                return comp
        return None

    def _get_compiler_from_defaults(self, kbase, role):
        """Use model defaults and preferred family to fill this role."""
        # If default not set in environment, use model default.
        try:
            comp = InstalledCompiler.probe(Target.attributes[role.keyword]['default'], role=role)
        except KeyError:
            # Default not set in model
            pass
        except ConfigurationError as err:
            self.logger.debug(err)
        else:
            return comp
        # If no model default use check all compiler families starting with the host's preferred family
        for family in kbase.iterfamilies():
            for info in family.members.get(role, []):
                try:
                    comp = InstalledCompiler.probe(info.command, family=family, role=role)
                except ConfigurationError as err:
                    self.logger.debug(err)
                    continue
                else:
                    return comp
        return None

    def _configure_argument_group(self, group, kbase, family_flag, family_attr, hint):
        # Check environment variables for default compilers.
        compilers = {role: self._get_compiler_from_env(role) for role in kbase.roles.values()}
        # Use the result of previous compiler detection to find compilers not specified in the environment
        if hint:
            try:
                family = InstalledCompilerFamily(kbase.families[hint])
            except ConfigurationError as err:
                # Something wrong with that installation... oh well, keep going
                self.logger.debug(err)
            except KeyError:
                # Suggested family might not support this compiler group,
                # e.g. Intel doesn't have SHMEM compilers.
                pass
            else:
                for role, comp in compilers.items():
                    if comp is None and role in family:
                        compilers[role] = family[role]
        sibling = next((comp for comp in compilers.values() if comp is not None), None)
        for role, comp in compilers.items():
            if not comp:
                if sibling:
                    # If some compilers found, but not all, then use compiler
                    # family information to get default compilers.
                    compilers[role] = self._get_compiler_from_sibling(role, sibling)
                else:
                    # No environment variables specify compiler defaults so use model defaults.
                    compilers[role] = self._get_compiler_from_defaults(kbase, role)
        # Use the majority family as the default compiler family.
        family_count = Counter(comp.info.family for comp in compilers.values() if comp is not None)
        try:
            family_default = family_count.most_common()[0][0].name
        except IndexError:
            family_default = arguments.SUPPRESS
        # Add the compiler family flag. If the knowledgebase keyword isn't all-caps then show in lower case.
        keyword = kbase.keyword
        if keyword.upper() != keyword:
            keyword = keyword.lower()
        group.add_argument(family_flag,
                           help=("select all %(kw)s compilers automatically from the given family, "
                                 "ignored if at least one %(kw)s compiler is specified") % {'kw': keyword},
                           metavar='<family>',
                           dest=family_attr,
                           default=family_default,
                           choices=kbase.family_names(),
                           action=TargetCreateCommand._family_flag_action(kbase, family_attr))
        # Monkey-patch default actions for compiler arguments
        # pylint: disable=protected-access
        for role, comp in compilers.items():
            action = next(act for act in group._actions if act.dest == role.keyword)
            action.default = comp.absolute_path if comp else arguments.SUPPRESS
            action.__action_call__ = action.__call__
            action.__call__ = TargetCreateCommand._compiler_flag_action_call(family_attr)
        # Use the name of the default compiler family as a hint for the next search
        return family_default

    def _construct_parser(self):
        parser = super()._construct_parser()
        group = parser.add_argument_group('host arguments')
        host_family_name = self._configure_argument_group(group, HOST_COMPILERS, '--compilers', 'host_family', None)

        # Crays are weird. Don't use the detected host family as a hint for MPI or SHMEM compilers
        # so that we'll always chose the Cray compiler wrappers.
        hint = host_family_name if HOST_OS is not CRAY_CNL else None

        group = parser.add_argument_group('Message Passing Interface (MPI) arguments')
        self._configure_argument_group(group, MPI_COMPILERS, '--mpi-wrappers', 'mpi_family', hint)

        group = parser.add_argument_group('Symmetric Hierarchical Memory (SHMEM) arguments')
        self._configure_argument_group(group, SHMEM_COMPILERS, '--shmem-compilers', 'shmem_family', hint)

        group = parser.add_argument_group('CUDA arguments')
        self._configure_argument_group(group, CUDA_COMPILERS, '--cuda-compilers', 'cuda_family', hint)

        return parser

    def _parse_args(self, argv):
        args = super()._parse_args(argv)
        # Check that all required compilers were found
        for role in TAU_MINIMAL_COMPILERS:
            if role.keyword not in args:
                raise ConfigurationError("%s compiler is required but could not be found" % role.language,
                                         "See 'compiler arguments' under `%s --help`" % COMMAND)
        if FC.keyword not in args:
            args.scorep_source = None
        return args

    def parse_compiler_flags(self, args):
        """Create a dictionary of :any:`InstalledCompiler` instances from commandl line arguments.

        Args:
            args: A namespace of parsed command line arguments.

        Returns:
            dict: InstalledCompiler instances indexed by role keyword.
        """
        compilers = {}
        for kbase in HOST_COMPILERS, MPI_COMPILERS, SHMEM_COMPILERS, CUDA_COMPILERS, CAF_COMPILERS, PYTHON_INTERPRETERS:
            for role in kbase.roles.values():
                try:
                    command = getattr(args, role.keyword)
                except AttributeError:
                    continue
                compilers[role.keyword] = InstalledCompiler.probe(command, role=role)
        return compilers

    def main(self, argv):
        TauInstallation.check_env_compat()
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        if hasattr(args, "forced_makefile"):
            self.parse_tau_makefile(args)
            self.logger.debug('Arguments after parsing TAU Makefile: %s', args)
        compilers = self.parse_compiler_flags(args)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for comp in compilers.values():
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid

        return super()._create_record(store, data)


COMMAND = TargetCreateCommand(Target, __name__)
