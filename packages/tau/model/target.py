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
import string

# TAU modules
import cf.tau
import cf.pdt
import cf.bfd
import cf.libunwind
import logger
import controller as ctl
import arguments as args


LOGGER = logger.getLogger(__name__)


class Target(ctl.Controller, ctl.ByName):
  """
  Target data model controller
  """
  
  attributes = {
    'projects': {
      'collection': 'Project',
      'via': 'targets'
    },
    'compilers': {
      'collection': 'Compiler',
      'via': 'target'
    },
    'name': {
      'type': 'string',
      'unique': True,
      'argparse': (('name',), 
                   {'help': 'Target configuration name',
                    'metavar': '<target_name>'})
    },
    'host_os': {
      'type': 'string',
      'required': True,
      'argparse': (('--host-os',), 
                   {'help': 'Host operating system',
                    'metavar': 'os',
                    'default': cf.tau.DEFAULT_HOST_OS or args.SUPPRESS})
    },
    'host_arch': {
      'type': 'string',
      'required': True,
      'argparse': (('--host-arch',), 
                   {'help': 'Host architecture',
                    'metavar': 'arch',
                    'default': cf.tau.DEFAULT_HOST_ARCH or args.SUPPRESS})
    },
    'device_arch': {
      'type': 'string',
      'argparse': (('--device-arch',), 
                   {'help': 'Coprocessor architecture',
                    'metavar': 'arch',
                    'default': cf.tau.DEFAULT_DEVICE_ARCH or args.SUPPRESS})
    },
    'cuda': {
      'type': 'string',
      'required': True,
      'argparse': (('--with-cuda',), 
                   {'help': 'Path to NVIDIA CUDA installation',
                    'metavar': '<path>',
                    'dest': 'cuda',
                    'default': '/usr/local/cuda'})
    },
    'tau': {
      'type': 'string',
      'required': True,
      'argparse': (('--with-tau',), 
                   {'help': 'URL or path to an existing TAU installation or archive file',
                    'metavar': '(<path>|<url>|"download")',
                    'dest': 'tau',
                    'default': cf.tau.DEFAULT_SOURCE})
    },
    'pdt': {
      'type': 'string',
      'argparse': (('--with-pdt',), 
                   {'help': 'URL or path to an existing PDT installation or archive file',
                    'metavar': '(<path>|<url>|"download")',
                    'dest': 'pdt',
                    'default': cf.pdt.DEFAULT_SOURCE})
    },
    'bfd': {
      'type': 'string',
      'argparse': (('--with-bfd',), 
                   {'help': 'URL or path to an existing BfD installation or archive file',
                    'metavar': '(<path>|<url>|"download")',
                    'dest': 'bfd',
                    'default': cf.bfd.DEFAULT_SOURCE})
    },
    'libunwind': {
      'type': 'string',
      'argparse': (('--with-libunwind',), 
                   {'help': 'URL or path to an existing LIBUNWIND installation or archive file',
                    'metavar': '(<path>|<url>|"download")',
                    'dest': 'libunwind',
                    'default': cf.libunwind.DEFAULT_SOURCE})
    },


  }
  
  _valid_name = set(string.digits + string.letters + '-_.')
  
  def onCreate(self):
    if set(self['name']) > Target._valid_name:
      raise ctl.ModelError('%r is not a valid target name.' % self['name'],
                           'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
