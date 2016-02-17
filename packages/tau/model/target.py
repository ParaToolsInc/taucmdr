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

from tau.error import InternalError, ConfigurationError
from tau.mvc.model import Model
from tau.mvc.controller import Controller
from tau.cf.compiler import CompilerRole
from tau.cf.compiler.installed import InstalledCompilerSet
from tau.cf.target import host, DARWIN_OS, INTEL_KNC_ARCH
from tau.model.compiler import Compiler


def attributes():
    from tau.model.project import Project
    from tau.cli.arguments import ParsePackagePathAction
    from tau.cf.target import Architecture, OperatingSystem
    from tau.model.measurement import intel_only
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
            'default': host.operating_system().name,
            'argparse': {'flags': ('--host-os',),
                         'group': 'host',
                         'metavar': '<os>',
                         'choices': OperatingSystem.keys()}
        },
        'host_arch': {
            'type': 'string',
            'required': True,
            'description': 'host architecture',
            'default': host.architecture().name,
            'argparse': {'flags': ('--host-arch',),
                         'group': 'host',
                         'metavar': '<arch>',
                         'choices': Architecture.keys()},
            'compat': {str(INTEL_KNC_ARCH): 
                       (Target.require('CC_ROLE', intel_only),
                        Target.require('CXX_ROLE', intel_only),
                        Target.require('FC_ROLE', intel_only))}
        },
        'CC': {
            'model': Compiler,
            'required': True,
            'description': 'Host C compiler command',
            'argparse': {'flags': ('--cc',),
                         'group': 'host',
                         'metavar': '<command>'}
        },
        'CXX': {
            'model': Compiler,
            'required': True,
            'description': 'Host C++ compiler command',
            'argparse': {'flags': ('--cxx',),
                         'group': 'host',
                         'metavar': '<command>'}
        },
        'FC': {
            'model': Compiler,
            'required': True,
            'description': 'Host Fortran compiler command',
            'argparse': {'flags': ('--fc',),
                         'group': 'host',
                         'metavar': '<command>'}
        },
        'UPC': {
            'model': Compiler,
            'required': False,
            'description': 'Universal Parallel C compiler command',
            'argparse': {'flags': ('--upc',),
                         'group': 'Universal Parallel C',
                         'metavar': '<command>'}
        },
        'MPI_CC': {
            'model': Compiler,
            'required': False,
            'description': 'MPI C compiler command',
            'argparse': {'flags': ('--mpi-cc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'}
        },
        'MPI_CXX': {
            'model': Compiler,
            'required': False,
            'description': 'MPI C++ compiler command',
            'argparse': {'flags': ('--mpi-cxx',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'}
        },
        'MPI_FC': {
            'model': Compiler,
            'required': False,
            'description': 'MPI Fortran compiler command',
            'argparse': {'flags': ('--mpi-fc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<command>'}
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
                              Target.require("MPI_FC"))}
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
                              Target.require("MPI_FC"))}
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
                              Target.require("MPI_FC"))}
        },
        'SHMEM_CC': {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C compiler command',
            'argparse': {'flags': ('--shmem-cc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'}
        },
        'SHMEM_CXX': {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM C++ compiler command',
            'argparse': {'flags': ('--shmem-cxx',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'}
        },
        'SHMEM_FC': {
            'model': Compiler,
            'required': False,
            'description': 'SHMEM Fortran compiler command',
            'argparse': {'flags': ('--shmem-fc',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<command>'}
        },
        'shmem_include_path': {
            'type': 'array',
            'description': 'paths to search for SHMEM header files when building SHMEM applications',
            'argparse': {'flags': ('--shmem-include-path',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<path>',
                         'nargs': '+'},
        },
        'shmem_library_path': {
            'type': 'array',
            'description': 'paths to search for SHMEM library files when building SHMEM applications',
            'argparse': {'flags': ('--shmem-library-path',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<path>',
                         'nargs': '+'},
        },
        'shmem_libraries': {
            'type': 'array',
            'description': 'libraries to link to when building SHMEM applications',
            'argparse': {'flags': ('--shmem-libraries',),
                         'group': 'Symmetric Hierarchical Memory (SHMEM)',
                         'metavar': '<flag>',
                         'nargs': '+'},
        },
        'cuda': {
            'type': 'string',
            'description': 'path to NVIDIA CUDA installation (enables OpenCL support)',
            'argparse': {'flags': ('--cuda',),
                         'group': 'software package',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'opencl': {
            'type': 'string',
            'description': 'path to OpenCL libraries and headers',
            'argparse': {'flags': ('--opencl',),
                         'group': 'software package',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'tau_source': {
            'type': 'string',
            'description': 'path or URL to a TAU installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--tau',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download)',
                         'action': ParsePackagePathAction}
        },
        'pdt_source': {
            'type': 'string',
            'description': 'path or URL to a PDT installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--pdt',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
        },
        'binutils_source': {
            'type': 'string',
            'description': 'path or URL to a GNU binutils installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--binutils',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN_OS.name)}
        },
        'libunwind_source': {
            'type': 'string',
            'description': 'path or URL to a libunwind installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--libunwind',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        },
        'papi_source': {
            'type': 'string',
            'description': 'path or URL to a PAPI installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--papi',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
            'compat': {(lambda x: x is not None): Target.discourage('host_os', DARWIN_OS.name)}
        },
        'scorep_source': {
            'type': 'string',
            'description': 'path or URL to a Score-P installation or archive file',
            'argparse': {'flags': ('--score-p',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        }
    }


class TargetController(Controller):
    """Target data controller."""


class Target(Model):
    """Target data model."""
    
    __attributes__ = attributes

    __controller__ = TargetController
    
    def on_create(self):
        super(Target, self).on_create()
        if not self['tau_source']:
            raise ConfigurationError("A TAU installation or source code must be provided.")
    
    def compilers(self):
        """Get information about the compilers used by this target configuration.
         
        Returns:
            InstalledCompilerSet: Collection of installed compilers used by this target.
        """
        eids = []
        compilers = {}
        for role in CompilerRole.all():
            try:
                compiler_command = self.populate(attribute=role.keyword)
            except KeyError:
                continue
            compilers[role.keyword] = compiler_command.info()
            eids.append(compiler_command.eid)
        missing = [role.keyword for role in CompilerRole.tau_required() if role.keyword not in compilers]
        if missing:
            raise InternalError("Target '%s' is missing required compilers: %s" % (self['name'], missing))
        return InstalledCompilerSet('_'.join([str(x) for x in eids]), **compilers)

    def check_compiler(self, given_compiler, compiler_args):
        """Checks a compiler command its arguments for compatibility with this target configuration.
        
        Checks that the given compiler matches one of the compilers used in the target.
        Also performs any special checkes for invalid compiler arguments, e.g. -mmic is only for native KNC.
        
        Args:
            given_compiler (str): The compiler command as passed by the user.
            compiler_args (list): Compiler command line arguments.
            
        Raises:
            ConfigurationError: The compiler or command line arguments are incompatible with this target.
        """
        compiler_ctrl = Compiler.controller(self.storage)
        given_compiler_eid = compiler_ctrl.register(given_compiler).eid
        target_compiler_eid = self[given_compiler.info.role.keyword]       
        # Confirm target supports compiler
        if given_compiler_eid != target_compiler_eid:
            target_compiler = compiler_ctrl.one(target_compiler_eid).info()
            target_info_abs = target_compiler.info.short_descr, target_compiler.absolute_path
            given_info_abs = given_compiler.info.short_descr, given_compiler.absolute_path
            raise ConfigurationError("Target '%s' is configured with %s '%s', not %s '%s'" %
                                     tuple([self['name']] + list(target_info_abs) + list(given_info_abs)),
                                     "Select a different target",
                                     "Compile with %s '%s'" % target_info_abs,
                                     "Create a new target configured with %s '%s'" % given_info_abs)
        # Handle special cases where a compiler flag isn't compatible with the target
        if '-mmic' in compiler_args and self['host_arch'] != INTEL_KNC_ARCH:
            raise ConfigurationError("Host architecture of target '%s' is '%s'"
                                     " but the '-mmic' compiler argument requires '%s'" %
                                     (self['name'], self['host_arch'], INTEL_KNC_ARCH),
                                     "Select a different target",
                                     "Create a new target with host architecture '%s'" % INTEL_KNC_ARCH)
                
            
