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

import os
import platform
import subprocess
from tau import logger
from tau.arguments import ParsePackagePathAction
from tau.controller import Controller, ByName
from tau.error import ConfigurationError, InternalError
from tau.cf.compiler.set import CompilerSet
from tau.cf.compiler.role import ALL_ROLES, REQUIRED_ROLES


LOGGER = logger.getLogger(__name__)


def host_os_default():
    """
    Detect the default host operating system
    """
    return platform.system()


def host_arch_default():
    """
    Use TAU's archfind script to detect the host target architecture
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cmd = os.path.join(os.path.dirname(here), 'util', 'archfind', 'archfind')
    _HOST_ARCH = subprocess.check_output(cmd).strip() 
    return _HOST_ARCH


def device_arch_default():
    """
    Detect coprocessors
    """
    # TODO
    return None


def libunwind_default():
    if host_arch_default() == 'apple':
        return None
    else:
        return 'download'


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
            'default': host_os_default(),
            'argparse': {'flags': ('--host-os',),
                         'group': 'target system',
                         'metavar': 'os'}
        }, 
        'host_arch': {
            'type': 'string',
            'required': True,
            'description': 'host architecture',
            'default': host_arch_default(),
            'argparse': {'flags': ('--host-arch',),
                         'group': 'target system',
                         'metavar': 'arch'}
        },
        'device_arch': {
            'type': 'string',
            'description': 'coprocessor architecture',
            'default': device_arch_default(),
            'argparse': {'flags': ('--device-arch',),
                         'group': 'target system',
                         'metavar': 'arch'}
        },
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
        'mpi_incdir': {
            'type': 'string',
            'description': 'path to directory containing MPI header files',
            'argparse': {'flags': ('--mpi-inc',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'mpi_libdir': {
            'type': 'string',
            'description': 'path to MPI directory containing MPI library files',
            'argparse': {'flags': ('--mpi-lib',),
                         'group': 'Message Passing Interface (MPI)',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'mpi_ldflags': {
            'type': 'array',
            'description': 'additional linker flags required by MPI ',
            'argparse': {'flags': ('--mpi-ldflags',),
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
            'default': libunwind_default(),
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

    def onCreate(self):
        if self['libunwind_source'] and self['host_arch'] == 'apple':
            libunwind_flag = self.attributes['libunwind_source']['argparse']['flags'][0]
            raise ConfigurationError("libunwind not supported on host architecture 'apple'",
                                     "Use %s=None" % libunwind_flag)
        
    
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
        return CompilerSet(''.join(eids), **compilers)
