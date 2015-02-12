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
import sys
import json

# TAU modules
import storage
from tau import HELP_CONTACT, EXIT_FAILURE
from logger import getLogger
from error import ConfigurationError
from docutils.nodes import field


LOGGER = getLogger(__name__)


class ModelError(ConfigurationError):
    """
    Indicates that invalid model data was given.
    """
    def __init__(self, value, hint="Try 'tau project --help'."):
        super(ModelError, self).__init__(value)
        self.hint = hint

    def handle(self):
        hint = 'Hint: %s\n' % self.hint if self.hint else ''
        message = """
%(value)s

%(hint)s

TAU cannot proceed with the given inputs.
Please review the input files and command line parameters
or contact %(contact)s for assistance.""" % {'value': self.value, 
                                             'hint': hint, 
                                             'contact': HELP_CONTACT}
        LOGGER.critical(message)
        sys.exit(EXIT_FAILURE)


class Model(object):
  """
  The "M" in MVC
  """
  def __init__(self, data):
    self.__dict__.update(self._validate(data))
    self.onCreate()

  def __repr__(self):
    return json.dumps(self.data())
  
  def onCreate(self):
    pass
  
  def onUpdate(self):
    pass

  def data(self):
    data = {}
    for name in self.attributes.iterkeys():
      try:
        data[name] = getattr(self, name)
      except AttributeError:
        pass
    return data
  
  @classmethod
  def _validate(cls, data, raise_on_nonschema=True):
    """
    Validates the given data against the model schema
    A new dictionary containing validated data is returned
    """
    validated = {}
    for attr, desc in cls.attributes.iteritems():
      # Check required fields
      if desc.get('required', False):
        try:
          validated[attr] = data[attr]
        except KeyError:
          raise ModelError('%r is required' % attr)
        else: 
          continue
      # Apply defaults
      try:
        default = desc['defaultsTo']
      except KeyError:
        pass
      else:
        validated[attr] = data.get(attr, default)
        continue
      # Empty collections are an empty list 
      if desc.get('collection', False):
        value = data.get(attr, [])
        validated[attr] = value if value else [] 
      # Flag non-schema fields and ignore `None` fields
      try:
        value = data[attr]
      except KeyError:
        pass
      else:
        if value != None:
          validated[attr] = value
    if raise_on_nonschema:
      for key in data:
        if not key in cls.attributes:
          raise ModelError('Data field %r not described in %s schema' % (key, cls.model_name))
    return validated

  @classmethod
  def create(cls, fields):
    """
    Store a new model record
    """
    return storage.insert(cls.model_name, cls(fields))
  
  @classmethod
  def search(cls, keys=None):
    """
    Return a list of records matching the given keys
    """
    return [cls(result) for result in storage.search(cls.model_name, keys)]
  
  @classmethod
  def exists(cls, keys=None):
    """
    Return true if a record matching the given keys exists
    """
    return storage.contains(cls.model_name, keys)

  @classmethod
  def edit(cls, keys, fields):
    """
    Change the fields of the record that match the given keys
    """
    return storage.update(cls.model_name, keys, fields)
  
  @classmethod
  def delete(cls, keys):
    """
    Delete the records that match the given keys
    """
    return storage.remove(cls.model_name, keys)


class ByName(object):
  """
  Mixin for a model with a unique 'name' field
  """
  @classmethod
  def named(cls, name):
    try:
      return cls.search({'name': name})[0]
    except IndexError:
      return None