#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

import platform
from tau.arguments import ParsePackagePathAction
from tau.controller import Controller, ByName
from tau.error import ConfigurationError, InternalError
from tau.cf.tau import KNOWN_TARGET_ARCH, KNOWN_TARGET_OS
from tau.cf.compiler.set import CompilerSet
from tau.cf.compiler.role import ALL_ROLES, REQUIRED_ROLES



class Target(Controller, ByName):

    """
    Target data model controller
    """

    attributes = {
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
            'default': platform.system(),
            'argparse': {'flags': ('--host-os',),
                         'group': 'target system',
                         'metavar': 'os',
                         'choices': KNOWN_TARGET_OS}
        }, 
        'host_arch': {
            'type': 'string',
            'required': True,
            'description': 'host architecture',
            'default': platform.machine(),
            'argparse': {'flags': ('--host-arch',),
                         'group': 'target system',
                         'metavar': 'arch',
                         'choices': KNOWN_TARGET_ARCH}
        },
        # TODO: Get TAU to support a proper host/device model for offloading, etc.
#         'device_arch': {
#             'type': 'string',
#             'description': 'coprocessor architecture',
#             'default': None,
#             'argparse': {'flags': ('--device-arch',),
#                          'group': 'target system',
#                          'metavar': 'arch'}
#         },
        'CC': {
            'model': 'CompilerCommand',
            'required': True,
            'description': 'C compiler command',
            'argparse': {'flags': ('--cc',),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'CXX': {
            'model': 'CompilerCommand',
            'required': True,
            'description': 'C++ compiler command',
            'argparse': {'flags': ('--cxx', '--c++'),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'FC': {
            'model': 'CompilerCommand',
            'required': True,
            'description': 'Fortran compiler command',
            'argparse': {'flags': ('--fc', '--fortran'),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'F77': {
            'model': 'CompilerCommand',
            'description': 'FORTRAN77 compiler command',
            'argparse': {'flags': ('--f77',),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'F90': {
            'model': 'CompilerCommand',
            'description': 'Fortran90 compiler command',
            'argparse': {'flags': ('--f90',),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'UPC': {
            'model': 'CompilerCommand',
            'description': 'Universal Parallel C compiler command',
            'argparse': {'flags': ('--upc',),
                         'group': 'compiler',
                         'metavar': '<command>'}
        },
        'cuda': {
            'type': 'string',
            'description': 'path to NVIDIA CUDA installation',
            'default': None,
            'argparse': {'flags': ('--cuda',),
                         'group': 'software package',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'mpi_include_path': {
            'type': 'array',
            'default': None,
            'description': 'paths to search for MPI header files when building MPI applications',
            'argparse': {'flags': ('--mpi-include-paths',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'mpi_library_path': {
            'type': 'array',
            'default': None,
            'description': 'paths to search for MPI library files when building MPI applications',
            'argparse': {'flags': ('--mpi-library-paths',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'mpi_compiler_flags': {
            'type': 'array',
            'default': None,
            'description': 'additional compiler flags required to build MPI applications',
            'argparse': {'flags': ('--mpi-compiler-flags',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<flag>',
                         'nargs': '+'},
        },
        'mpi_linker_flags': {
            'type': 'array',
            'default': None,
            'description': 'additional linker flags required to build MPI applications',
            'argparse': {'flags': ('--mpi-linker-flags',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<flag>',
                         'nargs': '+'},
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
        'bfd_source': {
            'type': 'string',
            'description': 'path or URL to a GNU binutils installation or archive file',
            'default': 'download',
            'argparse': {'flags': ('--bfd',),
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
            'default': None,
            'argparse': {'flags': ('--papi',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        },
        'score-p_source': {
            'type': 'string',
            'description': 'path or URL to a Score-P installation or archive file',
            'default': None,
            'argparse': {'flags': ('--score-p',),
                         'group': 'software package',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        }
    }

    def get_compilers(self):
        """Get Compiler objects for all compilers in this Target.
        
        Returns:
            A CompilerSet with all required compilers set.
        """
        eids = []
        compilers = {}
        for role in ALL_ROLES:
            try:
                compiler_command = self.populate(role.keyword)
            except KeyError:
                continue
            compilers[role.keyword] = compiler_command.info()
            eids.append(str(compiler_command.eid))
        missing = [role.keyword for role in REQUIRED_ROLES if role.keyword not in compilers]
        if missing:
            raise InternalError("Target '%s' is missing required compilers: %s" % (self['name'], missing))
        return CompilerSet('_'.join(eids), **compilers)
