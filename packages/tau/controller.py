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
import json
import sys

# TAU modules
import logger
import error
from storage import user_storage
import requisite
import util
import tau


LOGGER = logger.getLogger(__name__)


class ModelError(error.InternalError):
  """
  Indicates that invalid model data was given.
  """
  def __init__(self, model_cls, value):
    super(ModelError, self).__init__("Error in model '%s':\n%s" % (model_cls.model_name, value))
    self.model_cls = model_cls


class UniqueAttributeError(ModelError):
  def __init__(self, model_cls, unique):
    super(UniqueAttributeError, self).__init__(
            model_cls, 'A record with one of %r already exists' % unique)



class Controller(object):
  """
  The C" in MVC

  Subclasses reside in the 'model' package and define a member dictionary
  'attributes' that describes the data model in the form:
    <attribute>: {
      property: value,
      [[property: value], ...]
    }

  The 'model' package initializes the set 'references' in each class
  to describe one-sided relationships, e.g.
    Model_A:
      attr_x: { 'model': 'Model_C' }
    Model_B:
      attr_y: { 'model': 'Model_C' }
    Model_C:
      references = set( (Model_A, 'attr_x'), (Model_B, 'attr_y') )

  The 'model' package also initializes the dictionary 'associations' in
  each class to describe two-sided relationships, e.g.
    Model_A:
      attr_x: {
        model: Model_B
        via: attr_k
      }
      associations = {attr_x: (Model_B, attr_k)}
    Model_B:
      attr_k: {
        model: Model_A
      }
      associations = {attr_k: (Model_A, attr_x)}
  """

  # Subclasses override for callback
  def onCreate(self): pass
  def onUpdate(self): pass
  def onDelete(self): pass

  def __init__(self, fields):
    self.eid = getattr(fields, 'eid', None)
    self.data = self._validate(fields)
    self.populated = None

  def __getitem__(self, key):
    return self.data[key]

  def get(self, key, default=None):
    return self.data.get(key, default)

  def __repr__(self):
    return json.dumps(repr(self.data))

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
          raise ModelError(cls, "Model '%s' has no attribute named '%s'" % (cls.model_name, key))
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
      # Check model associations
      elif 'model' in props:
        value = data.get(attr, None)
        if value is not None:
          try:
            if int(value) != value:
              raise ValueError
          except ValueError:
            raise ModelError(cls, "Invalid non-integer ID '%s' in '%s'" % (value, attr))
          validated[attr] = value
    return validated

  def populate(self, attribute=None):
    """
    Transltes model id numbers in `self` to model controllers and
    returns all data as a dictionary
    """
    from tau.model import MODELS
    LOGGER.debug('Populating %r' % self)
    if not self.populated:
      self.populated = dict(self.data)
      for attr, props in self.attributes.iteritems():
        try:
          foreign_model = MODELS[props['model']]
        except KeyError:
          try:
            foreign_model = MODELS[props['collection']]
          except KeyError:
            continue
          else:
            self.populated[attr] = foreign_model.search(eids=self.data[attr])
        else:
          self.populated[attr] = foreign_model.one(eid=self.data[attr])
    if attribute:
      return self.populated[attribute]
    else:
      return self.populated

  @classmethod
  def one(cls, keys=None, eid=None):
    """
    Return a single record matching all of 'keys' or element id 'eid'
    """
    LOGGER.debug("Searching '%s' for keys=%r, eid=%r" % (cls.model_name, keys, eid))
    found = user_storage.get(cls.model_name, keys=keys, eid=eid)
    return cls(found) if found else None

  @classmethod
  def all(cls):
    """
    Return a list of all records
    """
    return [cls(result) for result in user_storage.search(cls.model_name)]

  @classmethod
  def search(cls, keys=None, eids=None):
    """
    Return a list of records matching all of 'keys' or element id 'eid'
    """
    if eids is not None:
      if isinstance(eids, list):
        return [cls.one(eid=id) for id in eids]
      else:
        return [cls.one(eid=eids)]
    elif keys:
      return [cls(record) for record in user_storage.search(cls.model_name, keys=keys)]
    else:
      return cls.all()

  @classmethod
  def match(cls, field, regex=None, test=None):
    """
    Return a list of records with 'field' matching 'regex' or 'test'
    """
    return [cls(record) for record in user_storage.match(cls.model_name, field, regex, test)]

  @classmethod
  def exists(cls, keys=None, eids=None):
    """
    Return true if a record matching the given keys exists
    """
    return user_storage.contains(cls.model_name, keys=keys, eids=eids)

  @classmethod
  def create(cls, fields):
    """
    Store a new model record and update associations
    """
    model = cls(fields)
    unique = dict([(attr, model[attr])
                   for attr, props in cls.attributes.iteritems()
                   if 'unique' in props])
    if user_storage.contains(cls.model_name, keys=unique, any=True):
      raise UniqueAttributeError(cls, unique)
    with user_storage as storage:
      model.eid = storage.insert(cls.model_name, model.data)
      for attr, foreign in cls.associations.iteritems():
        foreign_model, via = foreign
        if 'model' in model.attributes[attr]:
          foreign_keys = [model.data[attr]]
        elif 'collection' in model.attributes[attr]:
          foreign_keys = model.data[attr]
        model._addTo(foreign_model, foreign_keys, via)
      model.onCreate()
      return model

  @classmethod
  def update(cls, fields, keys=None, eids=None):
    """
    Change the fields of all records that match the given keys
    and update associations
    """
    if eids is not None:
      changing = cls.search(eids=eids)
    elif keys is not None:
      changing = cls.search(keys)
    else:
      raise error.InternalError('Controller.update() requires either keys or eids')
    with user_storage as storage:
      storage.update(cls.model_name, fields, keys=keys, eids=eids)
      for model in changing:
        for attr, foreign in cls.associations.iteritems():
          try:
            new_foreign_keys = set(fields[attr])
          except KeyError:
            continue
          try:
            old_foreign_keys = set(model[attr])
          except KeyError:
            old_foreign_keys = set()
          foreign_model, via = foreign
          added = new_foreign_keys - old_foreign_keys
          deled = old_foreign_keys - new_foreign_keys
          model._addTo(foreign_model, added, via)
          model._removeFrom(foreign_model.search(eids=list(deled)), via)
          model.onUpdate()

  @classmethod
  def delete(cls, keys=None, eids=None):
    """
    Delete the records that match the given keys and update associations
    """
    if eids is not None:
      changing = cls.search(eids=eids)
    elif keys is not None:
      changing = cls.search(keys)
    else:
      raise error.InternalError('Controller.delete() requires either keys or eids')
    with user_storage as storage:
      for model in changing:
        model.onDelete()
        for attr, foreign in cls.associations.iteritems():
          foreign_model, via = foreign
          affected = foreign_model.search(eids=model[attr])
          LOGGER.debug("Deleting %s(eid=%s) affects '%s' in '%s'" %
                       (cls.model_name, model.eid, via, affected))
          model._removeFrom(affected, via)
        for foreign_model, via in cls.references:
          test = lambda x: (model.eid in x if isinstance(x, list) else model.eid == x)
          affected = foreign_model.match(via, test=test)
          LOGGER.debug("Deleting %s(eid=%s) affects '%s'" % (cls.model_name, model.eid, affected))
          model._removeFrom(affected, via)
      return storage.remove(cls.model_name, keys=keys, eids=eids)

  def _addTo(self, foreign_cls, keys, attr):
    LOGGER.debug("Adding %s to '%s' in %s(eids=%s)" %
                 (self.eid, attr, foreign_cls.model_name, keys))
    with user_storage as storage:
      for key in keys:
        model = foreign_cls.one(eid=key)
        if not model:
          raise ModelError(foreign_cls, "No record with ID '%s'" % key)
        if 'model' in model.attributes[attr]:
          updated = self.eid
        elif 'collection' in model.attributes[attr]:
          updated = list(set(model[attr] + [self.eid]))
        storage.update(foreign_cls.model_name, {attr: updated}, eids=key)

  def _removeFrom(self, affected, attr):
    LOGGER.debug("Removing %s from '%s' in %r" % (self.eid, attr, affected))
    with user_storage as storage:
      for model in affected:
        if 'model' in model.attributes[attr]:
          if 'required' in model.attributes[attr]:
            LOGGER.debug("Empty required attr '%s': deleting %s(eid=%s)" %
                         (attr, model.model_name, model.eid))
            model.delete(eids=model.eid)
          else:
            storage.update(model.model_name, {attr: None}, eids=model.eid)
        elif 'collection' in model.attributes[attr]:
          update = list(set(model[attr]) - set([self.eid]))
          if 'required' in model.attributes[attr] and len(update) == 0:
            LOGGER.debug("Empty required attr '%s': deleting %s(eid=%s)" %
                         (attr, model.model_name, model.eid))
            model.delete(eids=model.eid)
          else:
            storage.update(model.model_name, {attr: update}, eids=model.eid)

  def compatibleWith(self, other):
    selfName = self.model_name.lower().strip()
    otherName = other.model_name.lower().strip()
    for attr, fields in self.attributes.iteritems():
      try:
        compat = fields['compat']
      except KeyError:
        continue
      for model, selfCompatAttr in compat.iteritems():
        if model == otherName :
          for oattr, rule in selfCompatAttr.iteritems():
            LOGGER.debug(" %s is oattr, while %s is self.data for %s" % (oattr,self.data,self.model_name))
            LOGGER.debug(" %s is oattr, while %s is other.data for %s" % (oattr,other.data,other.model_name))
            try:
              selfDataOattr=util.parseBoolean(self.data[oattr],trueList=['fallback','always'],falseList=['never'])
              otherDataOattr=util.parseBoolean(other.data[oattr],trueList=['fallback','always'],falseList=['never'])
            except KeyError:
              continue
            if selfDataOattr and otherDataOattr:
              LOGGER.debug(" %s is turned on in %s and on in %s  " % (oattr,self.model_name,other.model_name))
            if selfDataOattr and (not otherDataOattr):
              LOGGER.debug(" %s is turned on in %s and off in %s with rule %s  " % (oattr,self.model_name,other.model_name,rule))
              if rule == requisite.Required:
                raise error.ConfigurationError(" %s required by %s but not set in %s "  % (oattr,selfName,otherName))
              elif rule == requisite.Recommended:
                LOGGER.warning("%s is recommended for %s by the %s model" % (oattr,selfName,otherName))
                #how to raise error and print but succeed with select
            if (not selfDataOattr) and (otherDataOattr):
              LOGGER.debug(" %s is turned off  in %s and on %s  " % (oattr,self.model_name,other.model_name))
              LOGGER.debug(" %s is self.data[oattr] and  %s is other.data[oattr] for oattr = %s  " % (selfDataOattr,otherDataOattr,oattr))
            if (not selfDataOattr) and (not otherDataOattr):
              LOGGER.debug(" %s is turned off in %s and off %s  " % (oattr,self.model_name,other.model_name))



class ByName(object):
  """
  Mixin for a model with a unique 'name' field
  """
  @classmethod
  def withName(cls, name):
    return cls.one({'name': name})
