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
from UserDict import IterableUserDict

# TAU modules
from tau import HELP_CONTACT, EXIT_FAILURE
from logger import getLogger
from error import InternalError
from storage import user_storage as storage


LOGGER = getLogger(__name__)


class ModelError(InternalError):
  """
  Indicates that invalid model data was given.
  """
  def __init__(self, model_cls, value):
    super(ModelError, self).__init__(value)
    self.model_cls = model_cls

  def handle(self):
    message = """
Error in model %(model_name)s:
%(value)s

This is a bug in TAU. 
Please contact %(contact)s for assistance.""" % {'model_name': self.model_cls.model_name,
                                                 'value': self.value, 
                                                 'contact': HELP_CONTACT}
    LOGGER.critical(message)
    sys.exit(EXIT_FAILURE)
        

class UniqueAttributeError(ModelError):
  def __init__(self, model_cls, unique):
    super(UniqueAttributeError, self).__init__(
            model_cls, 'A record with one of %r already exists' % unique)



class Model(object, IterableUserDict):
  """
  The "M" in MVC
  """
  
  enforce_schema = True
  
  def onCreate(self): pass
  
  def __init__(self, fields):
    self.eid = getattr(fields, 'eid', None)
    self.data = self._validate(fields)
    self.onCreate()

  def __repr__(self):
    return json.dumps(self.data)
  
  def populate(self):
    """
    Populates associated attributes
    """
    for attr, props in (self.attributesWith('collection', 'model')):
      foreign_model = getModel(props['collection'])
      self[attr] = [foreign_model.get(eid=eid) for eid in self[attr]]
  
  @classmethod
  def _validate(cls, data):
    """
    Validates the given data against the model schema
    A new dictionary containing validated data is returned
    """
    validated = {}
    for attr, props in cls.attributes.iteritems():
      # Check required fields
      if props.get('required', False):
        try:
          validated[attr] = data[attr]
        except KeyError:
          raise ModelError(cls, '%r is required' % attr)
        else: 
          continue
      # Apply defaults
      try:
        default = props['defaultsTo']
      except KeyError:
        pass
      else:
        validated[attr] = data.get(attr, default)
        continue
      # Check model associations 
      try:
        collection_type = props['collection']
      except KeyError:
        pass
      else: 
        collection_model = getModel(collection_type)
        try:
          via = props['via']
        except KeyError:
          if collection_model:
            raise ModelError(cls, "'collection(%r)' does not define 'via' in %r" % 
                             (collection_type, cls.model_name))
        else:
          if not collection_model:
            raise ModelError(cls, "'collection(%r)' defines 'via' on non-model in %r" % 
                             (collection_type, cls.model_name))
          try:
            via_attr = collection_model.attributes[via]
          except KeyError:
            raise ModelError(cls, "'collection(%r)' defines 'via' on undefined attribute %s.attributes.%s in %r" % 
                             (collection_type, collection_model.__name__, via, cls.model_name))
          else:
            if not ('model' in via_attr or 'collection' in via_attr):
              raise ModelError(cls, "'collection(%r)' defines 'via' on non-model attribute %s.attributes.%s in %r" % 
                               (collection_type, collection_model.__name__, via, cls.model_name))
        # Empty collections are an empty list
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
    # Enforce schema
    if cls.enforce_schema:
      for key in data:
        if not key in cls.attributes:
          raise ModelError(cls, 'Data field %r not described in %s schema' % (key, cls.model_name))
    return validated
  
  @classmethod
  def get(cls, keys=None, eid=None):
    """
    Returns the record with the given keys or element id
    """
    found = storage.get(cls.model_name, keys, eid)
    return cls(found) if found else None

  @classmethod
  def search(cls, keys=None):
    """
    Return a list of records matching the given keys
    """
    return [cls(result) for result in storage.search(cls.model_name, keys)]
  
  @classmethod
  def exists(cls, keys=None, eids=None):
    """
    Return true if a record matching the given keys exists
    """
    return storage.contains(cls.model_name, keys, eids)
  
  @classmethod
  def create(cls, fields):
    """
    Store a new model record and update associations
    """
    model = cls(fields)
    unique = dict([(attr, model[attr]) 
                   for attr, _ in cls.attributesWith('unique')])
    if storage.contains(cls.model_name, unique):
      raise UniqueAttributeError(cls, unique)
    
    model.eid = storage.insert(cls.model_name, model.data)
    for attr, props in (cls.attributesWith('collection', 'model')):
      via = props['via']
      foreign_model = getModel(props['collection'])
      foreign_keys = model[attr]
      for foreign_key in foreign_keys:
        associated = foreign_model.get(eid=foreign_key)
        if not associated:
          raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
        if 'model' in associated.attributes[via]:
          updated_keys = [model.eid]
        elif 'collection' in associated.attributes[via]:
          updated_keys = list(set(associated[via] + [model.eid]))
        storage.update(foreign_model.model_name, {via: updated_keys}, eids=[foreign_key])
    return model.eid
  
  @classmethod
  def update(cls, fields, keys):
    """
    Change the fields of all records that match the given keys
    and update associations
    """
    for model in cls.search(keys):
      for attr, props in (cls.attributesWith('collection', 'model')):
        try:
          new_foreign_keys = set(fields[attr])
        except KeyError:
          continue
        else:
          via = props['via']
          foreign_model = getModel(props['collection'])
          old_foreign_keys = set(model[attr])
          added = new_foreign_keys - old_foreign_keys
          deled = old_foreign_keys - new_foreign_keys
          for foreign_key in added:
            associated = foreign_model.get(eid=foreign_key)
            if not associated:
              raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
            if 'model' in associated.attributes[via]:
              updated_keys = [model.eid]
            elif 'collection' in associated.attributes[via]:
              updated_keys = list(set(associated[via] + [model.eid]))
            storage.update(foreign_model.model_name, {via: updated_keys}, eids=[foreign_key])
          for foreign_key in deled:
            associated = foreign_model.get(eid=foreign_key)
            if not associated:
              raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
            if 'model' in associated.attributes[via]:
              updated_keys = []
            elif 'collection' in associated.attributes[via]:
              updated_keys = list(set(associated[via]) - set([model.eid]))
            storage.update(foreign_model.model_name, {via: updated_keys}, eids=[foreign_key])
    return storage.update(cls.model_name, fields, keys)
  
  @classmethod
  def delete(cls, keys):
    """
    Delete the records that match the given keys and update associations
    """
    for model in cls.search(keys):
      for attr, props in (cls.attributesWith('collection', 'model')):
        via = props['via']
        foreign_model = getModel(props['collection'])
        foreign_keys = model[attr]
        for foreign_key in foreign_keys:
          associated = foreign_model.get(eid=foreign_key)
          if not associated:
            raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
          if 'model' in associated.attributes[via]:
            updated_keys = []
          elif 'collection' in associated.attributes[via]:
            updated_keys = list(set(associated[via]) - set([model.eid]))
          storage.update(foreign_model.model_name, {via: updated_keys}, eids=[foreign_key])
    return storage.remove(cls.model_name, keys)
  
  @classmethod
  def attributesWith(cls, *args):
    """
    Yield attributes that have the specified property
    """
    for i in cls.attributes.iteritems():
      for property in args:
        if i[1].get(property, False):
          yield i


class ByName(object):
  """
  Mixin for a model with a unique 'name' field
  """
  @classmethod
  def withName(cls, name):
    return cls.get({'name': name})
    
    
def getModel(name):
  """
  Returns the named model class or None if no such model exists
  """
  module_name = '.'.join(['tau', 'api', name.lower()])
  class_name = name.lower().capitalize()
  try:
    module = __import__(module_name, globals(), locals(), [class_name], -1)
  except ImportError:
    return None
  else:
    return getattr(module, class_name, None)