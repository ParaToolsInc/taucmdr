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
"""``target create`` subcommand."""

import os
from collections import Counter

import six
from taucmdr import util
from taucmdr.error import ConfigurationError
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CreateCommand
from taucmdr.model.target import Target
from taucmdr.model.compiler import Compiler
from taucmdr.cf.compiler import Knowledgebase, InstalledCompiler, InstalledCompilerFamily
from taucmdr.cf.compiler.host import HOST_COMPILERS, FC
from taucmdr.cf.compiler.mpi import MPI_COMPILERS
from taucmdr.cf.compiler.shmem import SHMEM_COMPILERS
from taucmdr.cf.compiler.cuda import CUDA_COMPILERS
from taucmdr.cf.platforms import TauMagic, HOST_ARCH, HOST_OS, CRAY_CNL
from taucmdr.cf.software.tau_installation import TauInstallation, TAU_MINIMAL_COMPILERS



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

    def _parse_tau_makefile(self, args):
        # Parsing a TAU Makefile is a really hairy operation, so let's lift the limits
        # pylint: disable=too-many-statements,too-many-locals
        makefile = args.forced_makefile
        if not util.path_accessible(makefile):
            self.parser.error("Invalid TAU makefile: %s" % makefile)
        tau_arch_name = os.path.basename(os.path.dirname(os.path.dirname(makefile)))
        matches = [arch for arch in TauMagic.all() if arch.name == tau_arch_name]
        if len(matches) == 1:
            tau_arch = matches[0]
        elif len(matches) == 0:
            raise ConfigurationError("TAU Makefile '%s' targets an unrecognized TAU architecture: %s" % 
                                     (makefile, tau_arch_name))
        else:
            for arch in matches:
                if arch.architecture == HOST_ARCH and arch.operating_system == HOST_OS:
                    tau_arch = arch
                    break
            else:
                parts = ["TAU Makefile '%s' targets an ambiguous TAU architecture: %s" % (makefile, tau_arch_name),
                         "It could be any of these:"]
                parts.extend(["  - %s on %s" % (arch.operating_system.name, arch.architecture.name) 
                              for arch in matches])
                raise ConfigurationError("\n".join(parts))
        self.logger.info("Parsing TAU Makefile '%s' to populate command line arguments:", makefile)
        args.host_arch = tau_arch.architecture.name
        self.logger.info("  --host-arch='%s'", args.host_arch)
        args.host_os = tau_arch.operating_system.name
        self.logger.info("  --host-os='%s'", args.host_os)
        args.tau_source = os.path.abspath(os.path.join(os.path.dirname(makefile), '..', '..'))
        self.logger.info("  --taucmdr='%s'", args.tau_source)
        with open(makefile, 'r') as fin:
            compiler_parts = ("FULL_CC", "FULL_CXX", "TAU_F90")
            package_parts = {"BFDINCLUDE": ("binutils_source", lambda x: os.path.dirname(x.lstrip("-I"))), 
                             "UNWIND_INC": ("libunwind_source", lambda x: os.path.dirname(x.lstrip("-I"))),
                             "PAPIDIR": ("papi_source", os.path.abspath),
                             "PDTDIR": ("pdt_source", os.path.abspath),
                             "SCOREPDIR": ("scorep_source", os.path.abspath)}
            tau_r = ''
            for line in fin:
                if line.startswith('#'):
                    continue
                try:
                    key, val = [x.strip() for x in line.split('=', 1)]
                except ValueError:
                    continue
                if key == 'TAU_R':
                    tau_r = val.split()[0]
                elif key in compiler_parts:
                    path = util.which(val.strip().split()[0].replace('$(TAU_R)', tau_r))
                    if not path:
                        self.logger.warning("Failed to parse %s in TAU Makefile '%s'", key, makefile)
                        continue
                    matching_info = Knowledgebase.find_compiler(os.path.basename(path))
                    if matching_info:
                        if len(matching_info) > 1:
                            self.logger.warning("Ambiguous compiler '%s' in TAU Makefile '%s'", path, makefile)
                        comp = InstalledCompiler(path, matching_info[0])
                        attr = comp.info.role.keyword
                        setattr(args, attr, comp.absolute_path)
                        self.logger.info("  --%s='%s'", attr.lower().replace("_", "-"), comp.absolute_path)
                        while comp.wrapped:
                            comp = comp.wrapped
                            attr = comp.info.role.keyword
                            setattr(args, attr, comp.absolute_path)
                            self.logger.info("  --%s='%s'", attr.lower().replace("_", "-"), comp.absolute_path)
                elif key in package_parts:
                    attr, operator = package_parts[key]
                    path = val.strip()
                    if not path:
                        path = None
                    else:
                        path = operator(path)
                        if not os.path.exists(path):
                            self.logger.warning("'%s' referenced by TAU Makefile '%s' doesn't exist", path, makefile)
                            continue
                    setattr(args, attr, path)
                    self.logger.info("  --%s='%s'", attr.replace("_source", ""), path)

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
        compilers = {role: self._get_compiler_from_env(role) for role in six.itervalues(kbase.roles)}
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
                for role, comp in six.iteritems(compilers):
                    if comp is None:
                        compilers[role] = family[role]
        sibling = next((comp for comp in six.itervalues(compilers) if comp is not None), None)
        for role, comp in six.iteritems(compilers):
            if not comp:
                if sibling:
                    # If some compilers found, but not all, then use compiler
                    # family information to get default compilers.
                    compilers[role] = self._get_compiler_from_sibling(role, sibling)
                else:
                    # No environment variables specify compiler defaults so use model defaults.
                    compilers[role] = self._get_compiler_from_defaults(kbase, role)
        # Use the majority family as the default compiler family.
        family_count = Counter(comp.info.family for comp in six.itervalues(compilers) if comp is not None)
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
        for role, comp in six.iteritems(compilers):
            action = next(act for act in group._actions if act.dest == role.keyword)
            action.default = comp.absolute_path if comp else arguments.SUPPRESS
            action.__action_call__ = action.__call__
            action.__call__ = TargetCreateCommand._compiler_flag_action_call(family_attr)
        # Use the name of the default compiler family as a hint for the next search
        return family_default

    def _construct_parser(self):
        parser = super(TargetCreateCommand, self)._construct_parser()
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
        args = super(TargetCreateCommand, self)._parse_args(argv)
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
        for kbase in HOST_COMPILERS, MPI_COMPILERS, SHMEM_COMPILERS, CUDA_COMPILERS:
            for role in six.itervalues(kbase.roles):
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
            self._parse_tau_makefile(args)
            self.logger.debug('Arguments after parsing TAU Makefile: %s', args)
        compilers = self.parse_compiler_flags(args)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for comp in six.itervalues(compilers):
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid

        return super(TargetCreateCommand, self)._create_record(store, data)


COMMAND = TargetCreateCommand(Target, __name__)
