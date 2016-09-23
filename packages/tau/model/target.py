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
"""Target data model.

:any:`Target` fully describes the hardware and software environment that our
experiments will be performed in.  The hardware architecture, available compilers,
and system libraries are described in the target record.  There will be multiple
target records for any physical computer system since each target record uniquely
describes a specific set of system features.  For example, if both GNU and Intel
compilers are installed then there will target configurations for each compiler family.
"""

import os
import glob
from tau import logger, util
from tau.error import InternalError, ConfigurationError, IncompatibleRecordError
from tau.mvc.model import Model
from tau.model.compiler import Compiler
from tau.cf.compiler import Knowledgebase, InstalledCompilerSet
from tau.cf.target import host, DARWIN_OS, INTEL_KNC_ARCH
from tau.cf.software.tau_installation import TAU_MINIMAL_COMPILERS

LOGGER = logger.get_logger(__name__)


def knc_require_k1om(*_):
    """Compatibility checking callback for use with data models.

    Requires that the Intel k1om tools be installed if the host architecture is KNC. 
        
    Raises:
        ConfigurationError: Invalid compiler family specified in target configuration.
    """
    k1om_ar = util.which('x86_64-k1om-linux-ar')
    if not k1om_ar:
        for path in glob.glob('/usr/linux-k1om-*'):
            k1om_ar = util.which(os.path.join(path, 'bin', 'x86_64-k1om-linux-ar'))
            if k1om_ar:
                break
        else:
            raise ConfigurationError('k1om tools not found', 'Try installing on compute node', 'Install MIC SDK')


