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
from tau.cf.storage.levels import STORAGE_LEVELS
from tau.cli import arguments
from tau.cli.cli_view import CreateCommand
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole, CompilerInfo
from tau.cf.compiler.mpi import MpiCompilerFamily
from tau.cf.compiler.shmem import ShmemCompilerFamily
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily
from tau.cf.target import host
from tau.cf.target import TauArch

class TargetCreateCommand(CreateCommand):
    """``tau target create`` subcommand."""

    def _probe_compiler_family(self, args, compilers, family_attr, family_cls):
        try:
            family_arg = getattr(args, family_attr)
        except AttributeError as err:
            # User didn't specify that argument, but that's OK
            self.logger.debug(err)
            return
        if family_arg == "None":
            return
        try:
            family_comps = InstalledCompilerFamily(family_cls(family_arg))
        except KeyError:
            self.parser.error("Invalid compiler family: %s" % family_arg)
        for comp in family_comps:
            self.logger.debug("args.%s=%r", comp.info.role.keyword, comp.absolute_path)
            setattr(args, comp.info.role.keyword, comp.absolute_path)
            compilers[comp.info.role] = comp
    
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
            self._probe_compiler_family(args, compilers, 'host_family', CompilerFamily)
        self._probe_compiler_family(args, compilers, 'mpi_family', MpiCompilerFamily)
        self._probe_compiler_family(args, compilers, 'shmem_family', ShmemCompilerFamily)

        compiler_keys = set(CompilerRole.keys())
        all_keys = set(args.__dict__.keys())
        given_keys = compiler_keys & all_keys
        missing_keys = compiler_keys - given_keys
        family_keys = set(role.keyword for role in compilers)
        self.logger.debug("Given compilers: %s", given_keys)
        self.logger.debug("Missing compilers: %s", missing_keys)
        self.logger.debug("Family compilers: %s", family_keys)

        for key in given_keys - family_keys:
            cmd = getattr(args, key)
            absolute_path = util.which(cmd)
            if not absolute_path:
                self.parser.error("Invalid compiler command: %s" % cmd)
            role = CompilerRole.find(key)
            compilers[role] = InstalledCompiler.probe(absolute_path, role=role)

        for key in missing_keys:
            role = CompilerRole.find(key)
            try:
                compilers[role] = host.default_compiler(role)
            except ConfigurationError as err:
                self.logger.debug(err)
    
        # Check that all required compilers were found
        for role in CompilerRole.tau_required():
            if role not in compilers:
                raise ConfigurationError("%s compiler could not be found" % role.language,
                                         "See 'compiler arguments' under `%s --help`" % COMMAND)
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
        try:
            InstalledCompilerFamily(family)
        except ConfigurationError:
            return "None"
        else:
            return family.name

    def construct_parser(self):
        parser = super(TargetCreateCommand, self).construct_parser()
        group = parser.add_argument_group('host arguments')
        group.add_argument('--compilers',
                           help="select all host compilers automatically from the given family",
                           metavar='<family>',
                           dest='host_family',
                           default=host.preferred_compilers().name,
                           choices=CompilerFamily.family_names())
        group = parser.add_argument_group('Message Passing Interface (MPI) arguments')
        group.add_argument('--mpi-compilers', 
                           help="select all MPI compilers automatically from the given family",
                           metavar='<family>',
                           dest='mpi_family',
                           default=self._check_default_compilers(host.preferred_mpi_compilers()),
                           choices=["None"] + MpiCompilerFamily.family_names())
        group = parser.add_argument_group('Symmetric Hierarchical Memory (SHMEM) arguments')
        group.add_argument('--shmem-compilers', 
                           help="select all SHMEM compilers automatically from the given family",
                           metavar='<family>',
                           dest='shmem_family',
                           default=self._check_default_compilers(host.preferred_shmem_compilers()),
                           choices=["None"] + ShmemCompilerFamily.family_names())
        parser.add_argument('--from-tau-makefile',
                            help="Populate target configuration from a TAU Makefile",
                            metavar='<path>',
                            dest='tau_makefile',
                            default=arguments.SUPPRESS)
        return parser
    
    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = STORAGE_LEVELS[getattr(args, arguments.STORAGE_LEVEL_FLAG)[0]]

        if hasattr(args, "tau_makefile"):
            self._parse_tau_makefile(args)
            self.logger.debug('Arguments after parsing TAU Makefile: %s', args)
        
        compilers = self.parse_compiler_flags(args)
        self.logger.debug('Arguments after parsing compiler flags: %s', args)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        for keyword, comp in compilers.iteritems():
            self.logger.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
            record = Compiler.controller(store).register(comp)
            data[comp.info.role.keyword] = record.eid
            
        return super(TargetCreateCommand, self).create_record(store, data)

COMMAND = TargetCreateCommand(Target, __name__)
