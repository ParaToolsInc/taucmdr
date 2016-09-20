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
"""``tau target create`` subcommand."""

import os
from tau import util
from tau.error import ConfigurationError
from tau.cli import arguments
from tau.cli.cli_view import CreateCommand
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole, CompilerInfo, COMPILER_ROLES
from tau.cf.compiler.mpi import MpiCompilerFamily, MPI_COMPILER_ROLES
from tau.cf.compiler.shmem import ShmemCompilerFamily, SHMEM_COMPILER_ROLES
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily
from tau.cf.target import TauArch
from tau.cf.software.tau_installation import TAU_MINIMAL_COMPILERS

class TargetCreateCommand(CreateCommand):
    """``tau target create`` subcommand."""

    def _find_from_family(self, family_arg, family_cls):
        if family_arg.lower() != "none":
            family = InstalledCompilerFamily(family_cls(family_arg))
            return {comp.info.role: comp for comp in family}
        return {}

    def _probe_compiler_family(self, args, family_attr, family_cls, family_roles):
        compilers = {}
        seen_actions = getattr(args, '__seen_actions__', {})
        compiler_keys = set(role.keyword for role in family_roles)
        all_keys = set(seen_actions.keys())
        given_keys = compiler_keys & all_keys
        missing_keys = compiler_keys - given_keys
        self.logger.debug("Given %s compilers: %s", family_attr, given_keys)
        self.logger.debug("Missing %s compilers: %s", family_attr, missing_keys)
        # Either the family or role flags should be given, not both
        if given_keys and family_attr in seen_actions:
            role_flags = []
            for key in given_keys:
                role_flags.extend(Target.attributes[key]['argparse']['flags'])
            family_flags = seen_actions[family_attr].option_strings
            self.parser.error("%s may not be used with %s" % (', '.join(family_flags), ', '.join(role_flags)))
        # Check manually specified compiler commands
        for key in given_keys:
            cmd = getattr(args, key)
            absolute_path = util.which(cmd)
            if not absolute_path:
                self.parser.error("Invalid compiler command: %s" % cmd)
            role = CompilerRole.find(key)
            compilers[role] = InstalledCompiler.probe(absolute_path, role=role)
        # Find compilers not specified by the user
        if missing_keys:
            if compilers:
                # Use a compiler to discover missing compilers
                comp = compilers.itervalues().next()
                for key in missing_keys:
                    role = CompilerRole.find(key)
                    for info in comp.info.family.members.get(role, []):
                        try:
                            compilers[role] = InstalledCompiler.probe(info.command, role=role)
                        except ConfigurationError as err:
                            self.logger.debug(err)
            elif family_attr in seen_actions:
                # Use family argument to discover all missing compilers 
                family_arg = getattr(args, family_attr)
                compilers.update(self._find_from_family(family_arg, family_cls))
            else:
                # Fall back to parser default values. Prefer CC, etc. over family argument.
                for role in family_roles:
                    try:
                        compilers[role] = InstalledCompiler.probe(getattr(args, role.keyword), role=role)
                    except AttributeError:
                        # No default value for this compiler role
                        pass
                    except ConfigurationError as err:
                        self.logger.debug(err)
        # If any compilers are still missing then use the family argument to find them.
        missing_keys = missing_keys - set(role.keyword for role in compilers.iterkeys())
        if missing_keys:
            self.logger.debug("Missing %s compilers after probe: %s", family_attr, missing_keys)
            family_arg = getattr(args, family_attr)
            compilers.update(self._find_from_family(family_arg, family_cls))

        # Warn user if a compiler role can't be filled
        for role in family_roles:
            if role not in compilers:
                self.logger.info("Could not find a %s compiler.", role.language)
        delattr(args, family_attr)
        return compilers
    
    def parse_compiler_flags(self, args):
        """Parses host compiler flags out of the command line arguments.
         
        Args:
            args: Argument namespace containing command line arguments
             
        Returns:
            Dictionary of installed compilers by role keyword string.
             
        Raises:
            ConfigurationError: Invalid command line arguments specified
        """
        compilers = {}
        if not hasattr(args, 'tau_makefile'):
            # TAU Makefile specifies host compilers, but not others.
            compilers.update(self._probe_compiler_family(args, 'host_family', CompilerFamily, COMPILER_ROLES))
        compilers.update(self._probe_compiler_family(args, 'mpi_family', MpiCompilerFamily, MPI_COMPILER_ROLES))
        compilers.update(self._probe_compiler_family(args, 'shmem_family', ShmemCompilerFamily, SHMEM_COMPILER_ROLES))
        # Check that all required compilers were found
        for role in TAU_MINIMAL_COMPILERS:
            if role not in compilers:
                raise ConfigurationError("%s compiler is required but could not be found" % role.language,
                                         "See 'compiler arguments' under `%s --help`" % COMMAND)
        # Warn user if mixing compiler families
        families = set(comp.unwrap().info.family for comp in compilers.itervalues())
        if len(families) > 1:
            comp_parts = []
            for comp in compilers.itervalues():
                if comp.wrapped:
                    wrapped = comp.unwrap()
                    comp_parts.append("  - %s '%s' wrapped by %s '%s'" % 
                                      (wrapped.info.short_descr, wrapped.absolute_path, 
                                       comp.info.short_descr, comp.absolute_path))
                else:
                    comp_parts.append("  - %s '%s'" % (comp.info.short_descr, comp.absolute_path))
            parts = ["Configured with compilers from different families:"]
            parts.extend(sorted(comp_parts))
            self.logger.warning('\n'.join(parts))
        # Update arguments
        for role, comp in compilers.iteritems():
            self.logger.debug("args.%s='%s'", role.keyword, comp.absolute_path)
            setattr(args, role.keyword, comp.absolute_path)
        return compilers
    
    def _parse_tau_makefile(self, args):
        # Parsing a TAU Makefile is a really hairy operation, so let's lift the limit on statements
        # pylint: disable=too-many-statements
        makefile = args.tau_makefile
        if not util.file_accessible(makefile):
            self.parser.error("Invalid TAU makefile: %s" % makefile)
        tau_arch_name = os.path.basename(os.path.dirname(os.path.dirname(makefile)))
        try:
            tau_arch = TauArch.find(tau_arch_name)
        except KeyError:
            raise ConfigurationError("TAU Makefile '%s' targets an unrecognized TAU architecture: %s" % 
                                     (makefile, tau_arch_name))
        self.logger.info("Parsing TAU Makefile '%s' to populate command line arguments:", makefile)
        args.host_arch = tau_arch.architecture.name
        self.logger.info("  --host-arch='%s'", args.host_arch)
        args.host_os = tau_arch.operating_system.name
        self.logger.info("  --host-os='%s'", args.host_os)
        args.tau_source = os.path.abspath(os.path.join(os.path.dirname(makefile), '..', '..'))
        self.logger.info("  --tau='%s'", args.tau_source)
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
                    matching_info = CompilerInfo.find(os.path.basename(path))
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

    def _check_default_compilers(self, family):
        found = {}
        for role, complist in family.members.iteritems():
            for comp in complist:
                if util.which(comp.command):
                    found[role] = comp
                    break
        if not found:
            return "None"
        else:
            return family.name

    def _construct_parser(self):
        parser = super(TargetCreateCommand, self)._construct_parser()
        group = parser.add_argument_group('host arguments')
        group.add_argument('--compilers',
                           help=("select all host compilers automatically from the given family, "
                                 "ignored if at least one host compiler is specified"),
                           metavar='<family>',
                           dest='host_family',
                           default=CompilerFamily.preferred().name,
                           choices=CompilerFamily.family_names())
        group = parser.add_argument_group('Message Passing Interface (MPI) arguments')
        group.add_argument('--mpi-compilers', 
                           help=("select all MPI compilers automatically from the given family, "
                                 "ignored if at least one MPI compiler is specified"),
                           metavar='<family>',
                           dest='mpi_family',
                           default=self._check_default_compilers(MpiCompilerFamily.preferred()),
                           choices=["None"] + MpiCompilerFamily.family_names())
        group = parser.add_argument_group('Symmetric Hierarchical Memory (SHMEM) arguments')
        group.add_argument('--shmem-compilers', 
                           help=("select all SHMEM compilers automatically from the given family, "
                                 "ignored if at least one SHMEM compiler is specified"),
                           metavar='<family>',
                           dest='shmem_family',
                           default=self._check_default_compilers(ShmemCompilerFamily.preferred()),
                           choices=["None"] + ShmemCompilerFamily.family_names())
        parser.add_argument('--from-tau-makefile',
                            help="Populate target configuration from a TAU Makefile",
                            metavar='<path>',
                            dest='tau_makefile',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]

        if hasattr(args, "tau_makefile"):
            self._parse_tau_makefile(args)
            self.logger.debug('Arguments after parsing TAU Makefile: %s', args)
        
        compilers = self.parse_compiler_flags(args)
        self.logger.debug('Arguments after parsing compiler flags: %s', args)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for comp in compilers.itervalues():
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid
            
        return super(TargetCreateCommand, self)._create_record(store, data)

COMMAND = TargetCreateCommand(Target, __name__)
