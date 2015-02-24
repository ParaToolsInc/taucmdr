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

# TAU modules
import cf.tau
import logger
import settings
import error
import controller
import util
from model.project import Project
from model.target import Target


LOGGER = logger.getLogger(__name__)


class Experiment(controller.Controller):
  """
  Experiment data model controller
  """
  
  attributes = {
    'project': {
      'model': 'Project',
      'required': True,
    },
    'target': {
      'model': 'Target',
      'required': True,
    },
    'application': {
      'model': 'Application',
      'required': True,
    },
    'measurement': {
      'model': 'Measurement',
      'required': True,
    },
    'trials': {
      'collection': 'Trial',
      'via': 'experiment'
    },
  }
  
  def onCreate(self):
    pass
  
  def onDelete(self):
    if self.isSelected():
      settings.unset('experiment_id')
  
  def select(self):
    if not self.eid:
      raise error.InternalError('Tried to select an experiment without an eid')
    settings.set('experiment_id', self.eid)
  
  def isSelected(self):
    if self.eid:
      return settings.get('experiment_id') == self.eid
    return False
  
  @classmethod
  def getSelected(cls):
    experiment_id = settings.get('experiment_id')
    if experiment_id:
      experiment = cls.one(eid=experiment_id)
      if not experiment:
        raise error.InternalError('Invalid experiment ID: %r' % experiment_id)
      return experiment
    return None
  
  def bootstrap(self, compiler_cmd):
    """
    Installs all software required to perform the experiment
    """
    self.populate()
    prefix = self['project']['prefix']
    try:
      util.mkdirp(prefix)
    except:
      raise error.ConfigurationError('Cannot create directory %r' % prefix, 
                                     'Check that you have `write` access')
    target = self['target']
    tau_src = target['tau']
    arch = target['host_arch']
    cf.tau.initialize(prefix, tau_src, arch=arch, compiler_cmd=compiler_cmd)
