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
from logger import getLogger
from model import Model, ModelError
from arguments import ParseBooleanAction, SUPPRESS


LOGGER = getLogger(__name__)


class Measurement(Model):
  """
  Measurement data model
  """
  
  model_name = 'measurement'
  
  attributes = {
    'projects': {
      'collection': 'Project',
      'via': 'measurements'
    },
    'name': {
      'type': 'string',
      'required': True,
      'unique': True,
      'argparse': (('name',), 
                   {'help': 'Measurement configuration name',
                    'metavar': '<measurement_name>'})

    },
    'profile': {
      'type': 'boolean',
      'defaultsTo': True,
      'argparse': (('--profile',), 
                   {'help': 'Gather application profiles',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': True,
                    'action': ParseBooleanAction})
    },
    'trace': {
      'type': 'boolean',
      'defaultsTo': True,
      'argparse': (('--trace',), 
                   {'help': 'Gather application traces',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': False,
                    'action': ParseBooleanAction})
    },
    'sample': {
      'type': 'boolean',
      'defaultsTo': True,
      'argparse': (('--sample',), 
                   {'help': 'Gather application program counter samples',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': False,
                    'action': ParseBooleanAction})
    },
    'source_inst': {
      'type': 'boolean',
      'defaultsTo': True,
      'argparse': (('--source_inst',), 
                   {'help': 'Use source code parsing to instrument the application',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': True,
                    'action': ParseBooleanAction})
    },
    'compiler_inst': {
      'type': 'string',
      'argparse': (('--compiler_inst',), 
                   {'help': 'Use compiler callbacks to instrument the application',
                    'metavar': '<mode>',
                    'nargs': '?',
                    'const': 'always',
                    'default': 'fallback',
                    'choices': ['always', 'fallback', 'never']})
    },
    'mpi': {
      'type': 'boolean',
      'defaultsTo': False,
      'argparse': (('--mpi',), 
                   {'help': 'Measure time spent in MPI methods',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': False,
                    'action': ParseBooleanAction})
    },
    'openmp': {
      'type': 'string',
      'argparse': (('--openmp',), 
                   {'help': 'Method used to measure time spent in OpenMP directives',
                    'metavar': '<method>',
                    'nargs': '?',
                    'const': 'opari',
                    'default': 'ignore',
                    'choices': ['ignore', 'opari', 'ompt']})
    },
    'callpath': {
      'type': 'integer',
      'defaultsTo': 2,
      'argparse': (('--callpath',), 
                   {'help': 'Set maximum depth of callpath recording',
                    'metavar': '<depth>',
                    'nargs': '?',
                    'const': 2,
                    'default': 0,
                    'type': int})
    },
    'memory_use': {
      'type': 'boolean',
      'defaultsTo': False,
      'argparse': (('--memory_use',), 
                   {'help': 'Measure memory consumption',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': False,
                    'action': ParseBooleanAction})
    },
    'memory_alloc': {
      'type': 'boolean',
      'defaultsTo': False,
      'argparse': (('--memory_alloc',), 
                   {'help': 'Record memory allocation and deallocation events',
                    'metavar': '<flag>',
                    'nargs': '?',
                    'const': True,
                    'default': False,
                    'action': ParseBooleanAction})
    },
  }
  
  _valid_name = set(string.digits + string.letters + '-_.')
  
  def onCreate(self):
    if set(self.name) > Measurement._valid_name:
      raise ModelError('%r is not a valid measurement name.' % self.name,
                       'Use only letters, numbers, dot (.), dash (-), and underscore (_).')

