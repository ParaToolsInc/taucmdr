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

import model
from target import Target
from application import Application
from measurement import Measurement
from experiment import Experiment
from project import Project


# Index model classes by name
MODELS = dict([(cls.__name__, cls) for cls in 
               [Target, Application, Measurement, Project, Experiment]])

def __getPropsModelName(props):
  try:
    return props['model']
  except KeyError:
    return props['collection']

def __modelInit():
  # Set cls.model_name
  for cls_name, cls in MODELS.iteritems():
    cls.model_name = cls_name
  
  # Set cls.associations
  for cls_name, cls in MODELS.iteritems():
    if not hasattr(cls, 'associations'):
      cls.associations = {}
      
    for attr, props in cls.attributes.iteritems():
      via = props.get('via', None)   
      try:
        foreign_name = __getPropsModelName(props)
      except KeyError:
        if via:
          raise model.ModelError(cls, "Attribute '%s' defines 'via' property "
                                 "but not 'model' or 'collection'" % attr)
        else:
          continue
      
      try:
        foreign_cls = MODELS[foreign_name]
      except KeyError:
        raise model.ModelError(cls, "Invalid model name in attribute '%s'" % attr)
      if not hasattr(foreign_cls, 'associations'):
        foreign_cls.associations = {}
        
      forward = (foreign_cls, via)
      reverse = (cls, attr)
      foreign_cls.associations[via] = reverse
  
      if via:
        try:
          via_props = foreign_cls.attributes[via]
        except KeyError:
          raise model.ModelError(cls, "Found 'via' on undefined attribute '%s.%s'" % 
                                 (foreign_name, via))
        try:
          via_attr_model_name = __getPropsModelName(via_props)
        except KeyError:
          raise model.ModelError(cls, "Found 'via' on non-model attribute '%s.%s'" % 
                                 (foreign_name, via))
        if via_attr_model_name != cls_name:
          raise model.ModelError(cls, "Attribute %s.%s referenced by 'via' in '%s' "
                                 "does not defile 'collection' or 'model' of type '%s'" % 
                                 (foreign_name, via, attr, cls_name))
        try:
          existing = cls.associations[attr]
        except KeyError:
          cls.associations[attr] = forward
        else:
          if existing != forward:
            raise model.ModelError(cls, 
                                   "Conflicting associations on attribute '%s': " 
                                   "%r vs. %r" % (attr, existing, forward))
  
  
# Make it so
__modelInit()

# Clean up
del __getPropsModelName
del __modelInit
