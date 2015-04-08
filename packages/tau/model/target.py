"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# System modules
import os
import string
import platform
import subprocess

# TAU modules
import logger
import controller as ctl
import arguments as args


LOGGER = logger.getLogger(__name__)


def defaultHostOS():
  """
  Detect the default host operating system
  """
  return platform.system()

def defaultHostArch():
    """
    Use TAU's archfind script to detect the host target architecture
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cmd = os.path.join(os.path.dirname(here), 'util', 'archfind', 'archfind')
    return subprocess.check_output(cmd).strip()

def defaultDeviceArch():
  """
  Detect coprocessors
  """
  # TODO
  return None

def defaultCC():
  """
  Detect target's default C compiler
  """
  # TODO
  return 'gcc'

def defaultCXX():
  """
  Detect target's default C compiler
  """
  # TODO
  return 'g++'

def defaultFC():
  """
  Detect target's default C compiler
  """
  # TODO
  return 'gfortran'


class Target(ctl.Controller, ctl.ByName):
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
      'defaultsTo': defaultHostOS(),
      'argparse': {'flags': ('--host-os',),
                   'group': 'target system',
                   'help': 'Host operating system',
                   'metavar': 'os'}
    },
    'host_arch': {
      'type': 'string',
      'required': True,
      'defaultsTo': defaultHostArch(),
      'argparse': {'flags': ('--host-arch',),
                   'group': 'target system',
                   'help': 'Host architecture',
                   'metavar': 'arch'}
    },
    'device_arch': {
      'type': 'string',
      'defaultsTo': defaultDeviceArch(),
      'argparse': {'flags': ('--device-arch',),
                   'group': 'target system',
                   'help': 'Coprocessor architecture',
                   'metavar': 'arch'}
    },
    'CC': {
      'model': 'Compiler',
      'required': True,
      'defaultsTo': defaultCC(),
      'argparse': {'flags': ('--cc',),
                   'group': 'compiler',
                   'help': 'C Compiler',
                   'metavar': '<command>'}
    },
    'CXX': {
      'model': 'Compiler',
      'required': True,
      'defaultsTo': defaultCXX(),
      'argparse': {'flags': ('--cxx','--c++'),
                   'group': 'compiler',
                   'help': 'C++ Compiler',
                   'metavar': '<command>'}
    },
    'FC': {
      'model': 'Compiler',
      'required': True,
      'defaultsTo': defaultFC(),
      'argparse': {'flags': ('--fc','--fortran'),
                   'group': 'compiler',
                   'help': 'Fortran Compiler',
                   'metavar': '<command>'}
    },
    'cuda': {
      'type': 'string',
      'argparse': {'flags': ('--with-cuda',),
                   'group': 'software package',
                   'help': 'Path to NVIDIA CUDA installation',
                   'metavar': '<path>'}
    },
    'tau_source': {
      'type': 'string',
      'defaultsTo': 'download',
      'argparse': {'flags': ('--with-tau',),
                   'group': 'software package',
                   'help': 'URL or path to a TAU installation or archive file',
                   'metavar': '(<path>|<url>|"download")'}
    },
    'pdt_source': {
      'type': 'string',
      'defaultsTo': 'download',
      'argparse': {'flags': ('--with-pdt',),
                   'group': 'software package',
                   'help': 'URL or path to a PDT installation or archive file',
                   'metavar': '(<path>|<url>|"download")'}
    },
    'bfd_source': {
      'type': 'string',
      'defaultsTo': 'download',
      'argparse': {'flags': ('--with-bfd',),
                   'group': 'software package',
                   'help': 'URL or path to a BFD installation or archive file',
                   'metavar': '(<path>|<url>|"download")'}
    },
    'libunwind_source': {
      'type': 'string',
      'argparse': {'flags': ('--with-libunwind',),
                   'group': 'software package',
                   'help': 'URL or path to a libunwind installation or archive file',
                   'metavar': '(<path>|<url>|"download")'}
    },
    'papi_source': {
      'type': 'string',
      'defaultsTo': 'download',
      'argparse': {'flags': ('--with-papi',),
                   'group': 'software package',
                   'help': 'URL or path to a PAPI installation or archive file',
                   'metavar': '(<path>|<url>|"download")'}
    }
  }
  
  _valid_name = set(string.digits + string.letters + '-_.')
  
  def onCreate(self):
    if set(self['name']) > Target._valid_name:
      raise ctl.ModelError('%r is not a valid target name.' % self['name'],
                           'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
