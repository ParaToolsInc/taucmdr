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
import string
import platform
import subprocess
from tau import logger
from tau.arguments import ParsePackagePathAction
from tau.controller import Controller, ByName, ModelError
from tau.error import ConfigurationError


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


def cc_default():
    """
    Detect target's default C compiler
    """
    # TODO
    return 'gcc'


def cxx_default():
    """
    Detect target's default C compiler
    """
    # TODO
    return 'g++'


def fc_default():
    """
    Detect target's default C compiler
    """
    # TODO
    return 'gfortran'

def libunwind_default():
    if host_arch_default() == 'apple':
        return None
    else:
        return 'default'


class Target(Controller, ByName):

    """
    Target data model controller
    """

    attributes = {
        'projects': {
            'collection': 'Project',
            'via': 'targets'
        },
        'name': {
            'type': 'string',
            'unique': True,
            'argparse': {'help': 'Target configuration name',
                         'metavar': '<target_name>'}
        },
        'host_os': {
            'type': 'string',
            'required': True,
            'defaultsTo': host_os_default(),
            'argparse': {'flags': ('--host-os',),
                         'group': 'target system',
                         'help': 'Host operating system',
                         'metavar': 'os'}
        }, 
        'host_arch': {
            'type': 'string',
            'required': True,
            'defaultsTo': host_arch_default(),
            'argparse': {'flags': ('--host-arch',),
                         'group': 'target system',
                         'help': 'Host architecture',
                         'metavar': 'arch'}
        },
        'device_arch': {
            'type': 'string',
            'defaultsTo': device_arch_default(),
            'argparse': {'flags': ('--device-arch',),
                         'group': 'target system',
                         'help': 'Coprocessor architecture',
                         'metavar': 'arch'}
        },
        'CC': {
            'model': 'Compiler',
            'required': True,
            'defaultsTo': cc_default(),
            'argparse': {'flags': ('--cc',),
                         'group': 'compiler',
                         'help': 'C Compiler',
                         'metavar': '<command>'}
        },
        'CXX': {
            'model': 'Compiler',
            'required': True,
            'defaultsTo': cxx_default(),
            'argparse': {'flags': ('--cxx', '--c++'),
                         'group': 'compiler',
                         'help': 'C++ Compiler',
                         'metavar': '<command>'}
        },
        'FC': {
            'model': 'Compiler',
            'required': True,
            'defaultsTo': fc_default(),
            'argparse': {'flags': ('--fc', '--fortran'),
                         'group': 'compiler',
                         'help': 'Fortran Compiler',
                         'metavar': '<command>'}
        },
        'cuda': {
            'type': 'string',
            'defaultsTo': None,
            'argparse': {'flags': ('--with-cuda',),
                         'group': 'software package',
                         'help': 'Path to NVIDIA CUDA installation',
                         'metavar': '<path>',
                         'action': ParsePackagePathAction},
        },
        'tau_source': {
            'type': 'string',
            'defaultsTo': 'download',
            'argparse': {'flags': ('--with-tau',),
                         'group': 'software package',
                         'help': 'URL or path to a TAU installation or archive file',
                         'metavar': '(<path>|<url>|download)',
                         'action': ParsePackagePathAction}
        },
        'pdt_source': {
            'type': 'string',
            'defaultsTo': 'download',
            'argparse': {'flags': ('--with-pdt',),
                         'group': 'software package',
                         'help': 'URL or path to a PDT installation or archive file',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction},
        },
        'bfd_source': {
            'type': 'string',
            'defaultsTo': 'download',
            'argparse': {'flags': ('--with-bfd',),
                         'group': 'software package',
                         'help': 'URL or path to a BFD installation or archive file',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        },
        'libunwind_source': {
            'type': 'string',
            'defaultsTo': libunwind_default(),
            'argparse': {'flags': ('--with-libunwind',),
                         'group': 'software package',
                         'help': 'URL or path to a libunwind installation or archive file',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        },
        'papi_source': {
            'type': 'string',
            'defaultsTo': None,
            'argparse': {'flags': ('--with-papi',),
                         'group': 'software package',
                         'help': 'URL or path to a PAPI installation or archive file',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        },
        'scorep_source': {
            'type': 'string',
            'defaultsTo': None,
            'argparse': {'flags': ('--with-score-p',),
                         'group': 'software package',
                         'help': 'URL or path to a Score-P installation or archive file',
                         'metavar': '(<path>|<url>|download|None)',
                         'action': ParsePackagePathAction}
        }
    }

    _valid_name = set(string.digits + string.letters + '-_.')

    def onCreate(self):
        if set(self['name']) > Target._valid_name:
            raise ModelError('%r is not a valid target name.' % self['name'],
                             'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
        if self['libunwind_source'] and self['host_arch'] == 'apple':
            libunwind_flag = self.attributes['libunwind_source']['argparse']['flags'][0]
            raise ConfigurationError("libunwind not supported on host architecture 'apple'",
                                     "Use %s=None" % libunwind_flag)
