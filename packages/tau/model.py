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
        

class ModelKeyError(ModelError):
  def __init__(self, model_cls, unique):
    super(ModelKeyError, self).__init__(
            model_cls, 'A record with one of %r already exists' % unique)


class ModelAssociationError(ModelError):
  def __init__(self, model_cls, attr):
    super(ModelAssociationError, self).__init__(
            'Invalid association: %r' % attr)


class Model(object):
  """
  The "M" in MVC
  """
  
  enforce_schema = True
  
  def __init__(self, data):
    self.__dict__.update(self._validate(data))
    self.onCreate()

  def __repr__(self):
    return json.dumps(self.data())
  
  def onCreate(self):
    pass
  
  def data(self):
    """
    Returns model data fields as a dictionary
    """
    data = {}
    for name in self.attributes.iterkeys():
      try:
        data[name] = getattr(self, name)
      except AttributeError:
        pass
    return data

  def primaryKey(self):
    """
    Returns the value of the primary key field or None if no primary key defined
    """
    return getattr(self, self.primary_key, None)
  
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
  def withPrimaryKey(cls, key):
    """
    Return the record with the given primary key
    """
    try:
      return cls(storage.search(cls.model_name, {cls.primary_key: key})[0])
    except IndexError:
      raise ModelError(cls, 'Primary key (%r == %r) does not exist' % 
                       (cls.primary_key, key))

  @classmethod
  def create(cls, fields):
    """
    Store a new model record
    """
    model = cls(fields)
    unique = dict([(attr, getattr(model, attr)) 
                   for attr, _ in cls.uniqueAttributes()])
    if storage.contains(cls.model_name, unique):
      raise ModelKeyError(cls, unique)

    # Update N-N and N-1 relationships
    for attr, props in cls.attributesWith('collection'):
      via = props['via']
      foreign_cls = getModel(props['collection'])
      foreign_keys = getattr(model, attr)
      for foreign_key in foreign_keys:
        foreign_model = foreign_cls.withPrimaryKey(foreign_key)
        if 'model' in foreign_cls.attributes[via]:
          updated_keys = model.primaryKey()
        elif 'collection' in foreign_cls.attributes[via]:
          updated_keys = getattr(foreign_model, via)
          updated_keys.append(model.primaryKey())
        storage.update(foreign_cls.model_name,
                       {foreign_cls.primary_key: foreign_model.primaryKey()},
                       {via: updated_keys})
    
    # Update 1-N and 1-1 relationships
    for attr, props in cls.attributesWith('model'):
      via = props['via']
      foreign_cls = getModel(props['model'])
      foreign_key = getattr(model, attr)
      foreign_model = foreign_cls.withPrimaryKey(foreign_key)
      if 'model' in foreign_cls.attributes[via]:
        updated_keys = model.primaryKey()
      elif 'collection' in foreign_cls.attributes[via]:
        updated_keys = getattr(foreign_model, via)
        updated_keys.append(model.primaryKey())
      storage.update(foreign_cls.model_name,
                     {foreign_cls.primary_key: foreign_model.primaryKey()},
                     {via: updated_keys})

    return storage.insert(cls.model_name, model.data())
  
  @classmethod
  def update(cls, keys, fields):
    """
    Change the fields of all records that match the given keys
    """
    return storage.update(cls.model_name, keys, fields)
  
  @classmethod
  def delete(cls, keys):
    """
    Delete the records that match the given keys
    """
    for model in cls.search(keys):
      # Update N-N and N-1 relationships
      for attr, props in cls.attributesWith('collection'):
        via = props['via']
        foreign_cls = getModel(props['collection'])
        foreign_keys = getattr(model, attr)
        for foreign_key in foreign_keys:
          foreign_model = foreign_cls.withPrimaryKey(foreign_key)
          if 'model' in foreign_cls.attributes[via]:
            updated_keys = None
          elif 'collection' in foreign_cls.attributes[via]:
            updated_keys = list(set(getattr(foreign_model, via)) - set(model.primaryKey()))
          storage.update(foreign_cls.model_name,
                         {foreign_cls.primary_key: foreign_model.primaryKey()},
                         {via: updated_keys})
      
      # Update 1-N and 1-1 relationships
      for attr, props in cls.attributesWith('model'):
        via = props['via']
        foreign_cls = getModel(props['model'])
        foreign_key = getattr(model, attr)
        foreign_model = foreign_cls.withPrimaryKey(foreign_key)
        if 'model' in foreign_cls.attributes[via]:
          updated_keys = None
        elif 'collection' in foreign_cls.attributes[via]:
          updated_keys = list(set(getattr(foreign_model, via)) - set(model.primaryKey()))
        storage.update(foreign_cls.model_name,
                       {foreign_cls.primary_key: foreign_model.primaryKey()},
                       {via: updated_keys})
    
    return storage.remove(cls.model_name, keys)
  
  @classmethod
  def attributesWith(cls, property):
    """
    Yield attributes that have the specified property
    """
    for i in cls.attributes.iteritems():
      if i[1].get(property, False):
        yield i

  @classmethod
  def uniqueAttributes(cls):
    """
    Yield attributes that must have unique values
    """
    primary_key = getattr(cls, 'primary_key', None)
    for i in cls.attributes.iteritems():
      if primary_key and i[0] == primary_key:
        yield i
      else:
        try:
          attr_val = i[1]['unique']
        except KeyError:
          continue
        else:
          if attr_val:
            yield i

  @classmethod
  def requiredAttributes(cls):
    """
    Yield attributes that must have values
    """
    primary_key = getattr(cls, 'primary_key', None)
    for i in cls.attributes.iteritems():
      if primary_key and i[0] == primary_key:
        yield i
      else:
        try:
          attr_val = i[1]['required']
        except KeyError:
          continue
        else:
          if attr_val:
            yield i



class ByID(object):
  """
  Mixin for a model with a unique 'id' field
  """
  primary_key = 'id'
  
  @classmethod
  def withId(cls, id):
    try:
      return cls.search({'id': id})[0]
    except IndexError:
      return None


class ByName(object):
  """
  Mixin for a model with a unique 'name' field
  """
  primary_key = 'name'
  
  @classmethod
  def withName(cls, name):
    try:
      return cls.search({'name': name})[0]
    except IndexError:
      return None
    
    
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