#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
#This file is part of TAU Commander
#
#@section COPYRIGHT
#
#Copyright (c) 2015, ParaTools, Inc.
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice, 
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice, 
#     this list of conditions and the following disclaimer in the documentation 
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
#     be used to endorse or promote products derived from this software without 
#     specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#"""

# System modules
import os
import string
import shutil

# TAU modules
import util
import error
import environment as env
import controller as ctl


class Project(ctl.Controller, ctl.ByName):
  """
  Project data model controller
  """
  
  attributes = {
    'name': {
      'type': 'string',
      'unique': True,
      'argparse': {'help': 'Project name',
                   'metavar': '<project_name>'}
    },
    'targets': {
      'collection': 'Target',
      'via': 'projects',
    },
    'applications': {
      'collection': 'Application',
      'via': 'projects',
    },
    'measurements': {
      'collection': 'Measurement',
      'via': 'projects',
    },
    'experiments': {
      'collection': 'Experiment',
      'via': 'project'
    },
    'prefix': {
      'type': 'string',
      'required': True,
      'defaultsTo': env.USER_PREFIX,
      'argparse': {'flags': ('--home',),
                   'help': 'Location for all files and experiment data related to this project',
                   'metavar': 'path'}
    },
  }

  _valid_name = set(string.digits + string.letters + '-_.')
  
  def prefix(self):
    return os.path.join(self['prefix'], self['name'])
  
  def onCreate(self):
    if set(self['name']) > Project._valid_name:
      raise ctl.ModelError('%r is not a valid project name.' % self['name'],
                           'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
    prefix = self.prefix()
    try:
      util.mkdirp(prefix)
    except Exception as err:
      raise error.ConfigurationError('Cannot create directory %r: %s' % (prefix, err), 
                                     'Check that you have `write` access')

  def onDelete(self):
    prefix = self.prefix()
    try:
      shutil.rmtree(prefix)
    except Exception as err:
      if os.path.exists(prefix):
        LOGGER.error("Could not remove project data at '%s': %s" % (prefix, err))