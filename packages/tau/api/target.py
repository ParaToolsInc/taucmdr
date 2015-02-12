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
from logger import getLogger
from model import Model, ModelError
from arguments import SUPPRESS


LOGGER = getLogger(__name__)


def detectDefaultHostOS():
  """
  Detect the default host operating system
  """
  return platform.system()
  

def detectDefaultHostArch():
    """
    Use TAU's archfind script to detect the host target architecture
    """
    here = os.path.dirname(os.path.realpath(__file__))
    cmd = os.path.join(os.path.dirname(here), 'util', 'archfind', 'archfind')
    print cmd
    return subprocess.check_output(cmd).strip()


def detectDefaultDeviceArch():
  """
  Detect coprocessors
  """
  return SUPPRESS


class Target(Model):
  """
  Target data model
  """
  
  model_name = 'target'
  
  attributes = {
    'projects': {
      'collection': 'Project',
      'via': 'targets'
    },
    'name': {
      'type': 'string',
      'required': True,
      'unique': True,
      'argparse': (('name',), 
                   {'help': 'Target configuration name',
                    'metavar': '<target_name>'})
    },
    'host_os': {
      'type': 'string',
      'required': True,
      'argparse': (('--host_os',), 
                   {'help': 'Host operating system',
                    'metavar': '<os>',
                    'default': detectDefaultHostOS()})
    },
    'host_arch': {
      'type': 'string',
      'required': True,
      'argparse': (('--host_arch',), 
                   {'help': 'Host architecture',
                    'metavar': '<arch>',
                    'default': detectDefaultHostArch()})
    },
    'device_arch': {
      'type': 'string',
      'argparse': (('--device_arch',), 
                   {'help': 'Coprocessor architecture',
                    'metavar': '<arch>',
                    'default': detectDefaultDeviceArch()})
    },
    'compilers': {
      'collection': 'Compiler',
      'via': 'target'
    },
    'packages': {
      'collection': 'Package',
      'via': 'target'
    }
  }
  
  _valid_name = set(string.digits + string.letters + '-_.')
  
  def onCreate(self):
    if set(self.name) > Target._valid_name:
      raise ModelError('%r is not a valid target name.' % self.name,
                       'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
