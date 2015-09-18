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
from tau.cli.arguments import ParsePackagePathAction
from tau.model import Controller, ByName
from tau.cf.target import Architecture, OperatingSystem
from tau.cf.target import host
from tau.cf.compiler import CC_ROLE, CXX_ROLE, FC_ROLE, UPC_ROLE, CompilerRole
from tau.cf.compiler.mpi import MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE
from tau.cf.compiler.shmem import SHMEM_CC_ROLE, SHMEM_CXX_ROLE, SHMEM_FC_ROLE
from tau.cf.compiler.installed import InstalledCompilerSet 


class Target(Controller, ByName):
    """Target data controller."""

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
                compiler_command = self.populate(role.keyword)
            except KeyError:
                continue
            compilers[role.keyword] = compiler_command.info()
            eids.append(compiler_command.eid)
        missing = [role.keyword for role in CompilerRole.tau_required() if role.keyword not in compilers]
        if missing:
            raise InternalError("Target '%s' is missing required compilers: %s" % (self['name'], missing))
        return InstalledCompilerSet('_'.join([str(x) for x in eids]), **compilers)


Target.attributes = {
    'projects': {
        'collection': 'Project',
        'via': 'targets',
        'description': 'projects using this target'
    },
    'name': {
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
                     'group': 'target system',
                     'metavar': '<os>',
                     'choices': OperatingSystem.keys()}
    },
    'host_arch': {
        'type': 'string',
        'required': True,
        'description': 'host architecture',
        'default': host.architecture().name,
        'argparse': {'flags': ('--host-arch',),
                     'group': 'target system',
                     'metavar': '<arch>',
                     'choices': Architecture.keys()}
    },
    CC_ROLE.keyword: {
        'model': 'Compiler',
        'required': CC_ROLE.required,
        'description': '%s compiler command' % CC_ROLE.language,
        'argparse': {'flags': ('--cc',),
                     'group': 'compiler',
                     'metavar': '<command>'}
    },
    CXX_ROLE.keyword: {
        'model': 'Compiler',
        'required': CXX_ROLE.required,
        'description': '%s compiler command' % CXX_ROLE.language,
        'argparse': {'flags': ('--cxx',),
                     'group': 'compiler',
                     'metavar': '<command>'}
    },
    FC_ROLE.keyword: {
        'model': 'Compiler',
        'required': FC_ROLE.required,
        'description': '%s compiler command' % FC_ROLE.language,
        'argparse': {'flags': ('--fc',),
                     'group': 'compiler',
                     'metavar': '<command>'}
    },
    UPC_ROLE.keyword: {
        'model': 'Compiler',
        'required': UPC_ROLE.required,
        'description': '%s compiler command' % UPC_ROLE.language,
        'argparse': {'flags': ('--upc',),
                     'group': 'Universal Parallel C',
                     'metavar': '<command>'}
    },
    MPI_CC_ROLE.keyword: {
        'model': 'Compiler',
        'required': MPI_CC_ROLE.required,
        'description': '%s compiler command' % MPI_CC_ROLE.language,
        'argparse': {'flags': ('--mpi-cc',),
                     'group': 'Message Passing Interface (MPI)',
                     'metavar': '<command>'}
    },
    MPI_CXX_ROLE.keyword: {
        'model': 'Compiler',
        'required': MPI_CXX_ROLE.required,
        'description': '%s compiler command' % MPI_CXX_ROLE.language,
        'argparse': {'flags': ('--mpi-cxx',),
                     'group': 'Message Passing Interface (MPI)',
                     'metavar': '<command>'}
    },
    MPI_FC_ROLE.keyword: {
        'model': 'Compiler',
        'required': MPI_FC_ROLE.required,
        'description': '%s compiler command' % MPI_FC_ROLE.language,
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
        'compat': {bool: (Target.require(MPI_CC_ROLE.keyword),
                          Target.require(MPI_CXX_ROLE.keyword),
                          Target.require(MPI_FC_ROLE.keyword))}
    },
    'mpi_library_path': {
        'type': 'array',
        'description': 'paths to search for MPI library files when building MPI applications',
        'argparse': {'flags': ('--mpi-library-path',),
                     'group': 'Message Passing Interface (MPI)',
                     'metavar': '<path>',
                     'nargs': '+'},
        'compat': {bool: (Target.require(MPI_CC_ROLE.keyword),
                          Target.require(MPI_CXX_ROLE.keyword),
                          Target.require(MPI_FC_ROLE.keyword))}
    },
    'mpi_libraries': {
        'type': 'array',
        'description': 'libraries to link to when building MPI applications',
        'argparse': {'flags': ('--mpi-libraries',),
                     'group': 'Message Passing Interface (MPI)',
                     'metavar': '<flag>',
                     'nargs': '+'},
        'compat': {bool: (Target.require(MPI_CC_ROLE.keyword),
                          Target.require(MPI_CXX_ROLE.keyword),
                          Target.require(MPI_FC_ROLE.keyword))}
    },
    SHMEM_CC_ROLE.keyword: {
        'model': 'Compiler',
        'required': SHMEM_CC_ROLE.required,
        'description': '%s compiler command' % SHMEM_CC_ROLE.language,
        'argparse': {'flags': ('--shmem-cc',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<command>'}
    },
    SHMEM_CXX_ROLE.keyword: {
        'model': 'Compiler',
        'required': SHMEM_CXX_ROLE.required,
        'description': '%s compiler command' % SHMEM_CXX_ROLE.language,
        'argparse': {'flags': ('--mpi-cxx',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<command>'}
    },
    SHMEM_FC_ROLE.keyword: {
        'model': 'Compiler',
        'required': SHMEM_FC_ROLE.required,
        'description': '%s compiler command' % SHMEM_FC_ROLE.language,
        'argparse': {'flags': ('--mpi-fc',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<command>'}
    },
    'shmem_include_path': {
        'type': 'array',
        'description': 'paths to search for SHMEM header files when building SHMEM applications',
        'argparse': {'flags': ('--mpi-include-path',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<path>',
                     'nargs': '+'},
    },
    'shmem_library_path': {
        'type': 'array',
        'description': 'paths to search for SHMEM library files when building SHMEM applications',
        'argparse': {'flags': ('--mpi-library-path',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<path>',
                     'nargs': '+'},
    },
    'shmem_libraries': {
        'type': 'array',
        'description': 'libraries to link to when building SHMEM applications',
        'argparse': {'flags': ('--mpi-libraries',),
                     'group': 'Symmetric Hierarchical Memory (SHMEM)',
                     'metavar': '<flag>',
                     'nargs': '+'},
    },
    'cuda': {
        'type': 'string',
        'description': 'path to NVIDIA CUDA installation',
        'argparse': {'flags': ('--cuda',),
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
                     'action': ParsePackagePathAction}
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
        'argparse': {'flags': ('--papi',),
                     'group': 'software package',
                     'metavar': '(<path>|<url>|download|None)',
                     'action': ParsePackagePathAction}
    },
    'score-p_source': {
        'type': 'string',
        'description': 'path or URL to a Score-P installation or archive file',
        'argparse': {'flags': ('--score-p',),
                     'group': 'software package',
                     'metavar': '(<path>|<url>|download|None)',
                     'action': ParsePackagePathAction}
    }
}