def attributes():
    """Construct attributes dictionary for the target model.
    
    We build the attributes in a function so that classes like ``tau.module.project.Project`` are
    fully initialized and usable in the returned dictionary.
    
    Returns:
        dict: Attributes dictionary.
    """
    from tau.model.project import Project
    from tau.cli.arguments import ParsePackagePathAction
    from tau.cf.target import Architecture, OperatingSystem
    from tau.cf.compiler.host import CC, CXX, FC, UPC, INTEL
    from tau.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC, INTEL as INTEL_MPI
    from tau.cf.compiler.shmem import SHMEM_CC, SHMEM_CXX, SHMEM_FC
    from tau.model import require_compiler_family
    
    knc_intel_only = require_compiler_family(INTEL, 
                                             "You must use Intel compilers to target the Xeon Phi",
                                             "Try adding `--compilers=Intel` to the command line")
    knc_intel_mpi_only = require_compiler_family(INTEL_MPI,
                                                 "You must use Intel MPI compilers to target the Xeon Phi",
                                                 "Try adding `--mpi-compilers=Intel` to the command line")

    host_os = host.operating_system()
    
    return {
        'projects': {
            'collection': Project,
            'via': 'targets',
            'description': 'projects using this target'
        },
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': 'target configuration name',
            'argparse': {'metavar': '<target_name>'}
        },
        'host_os': {
            'type': 'string',
            'required': True,
            'description': 'host operating system',
            'default': host_os.name,
            'argparse': {'flags': ('--os',),
                         'group': 'host',
                         'metavar': '<os>',
                         'choices': OperatingSystem.keys()},
            'on_change': Target.attribute_changed
        },
        'host_arch': {
            'type': 'string',
            'required': True,
            'description': 'host architecture',
            'default': host.architecture().name,
            'argparse': {'flags': ('--arch',),
                         'group': 'host',
                         'metavar': '<arch>',
                         'choices': Architecture.keys()},
            'compat': {str(INTEL_KNC_ARCH): 
                       (Target.require('CC', knc_intel_only),
                        Target.require('CXX', knc_intel_only),
                        Target.require('FC', knc_intel_only),
                        Target.require('host_arch', knc_require_k1om),
                        Target.require('MPI_CC', knc_intel_mpi_only),
                        Target.require('MPI_CXX', knc_intel_mpi_only),
                        Target.require('MPI_FC', knc_intel_mpi_only))},
            'on_change': Target.attribute_changed
        },
        CC.keyword: {
            'model': Compiler,
            'required': True,
            'description': 'Host C compiler command',
            'argparse': {'flags': ('--cc',),
                         'group': 'host',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        CXX.keyword: {
            'model': Compiler,
            'required': True,
            'description': 'Host C++ compiler command',
            'argparse': {'flags': ('--cxx',),
                         'group': 'host',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Host Fortran compiler command',
            'argparse': {'flags': ('--fc',),
                         'group': 'host',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        UPC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'Universal Parallel C compiler command',
            'argparse': {'flags': ('--upc',),
                         'group': 'Universal Parallel C',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        MPI_CC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI C compiler command',
            'argparse': {'flags': ('--mpi-cc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        MPI_CXX.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI C++ compiler command',
            'argparse': {'flags': ('--mpi-cxx',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        MPI_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'MPI Fortran compiler command',
            'argparse': {'flags': ('--mpi-fc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        'mpi_include_path': {
            'type': 'array',
            'description': 'paths to search for MPI header files when building MPI applications',
            'argparse': {'flags': ('--mpi-include-path',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'nargs': '+'},
            'compat': {bool: (Target.require("MPI_CC"),
                              Target.require("MPI_CXX"),
                              Target.require("MPI_FC"))},
            'on_change': Target.attribute_changed
        },
        'mpi_library_path': {
            'type': 'array',
            'description': 'paths to search for MPI library files when building MPI applications',
            'argparse': {'flags': ('--mpi-library-path',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'nargs': '+'},
            'compat': {bool: (Target.require("MPI_CC"),
                              Target.require("MPI_CXX"),
                              Target.require("MPI_FC"))},
            'on_change': Target.attribute_changed
        },
        'mpi_libraries': {
            'type': 'array',
            'description': 'libraries to link to when building MPI applications',
            'argparse': {'flags': ('--mpi-libraries',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<flag>',
                         'nargs': '+'},
            'compat': {bool: (Target.require("MPI_CC"),
                              Target.require("MPI_CXX"),
                              Target.require("MPI_FC"))},
            'on_change': Target.attribute_changed
        },
        SHMEM_CC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C compiler command',
            'argparse': {'flags': ('--shmem-cc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        SHMEM_CXX.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C++ compiler command',
            'argparse': {'flags': ('--shmem-cxx',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        SHMEM_FC.keyword: {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM Fortran compiler command',
            'argparse': {'flags': ('--shmem-fc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'},
            'on_change': Target.attribute_changed
        },
        'shmem_include_path': {
            'type': 'array',
            'description': 'paths to search for SHMEM header files when building SHMEM applications',
            'argparse': {'flags': ('--shmem-include-path',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<path>',
                         'nargs': '+'},
            'on_change': Target.attribute_changed
        },
        'shmem_library_path': {
            'type': 'array',
            'description': 'paths to search for SHMEM library files when building SHMEM applications',
            'argparse': {'flags': ('--shmem-library-path',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<path>',
                         'nargs': '+'},
            'on_change': Target.attribute_changed
        },
        'shmem_libraries': {
            'type': 'array',
            'description': 'libraries to link to when building SHMEM applications',
            'argparse': {'flags': ('--shmem-libraries',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<flag>',
                         'nargs': '+'},
            'on_change': Target.attribute_changed
        },
        'cuda': {
            'type': 'string',
            'description': 'path to NVIDIA CUDA installation (enables OpenCL support)',
            'argparse': {'flags': ('--cuda',),
                         'group': 'software package',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
            'on_change': Target.attribute_changed
        },
        'tau_source': {
            'type': 'string',
            'description': 'path or URL to a TAU installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--tau',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download)',
                         'action': ParsePackagePathAction},
            'on_change': Target.attribute_changed
        },
        'pdt_source': {
            'type': 'string',
            'description': 'path or URL to a PDT installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--pdt',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'on_change': Target.attribute_changed
        },
        'binutils_source': {
            'type': 'string',
            'description': 'path or URL to a GNU binutils installation or archive file',
            'default': 'download' if host_os is not DARWIN_OS else None,
            'argparse': {'flags': ('--binutils',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN_OS.name)},
            'on_change': Target.attribute_changed
        },
        'libunwind_source': {
            'type': 'string',
            'description': 'path or URL to a libunwind installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--libunwind',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'on_change': Target.attribute_changed
        },
        'papi_source': {
            'type': 'string',
            'description': 'path or URL to a PAPI installation or archive file',
            'default': 'download' if host_os is not DARWIN_OS else None,
            'argparse': {'flags': ('--papi',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN_OS.name)},
            'on_change': Target.attribute_changed
        },
        'scorep_source': {
            'type': 'string',
            'description': 'path or URL to a Score-P installation or archive file',
            'default': 'download' if host_os is not DARWIN_OS else None,
            'argparse': {'flags': ('--scorep',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN_OS.name)},
            'on_change': Target.attribute_changed
        }
    }


class Target(Model):
    """Target data model."""
    
    __attributes__ = attributes
    
    def __init__(self, *args, **kwargs):
        super(Target, self).__init__(*args, **kwargs)
        self._compilers = None
        
    @classmethod
    def attribute_changed(cls, model, attr, new_value):
        if model.is_selected():
            old_value = model.get(attr, None)
            Target.controller(model.storage).push_to_topic('rebuild_required', {attr: (old_value, new_value)})
    
    def on_create(self):
        if not self['tau_source']:
            raise ConfigurationError("A TAU installation or source code must be provided.")
    
    def on_update(self):
        from tau.error import ImmutableRecordError
        from tau.model.experiment import Experiment
        expr_ctrl = Experiment.controller()
        found = expr_ctrl.search({'target': self.eid})
        used_by = [expr['name'] for expr in found if expr.data_size() > 0]
        if used_by:
            raise ImmutableRecordError("Target '%s' cannot be modified because "
                                       "it is used by these experiments: %s" % (self['name'], ', '.join(used_by)))
        for expr in found:
            try:
                expr.verify()
            except IncompatibleRecordError as err:
                raise ConfigurationError("Changing measurement '%s' in this way will create an invalid condition "
                                         "in experiment '%s':\n    %s." % (self['name'], expr['name'], err),
                                         "Delete experiment '%s' and try again." % expr['name'])
    
    def is_selected(self):
        """Returns True if this target configuration is part of the selected experiment, False otherwise."""
        from tau.model.project import Project, ProjectSelectionError, ExperimentSelectionError
        try:
            selected = Project.controller().selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError):
            return False
        return selected['target'] == self.eid
    
    def compilers(self):
        """Get information about the compilers used by this target configuration.
        
        Returns:
            InstalledCompilerSet: Collection of installed compilers used by this target.
        """
        if not self._compilers:
            eids = []
            compilers = {}
            for role in Knowledgebase.all_roles():
                try:
                    compiler_record = self.populate(role.keyword)
                except KeyError:
                    continue
                compilers[role.keyword] = compiler_record.installation_info()
                LOGGER.debug("compilers[%s] = '%s'", role.keyword, compilers[role.keyword].absolute_path)
                eids.append(compiler_record.eid)
            missing = [role for role in TAU_MINIMAL_COMPILERS if role.keyword not in compilers]
            if missing:
                raise InternalError("Target '%s' is missing required compilers: %s" % (self['name'], missing))
            self._compilers = InstalledCompilerSet('_'.join([str(x) for x in sorted(eids)]), **compilers)
        return self._compilers

    def check_compiler(self, compiler_cmd, compiler_args):
        """Checks a compiler command its arguments for compatibility with this target configuration.
        
        Checks that the given compiler matches one of the compilers used in the target.
        Also performs any special checkes for invalid compiler arguments, e.g. -mmic is only for native KNC.
        
        If the given compiler command and arguments are compatible with this target then information about
        the compiler installation is returned as an :any:`InstalledCompiler` instance.
        
        Args:
            compiler_cmd (str): The compiler command as passed by the user.
            compiler_args (list): Compiler command line arguments.
            
        Returns:
            InstalledCompiler: Information about the installed compiler.
            
        Raises:
            ConfigurationError: The compiler or command line arguments are incompatible with this target.
        """
        compiler_ctrl = Compiler.controller(self.storage)
        absolute_path = util.which(compiler_cmd)
        installed_comp = None
        known_compilers = [comp for comp in self.compilers().iteritems()]
        # Check that this target supports the given compiler
        for role in Knowledgebase.all_roles():
            try:
                compiler_record = self.populate(role.keyword)
            except KeyError:
                continue
            # Target was configured with this compiler
            if compiler_record['path'] == absolute_path:
                installed_comp = compiler_record.installation_info(probe=True)
            else:
                # Target was configured with a wrapper compiler so check if that wrapper wraps this compiler
                while 'wrapped' in compiler_record:
                    compiler_record = compiler_ctrl.one(compiler_record['wrapped'])
                    comp = compiler_record.installation_info(probe=True)
                    known_compilers.append(comp)
                    compiler_path = compiler_record['path']
                    if (absolute_path and (compiler_path == absolute_path) or 
                            (not absolute_path and (os.path.basename(compiler_path) == compiler_cmd))):
                        installed_comp = comp
                        break
            if installed_comp:
                LOGGER.debug("'%s' appears to be a %s", compiler_cmd, installed_comp.info.short_descr)
                break
        else:
            parts = ["No compiler in target '%s' matches '%s'." % (self['name'], absolute_path),
                     "The known compiler commands are:"]
            parts.extend('  %s (%s)' % (comp.absolute_path, comp.info.short_descr) for comp in known_compilers)
            hints = ("Try one of the valid compiler commands",
                     "Create and select a new target configuration that uses the '%s' compiler" % compiler_cmd,
                     "Check loaded modules and the PATH environment variable")
            raise ConfigurationError('\n'.join(parts), *hints)

        # Handle special cases where a compiler flag isn't compatible with the target
        if '-mmic' in compiler_args and self['host_arch'] != str(INTEL_KNC_ARCH):
            raise ConfigurationError("Host architecture of target '%s' is '%s'"
                                     " but the '-mmic' compiler argument requires '%s'" %
                                     (self['name'], self['host_arch'], INTEL_KNC_ARCH),
                                     "Select a different target",
                                     "Create a new target with host architecture '%s'" % INTEL_KNC_ARCH)

        return installed_comp

