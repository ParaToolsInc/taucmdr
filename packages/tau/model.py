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
        

class UniqueAttributeError(ModelError):
  def __init__(self, model_cls, unique):
    super(UniqueAttributeError, self).__init__(
            model_cls, 'A record with one of %r already exists' % unique)



class Model(object):
  """
  The "M" in MVC
  """
  
  # Subclasses override for callback
  def onCreate(self): pass
  
  def __init__(self, fields):
    self.eid = getattr(fields, 'eid', None)
    self.data = self._validate(fields)
    self.onCreate()
    
  def __getitem__(self, key):
    return self.data[key]
  
  def get(self, key, default=None):
    return self.data.get(key, default)

  def __repr__(self):
    return json.dumps(self.data)

  @classmethod
  def _validate(cls, data, enforce_schema=True):
    """
    Validates the given data against the model schema
    """
    if data is None:
      return None
    if enforce_schema:
      for key in data:
        if not key in cls.attributes:
          raise ModelError(cls, 'Data field %r not described in %s schema' % (key, cls.model_name))
    validated = {}
    for attr, props in cls.attributes.iteritems():
      #
      # TODO: Check types
      #
      # Check required fields and defaults
      try:
        validated[attr] = data[attr]
      except KeyError:
        if 'required' in props:
          raise ModelError(cls, "'%s' is required but was not defined" % attr)
        elif 'defaultsTo' in props:
          validated[attr] = props['defaultsTo']
      # Check collections
      if 'collection' in props:
        value = data.get(attr, [])
        if not value:
          value = []
        elif not isinstance(value, list):
          raise ModelError(cls, "Value supplied for '%s' is not a list: %r" % (attr, value))
        else:
          for id in value:
            try:
              int(id)
            except ValueError:
              raise ModelError(cls, "Invalid non-integer ID '%s' in '%s'" % (id, attr))
        validated[attr] = value
        continue
      # Check model associations
      if 'model' in props:
        value = data.get(attr, None)
        try:
          if int(value) != value:
            raise ValueError
        except ValueError:
          raise ModelError(cls, "Invalid non-integer ID '%s' in '%s'" % (value, attr))
        validated[attr] = value
        continue
    return validated
  
  def populate(self):
    """
    Populates associated attributes
    """
    from api import MODELS
    for attr, props in self.attributes.iteritems():
      try:
        foreign_model = MODELS[props['model']]
      except KeyError:
        try:
          foreign_model = MODELS[props['collection']]
        except KeyError:
          continue
        else:
          self.data[attr] = foreign_model.search(eids=self[attr])
      else:
        self.data[attr] = foreign_model.one(eid=self[attr])
    return self

  @classmethod
  def one(cls, keys=None, eid=None):
    """
    Returns the record with the given keys or element id
    """
    found = storage.get(cls.model_name, keys, eid)
    return cls(found) if found else None
  
  @classmethod
  def all(cls):
    """
    Returns a list of all records
    """
    return [cls(result) for result in storage.search(cls.model_name)]

  @classmethod
  def search(cls, keys=None, eids=None):
    """
    Return a list of records matching the given keys
    """
    if eids != None:
      return [cls.one(eid=eid) for eid in eids]
    elif keys:
      return [cls(record) for record in storage.search(cls.model_name, keys)]
    else:
      return cls.all()
  
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
                   for attr, props in cls.attributes.iteritems()
                   if 'unique' in props])
    if storage.contains(cls.model_name, unique):
      raise UniqueAttributeError(cls, unique)
    
    model.eid = storage.insert(cls.model_name, model.data)
    for attr, foreign in cls.associations.iteritems():
      if not attr: continue
      foreign_model, via = foreign
      if 'model' in model.attributes[attr]:
        foreign_keys = [model.data[attr]]
      elif 'collection' in model.attributes[attr]:
        foreign_keys = model.data[attr]
      for key in foreign_keys:
        associated = foreign_model.one(eid=key)
        if not associated:
          raise ModelError(foreign_model, "No record with ID '%s'" % key)
        if 'model' in associated.attributes[via]:
          updated_field = model.eid
        elif 'collection' in associated.attributes[via]:
          updated_field = list(set(associated[via] + [model.eid]))
        storage.update(foreign_model.model_name, {via: updated_field}, eids=[key])
    return model
  
  @classmethod
  def update(cls, fields, keys):
    """
    Change the fields of all records that match the given keys
    and update associations
    """
    for model in cls.search(keys):
      for attr, foreign in cls.associations.iteritems():
        try:
          new_foreign_keys = set(fields[attr])
        except KeyError:
          continue
        foreign_model, via = foreign
        old_foreign_keys = set(model[attr])
        added = new_foreign_keys - old_foreign_keys
        deled = old_foreign_keys - new_foreign_keys
        for foreign_key in added:
          associated = foreign_model.one(eid=foreign_key)
          if not associated:
            raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
          if 'model' in associated.attributes[via]:
            updated_keys = model.eid
          elif 'collection' in associated.attributes[via]:
            updated_keys = list(set(associated[via] + [model.eid]))
          storage.update(foreign_model.model_name, {via: updated_keys}, eids=[foreign_key])
        for foreign_key in deled:
          associated = foreign_model.one(eid=foreign_key)
          if not associated:
            raise ModelError(foreign_model, 'No record with ID %r' % foreign_key)
          if 'model' in associated.attributes[via]:
            updated_keys = None
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
      for attr, foreign in cls.associations.iteritems():
        foreign_model, via = foreign
        affected = foreign_model.search(eids=model[attr]) if attr else foreign_model.all() 
        for associated in affected:
          if 'model' in associated.attributes[via]:
            updated_field = None
          elif 'collection' in associated.attributes[via]:
            updated_field = list(set(associated[via]) - set([model.eid]))
          storage.update(foreign_model.model_name, {via: updated_field}, eids=[associated.eid])
    return storage.remove(cls.model_name, keys)


class ByName(object):
  """
  Mixin for a model with a unique 'name' field
  """
  @classmethod
  def withName(cls, name):
    return cls.one({'name': name})
