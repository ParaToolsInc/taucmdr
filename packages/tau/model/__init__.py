# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""TAU Commander data model.

TAU Commander follows the `Model-View-Controller (MVC)`_ design pattern.
Modules in :py:mod:`tau.model` define the data model by declaring subclasses of :any:`Controller`. 
These subclasses define a member dictionary `attributes` that describes the data model in the form::

    <attribute>: {
        property: value,
        [[property: value], ...]
    }
    
Attribute properties can be anything you wish as long as it's not one of these special properties:

* ``type`` (str): The attribute must be of the specified type.
* ``required`` (bool): The attribute must be specified in the data record. 
* ``model`` (str): The attribute creates an association with another data model.
* ``collection`` (str): The attribute creates an association with another data model.
* ``via`` (str): The attribute associates with another model "via" the specified attribute.

Models may have **associations** and **references**.  An association creates a relationship between
an attribute of this model and an attribute of another (a.k.a foreign) model.  If the associated
attribute changes then the foreign model will update its associated attribute.  A reference indicates
that this model is being referened by one or more attributes of a foreign model.  If a record of the
referenced model changes then the referencing model, i.e. the foreign model, will update all referencing 
attributes. Associations and references are constructed when :py:mod:`tau.model` is imported.  This 
module initializes the set :py:attr:`references` and the dictionary :py:attr:`associations`in each 
subclass of :any:`Controller` to describe these relationships.

Examples:

    *One-sided relationship*
    ::

        class Pet(Controller):
            attributes = {'name': {'type': 'string'}, 'hungry': {'type': 'bool'}}
        
        class Person(Controller):
            attributes = {'name': {'type': 'string'}, 'pet': {'model': 'Pet'}}
            
    We've related a Person to a Pet but not a Pet to a Person.  That is, we can query a Person 
    to get information about their Pet, but we can't query a Pet to get information about their Person.  
    If a Pet record changes then the Person record that referenced the Pet record is notified of the 
    change. If a Person record changes then nothing happens to Pet.  The Pet and Person classes codify
    this relationship as:
    
        * Pet.references = set( (Person, 'pet') )
        * Pet.associations = {}
        * Person.references = set() 
        * Person.associations = {}
    
    Some example data for this model::
    
        {
         'Pet': {1: {'name': 'Fluffy', 'hungry': True}},
         'Person': {0: {'name': 'Bob', 'pet': 1}} 
        }
                      
    *One-to-one relationship*
    ::
    
        class Husband(Controller):
            attributes = {'name': {'type': 'string'}, 'wife': {'model': 'Wife'}}
            
        class Wife(Controller):
            attributes = {'name': {'type': 'string'}, 'husband': {'model': 'Husband'}}
    
    We've related a Husband to a Wife.  The Husband may have only one Wife and the Wife may have
    only one Husband.  We can query a Husband to get information about their Wife and we can query a
    Wife to get information about their Husband.  If a Husband/Wife record changes then the Wife/Husband 
    record that referenced the Husband/Wife record is notified of the change.  The Husband and Wife classes
    codify this relationship as:
    
        * Husband.references = set( (Wife, 'husband') )
        * Husband.associations = {}
        * Wife.references = set( (Husband, 'wife') )
        * Wife.associations = {}  
    
    Example data::
    
        {
         'Husband': {2: {'name': 'Filbert', 'wife': 1}},
         'Wife': {1: {'name': 'Matilda', 'husband': 2}}
        }
    
    *One-to-many relationship*
    ::
    
        class Brewery(Controller):
            attributes = {'address': {'type': 'string'}, 
                          'brews': {'collection': 'Beer', 
                                    'via': 'origin'}}
            
        class Beer(Controller):
            attributes = {'origin': {'model': 'Brewery'}, 
                          'color': {'type': 'string'}, 
                          'ibu': {'type': 'int'}}
            
    We've related one Brewery to many Beers.  A Beer has only one Brewery but a Brewery has zero or
    more Beers.  The `brews` attribute has a `via` property along with a `collection` property to specify 
    which attribute of Beer relates Beer to Brewery, i.e. you may want a model to have multiple 
    one-to-many relationship with another model.  The Brewery and Beer classes codify this relationship as:
    
        * Brewery.references = set()
        * Brewery.associations = {'brews': (Beer, 'origin')}
        * Beer.references = set()
        * Beer.associations = {'origin': (Brewery, 'brews')}
        
    Example data::
    
        {
         'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                           'brews': [10, 12, 14]}},
         'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45},
                  12: {'origin': 100, 'color': 'dark', 'ibu': 15},
                  14: {'origin': 100, 'color': 'pale', 'ibu': 30}}
        }
    
    *Many-to-many relationship*
    ::
    
        class Actor(Controller):
            attributes = {'home_town': {'type': 'string'},
                          'appears_in': {'collection': 'Movie',
                                         'via': 'cast'}}
                                         
        class Movie(Controller):
            attributes = {'title': {'type': 'string'},
                          'cast': {'collection': 'Actor',
                                   'via': 'appears_in'}}
                                   
    An Actor may appear in many Movies and a Movie may have many Actors.  Changing the `cast` of a Movie
    notifies Actor and changing the movies an Actor `apppears_in` notifies Movie.  This relationship is
    codified as:
    
        * Actor.references = set()
        * Actor.associations = {'appears_in': (Movies, 'cast')}
        * Movie.references = set()
        * Movie.associations = {'cast': (Actor, 'appears_in')}
    
.. _Model-View-Controller (MVC): https://en.wikipedia.org/wiki/Model-view-controller
"""

import sys
import json
import operator
from pkgutil import walk_packages
from tau import logger, util
from tau.error import InternalError, ConfigurationError
from tau.storage import USER_STORAGE


LOGGER = logger.get_logger(__name__)


class ModelError(InternalError):
    """Indicates the given data does not match the specified model.
    
    Args:
        model_cls (Controller): Controller subclass definining the data model.
        value (str): A message describing the error.  
    """

    def __init__(self, model_cls, value):
        super(ModelError, self).__init__("Error in model '%s':\n%s" % (model_cls.model_name, value))
        self.model_cls = model_cls


class UniqueAttributeError(ModelError):
    """Indicates that duplicate values were given for a unique attribute.
    
    Args:
        model_cls (Controller): Controller subclass definining the data model.
        unique (dict): Dictionary of unique attributes in the data model.  
    """ 

    def __init__(self, model_cls, unique):
        super(UniqueAttributeError, self).__init__(model_cls, 'A record with one of %r already exists' % unique)


class Controller(object):
    """The "C" in `MVC`_.

    Attributes:
        model_name (str): The name of the model.
        attributes (dict): The model attributes.
        references (set): (Controller, str) tuples listing foreign models referencing this model.  
        associations (dict): (Controller, str) tuples keyed by attribute name defining attribute associations.
        eid (int): Unique identifier for the controlled data record, None if the data has not been recorded.
        data (dict): The controlled data.

    Args:
        fields (dict): A dictionary-like object with the optional `eid` attribute.
    
    .. _MVC: https://en.wikipedia.org/wiki/Model-view-controller
    """
    # Class methods may access the protected members of the class instances. 
    # pylint: disable=protected-access
    # Some class members don't exist until tau.model is imported.
    # pylint: disable=no-member
    
    def __init__(self, fields):
        self._populated = None
        self.eid = getattr(fields, 'eid', None)
        self.data = self._validate(fields)

    def __getitem__(self, key):
        return self.data[key]
    
    def __contains__(self, key):
        return key in self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __repr__(self):
        return json.dumps(repr(self.data))
    
    @classmethod
    def __class_init__(cls):
        def err(msg):
            raise ModelError(cls, "%s: %s" % (model_attr_name, msg))
        if not hasattr(cls, 'model_name'):
            cls.model_name = cls.__name__
        if not hasattr(cls, 'associations'):
            cls.associations = {}
        if not hasattr(cls, 'references'):
            cls.references = set()
        for attr, props in cls.attributes.iteritems():
            model_attr_name = cls.model_name + "." + attr
            if 'collection' in props and not 'via' in props:
                err("collection does not define 'via'")
            try:
                unique = props['unique']
            except KeyError:
                pass
            else:
                if not isinstance(unique, bool):
                    err("invalid value for 'unique'")
            try:
                description = props['description']
            except KeyError:
                LOGGER.debug("%s: no 'description'", model_attr_name)
            else:
                if not isinstance(description, basestring):
                    err("invalid value for 'description'")
#             try:
#                 compat = props['compat']
#             except KeyError:
#                 pass
#             else:
#                 for action, model_conditions in compat.iteritems():
#                     if action not in ['require', 'recommend', 'discourage', 'exclude']:
#                         err("Invalid action in 'compat': %s" % action)
#                     for model_name, conditions in model_conditions.iteritems():
#                         model = MODELS[model_name]
#                         for attr_name in conditions:
#                             if attr_name not in model.attributes:
#                                 err("In 'compat', model '%s' has no attribute '%s'" % (model_name, attr_name))

    @classmethod
    def _validate(cls, data, enforce_required=True):
        """Validates the given data against the model.
        
        Args:
            data (dict): Data to validate, may be None.
            enforce_required (bool): Set to False to allow required attributes to be unset in data.
                                     Useful when updating an existing record since we don't have to
                                     completely duplicate the existing record just to update one field.
        
        Returns:
            dict: Dictionary of validated data, may be None.
            
        Raises:
            ModelError: The given data doesn't fit the model.
        """
        #LOGGER.debug("Validating data for %s: %s" % (cls.__name__, data))
        if data is None:
            return None
        for key in data:
            if not key in cls.attributes:
                raise ModelError(cls, "Model '%s' has no attribute named '%s'" % (cls.model_name, key))
        validated = {}
        for attr, props in cls.attributes.iteritems():
            # Check required fields and defaults
            try:
                validated[attr] = data[attr]
            except KeyError:
                if 'required' in props:
                    if props['required'] and enforce_required:
                        raise ModelError(cls, "'%s' is required but was not defined" % attr)
                elif 'default' in props:
                    validated[attr] = props['default']
            # Check collections
            if 'collection' in props:
                value = data.get(attr, [])
                if not value:
                    value = []
                elif not isinstance(value, list):
                    raise ModelError(cls, "Value supplied for '%s' is not a list: %r" % (attr, value))
                else:
                    for eid in value:
                        try:
                            int(eid)
                        except ValueError:
                            raise ModelError(cls, "Invalid non-integer ID '%s' in '%s'" % (eid, attr))
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
        #LOGGER.debug("Validated %s data: %s" % (cls.__name__, validated))
        return validated

    def on_create(self):
        """Callback to be invoked when a new data record is created.""" 
        self.check_compatibility(self)

    def on_update(self): 
        """Callback to be invoked when a data record is updated."""
        self.check_compatibility(self)

    def on_delete(self): 
        """Callback to be invoked when a data record is deleted."""
        pass

    def populate(self, attribute=None):
        """Merges associated record data into the controlled data.
        
        Example:
            Suppose we have the following records::
            
                1: {'name': 'Katie', 'friends': [2, 3]}
                2: {'name': 'Ryan', 'friends': [1]}
                3: {'name': 'John', 'friends': [1]}
                
            Populating record ``1`` produces this dictionary::
            
                {'name': 'Katie',
                 'friends': [Controller({'name': 'Ryan', 'friends': [1]}),
                             Controller({'name': 'John', 'friends': [1]})]}
                             
            Note that the referenced data records are returned as :any:`Controller`
            subclass instances.  This enables expressions like::
            
                for friend in katie.populate('friends'):
                    print 'Hello %s!  Here are some fresh cookies' % friend['name']

        Args:
            attribute (Optional[str]): If given, return only the populated attribute.
            
        Returns:
            dict: Controlled data merged with associated records.
            
        Raises:
            KeyError: `attribute` is undefined in the populated record. 
        """
        if not self._populated:
            LOGGER.debug("Populating %r", self)
            self._populated = dict(self.data)
            for attr, props in self.attributes.iteritems():
                try:
                    foreign_model = MODELS[props['model']]
                except KeyError:
                    try:
                        foreign_model = MODELS[props['collection']]
                    except KeyError:
                        continue
                    else:
                        try:
                            self._populated[attr] = foreign_model.search(eids=self.data[attr])
                        except KeyError:
                            if props.get('required', False):
                                raise ModelError(self, "'%s' is required but was not defined" % attr)
                else:
                    try:
                        self._populated[attr] = foreign_model.one(eid=self.data[attr])
                    except KeyError:
                        if props.get('required', False):
                            raise ModelError(self, "'%s' is required but was not defined" % attr)
        if attribute:
            return self._populated[attribute]
        else:
            return self._populated

    @classmethod
    def one(cls, keys=None, eid=None):
        """Return a single record matching all of `keys` or element id `eid`.
        
        Either `keys` or `eid` should be specified, not both.  If `keys` is given,
        then every attribute listed in `keys` must have the given value. If `eid`
        is given, return the record with that eid. 
        
        Args:
            keys (dict): Attributes to match.
            eid (int): Record identifier to match.
            
        Returns:
            Controller: Controller subclass instance controlling the found record or None if no such record exists. 
        """
        LOGGER.debug("%s.one(keys=%s, eid=%s)", cls.model_name, keys, eid)
        found = USER_STORAGE.get(cls.model_name, keys=keys, eid=eid)
        return cls(found) if found else None

    @classmethod
    def all(cls):
        """Return a list of all records."""
        return [cls(result) for result in USER_STORAGE.search(cls.model_name)]

    @classmethod
    def search(cls, keys=None, eids=None):
        """Return a list of records matching all of `keys` or element id `eid`.
        
        Either `keys` or `eids` may be specified, not both.  If `keys` is not empty
        then every attribute listed in `keys` must have the given value. If `eids`
        is not empty then return the records with those eids. If either `keys` or 
        `eids` is empty, return an empty list.  If no arguments are given then
        return all records.
        
        Args:
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.
            
        Returns:
            list: Controller subclass instances controlling the found records. 
        """
        LOGGER.debug("%s.search(keys=%s, eids=%s)", cls.model_name, keys, eids)
        if keys is None and eids is None:
            return cls.all()
        elif eids:
            if isinstance(eids, list):
                return [cls.one(eid=i) for i in eids]
            else:
                return [cls.one(eid=eids)]
        elif keys:
            return [cls(record) for record in USER_STORAGE.search(cls.model_name, keys=keys)]
        else:
            return []

    @classmethod
    def match(cls, field, regex=None, test=None):
        """Return a list of records with `field` matching `regex` or `test`.
        
        Either `regex` or `test` may be specified, not both.  If `regex` is given,
        then all records with `field` matching the regular expression are returned.
        If test is given then all records with `field` set to a value that caues
        `test` to return True are returned. If neither is given, return all records. 
        
        Args:
            field (string): Name of the data field to match.
            regex (string): Regular expression string.
            test: A callable expression returning a boolean value.  
            
        Returns:
            list: Controller subclass instances controlling the found records. 
        """
        LOGGER.debug("%s.match(field=%s, regex=%s, test=%s)", cls.model_name, field, regex, test)
        return [cls(record) for record in USER_STORAGE.match(cls.model_name, field, regex, test)]

    @classmethod
    def exists(cls, keys=None, eids=None):
        """Test if a record matching the given keys exists.
        
        Just like :any:`Controller.search`, except only tests if the record exists without
        retrieving any data or allocating new controllers.
        
        Args:
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.
            
        Returns:
            bool: True if a record exists for **all** values in `keys` or `eids`.          
        """
        return USER_STORAGE.contains(cls.model_name, keys=keys, eids=eids)

    @classmethod
    def create(cls, fields):
        """Store a new model record and update associations.
        
        Invokes the `on_create` callback **after** the data is recorded. 
        
        Args:
            fields (dict): Data to record.
            
        Returns:
            Controller: Controller subclass instance controlling the specified data. 
        """
        model = cls(fields)
        unique = dict([(attr, model[attr]) for attr, props in cls.attributes.iteritems() if 'unique' in props])
        if USER_STORAGE.contains(cls.model_name, keys=unique, match_any=True):
            raise UniqueAttributeError(cls, unique)
        with USER_STORAGE as storage:
            model.eid = storage.insert(cls.model_name, model.data)
            for attr, foreign in cls.associations.iteritems():
                foreign_model, via = foreign
                if 'model' in model.attributes[attr]:
                    foreign_keys = [model.data[attr]]
                elif 'collection' in model.attributes[attr]:
                    foreign_keys = model.data[attr]
                model._associate(foreign_model, foreign_keys, via)
            model.on_create()
            LOGGER.debug("Created new %s record", cls.model_name)
            return model

    @classmethod
    def update(cls, fields, keys=None, eids=None):
        """Change recorded data and update associations.
        
        Invokes the `on_update` callback for each record **after** the records are updated.

        Args:
            fields (dict): New data for existing records.
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.
        """
        LOGGER.debug("%s.update(fields=%s, keys=%s, eids=%s)", cls.model_name, fields, keys, eids)
        with USER_STORAGE as storage:
            # Get the list of affected records **before** updating the data so foreign keys are correct
            changing = cls.search(keys, eids)
            storage.update(cls.model_name, cls._validate(fields, enforce_required=False), keys=keys, eids=eids)
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
                    added = list(new_foreign_keys - old_foreign_keys)
                    deled = list(old_foreign_keys - new_foreign_keys)
                    model._associate(foreign_model, added, via)
                    model._disassociate(foreign_model.search(eids=list(deled)), via)
                    model.on_update()

    @classmethod
    def delete(cls, keys=None, eids=None):
        """Delete recorded data and update associations.
        
        Invokes the `on_delete` callback for each record **before** the record is deleted.

        Args:
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.
        """
        LOGGER.debug("%s.delete(keys=%s, eids=%s)", cls.model_name, keys, eids)
        with USER_STORAGE as storage:
            for model in cls.search(keys, eids):
                # pylint complains because `model` is changing on every iteration so we'll have
                # a different lambda function `test` on each iteration.  This is exactly what
                # we want so we disble the warning. 
                # pylint: disable=cell-var-from-loop
                test = lambda x: model.eid in x if isinstance(x, list) else model.eid == x
                model.on_delete()
                for attr, foreign in cls.associations.iteritems():
                    foreign_model, via = foreign
                    affected = foreign_model.search(eids=model[attr])
                    LOGGER.debug("Deleting %s(eid=%s) affects '%s' in '%s'", cls.model_name, model.eid, via, affected)
                    model._disassociate(affected, via)
                for foreign_model, via in cls.references:
                    affected = foreign_model.match(via, test=test)
                    LOGGER.debug("Deleting %s(eid=%s) affects '%s'", cls.model_name, model.eid, affected)
                    model._disassociate(affected, via)
            storage.remove(cls.model_name, keys=keys, eids=eids)

    @staticmethod
    def import_records(data):
        """Import data records.
        
        TODO: Docs
        """
        eid_map = {}
        with USER_STORAGE:
            for model_name, model_records in data.iteritems():
                for eid, data in model_records.iteritems():
                    eid_map[eid] = MODELS[model_name].create(data)
        
    @classmethod
    def export_records(cls, keys=None, eids=None):
        """Export data records.
        
        Constructs a dictionary containing records matching `keys` or `eids` and all their
        associated records.  Association fields (`model` and `collection`) are **not** updated
        and may contain eids of undefined records. 

        Args:
            keys (dict): Attributes to match.
            eids (list): Record identifiers to match.

        Returns:
            dict: Dictionary of tables containing records.
            
        Example:
        ::
            
            {
             'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                               'brews': [10, 12, 14]}},
             'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45},
                      12: {'origin': 100, 'color': 'dark', 'ibu': 15},
                      14: {'origin': 100, 'color': 'pale', 'ibu': 30}}
            }
        
            Beer.export_records(eids=[10])
            
            {
             'Brewery': {100: {'address': '4615 Hollins Ferry Rd, Halethorpe, MD 21227',
                               'brews': [10, 12, 14]}},
             'Beer': {10: {'origin': 100, 'color': 'gold', 'ibu': 45}}
            }

        """
        def export_record(record, root):
            if isinstance(record, cls) and record is not root:
                return
            data = all_data.setdefault(record.model_name, {})
            if record.eid not in data:
                data[record.eid] = record.data
                for attr, foreign in record.associations.iteritems():
                    for foreign_record in foreign[0].search(eids=record[attr]):
                        export_record(foreign_record, root)
        all_data = {}
        for record in cls.search(keys, eids):
            export_record(record, record)
        return all_data
          
    
    def _associate(self, foreign_cls, affected, attr):
        """Associates the controlled record with another record.
        
        Associations are defined by the :py:attr:`associations` and :py:attr:`references` 
        attributes of the :any:`Controller` class.
        
        Args:
            foreign_cls (Controller): Class definining the foreign record's data model.
            affected (list): Identifiers for the records that will be updated to 
                             associate with the controlled record.
            attr (str): The name of the associated foreign attribute.
        """ 
        if not len(affected): 
            return
        LOGGER.debug("Adding %s to '%s' in %s(eids=%s)", self.eid, attr, foreign_cls.model_name, affected)
        with USER_STORAGE as storage:
            for key in affected:
                model = foreign_cls.one(eid=key)
                if not model:
                    raise ModelError(foreign_cls, "No record with ID '%s'" % key)
                if 'model' in model.attributes[attr]:
                    updated = self.eid
                elif 'collection' in model.attributes[attr]:
                    updated = list(set(model[attr] + [self.eid]))
                storage.update(foreign_cls.model_name, {attr: updated}, eids=key)

    def _disassociate(self, affected, attr):
        """Disassociates the controlled record from another record.
        
        Associations are defined by the :py:attr:`associations` and :py:attr:`references` 
        attributes of the :any:`Controller` class.
        
        Args:
            affected (list): Identifiers for the records that will be updated to 
                             associate with the controlled record.
            attr (str): The name of the associated foreign attribute.
        """ 
        if not len(affected):
            return
        LOGGER.debug("Removing %s from '%s' in %r", self.eid, attr, affected)
        with USER_STORAGE as storage:
            for model in affected:
                if 'model' in model.attributes[attr]:
                    if 'required' in model.attributes[attr]:
                        LOGGER.debug("Empty required attr '%s': deleting %s(eid=%s)", 
                                     attr, model.model_name, model.eid)
                        model.delete(eids=model.eid)
                    else:
                        storage.update(
                            model.model_name, {attr: None}, eids=model.eid)
                elif 'collection' in model.attributes[attr]:
                    update = list(set(model[attr]) - set([self.eid]))
                    if 'required' in model.attributes[attr] and len(update) == 0:
                        LOGGER.debug("Empty required attr '%s': deleting %s(eid=%s)",
                                     attr, model.model_name, model.eid)
                        model.delete(eids=model.eid)
                    else:
                        storage.update(
                            model.model_name, {attr: update}, eids=model.eid)
    
    @classmethod
    def _construct_enforcer(cls, args, op, callback, attr_incorrect_fmt, attr_undefined_fmt):
        rhs_attr = args[0]
        try:
            checked_value = args[1]
        except IndexError:
            if not attr_undefined_fmt:
                raise ModelError("%s: Invalid 'compat' property: no checked value and"
                                 " no message format for undefined attribute" % cls.model_name)
            else:
                def enforcer(lhs, lhs_attr, lhs_value, rhs):
                    if isinstance(rhs, cls) and rhs_attr not in rhs:
                        fields = {'lhs_attr': lhs_attr,
                                  'lhs_value': lhs_value,
                                  'lhs_name': lhs.model_name.lower(),
                                  'rhs_attr': rhs_attr,
                                  'rhs_name': cls.model_name.lower()}
                        callback(attr_undefined_fmt % fields)
        else:
            if callable(checked_value):
                def enforcer(lhs, lhs_attr, lhs_value, rhs):
                    if isinstance(rhs, cls):
                        checked_value(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
            else:
                def enforcer(lhs, lhs_attr, lhs_value, rhs):
                    if isinstance(rhs, cls):
                        fields = {'lhs_attr': lhs_attr,
                                  'lhs_value': lhs_value,
                                  'lhs_name': lhs.model_name.lower(),
                                  'rhs_attr': rhs_attr,
                                  'rhs_name': cls.model_name.lower()}
                        try:
                            rhs_value = rhs[rhs_attr]
                        except KeyError:
                            if attr_undefined_fmt:
                                callback(attr_undefined_fmt % fields)
                        else:
                            if op(rhs_value, checked_value):
                                fields['rhs_value'] = rhs_value
                                callback(attr_incorrect_fmt % fields)
        return enforcer

    @classmethod
    def require(cls, *args):
        def callback(msg):
            raise ConfigurationError(msg)
        attr_undefined_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s requires"
                              " %(rhs_attr)s be defined in %(rhs_name)s")
        attr_incorrect_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s requires"
                              " %(rhs_attr)s = %(rhs_value)s in %(rhs_name)s")
        return cls._construct_enforcer(args, operator.ne, callback, attr_incorrect_fmt, attr_undefined_fmt)

    @classmethod
    def encourage(cls, *args):
        attr_undefined_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s recommends"
                              " %(rhs_attr)s be defined in %(rhs_name)s")
        attr_incorrect_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s recommends"
                              " %(rhs_attr)s = %(rhs_value)s in %(rhs_name)s")
        return cls._construct_enforcer(args, operator.ne, LOGGER.warning, attr_incorrect_fmt, attr_undefined_fmt)

    @classmethod
    def discourage(cls, *args):
        attr_incorrect_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s discourages"
                              " %(rhs_attr)s = %(rhs_value)s in %(rhs_name)s")
        return cls._construct_enforcer(args, operator.eq, LOGGER.warning, attr_incorrect_fmt, None)

    @classmethod
    def exclude(cls, *args):
        def callback(msg):
            raise ConfigurationError(msg)
        attr_incorrect_fmt = ("%(lhs_attr)s = %(lhs_value)s in %(lhs_name)s disallows"
                              " %(rhs_attr)s = %(rhs_value)s in %(rhs_name)s")
        return cls._construct_enforcer(args, operator.eq, callback, attr_incorrect_fmt, None)
        

    def check_compatibility(self, rhs):
        """Test the controlled record for compatibility with another record.
        
        Operations combining data from multiple records (e.g. selecting a project configuration)
        must know that the records are mutually compatible.  This routine checks the 'compat'
        property of each attribute (if set) to enforce compatibility.  'compat' is a dictionary
        of compatibility `action`s mapped to dictionaries of model attributes keyed by the
        model name, i.e. ``compat[action][model_name][attribute_name] = value``
        ::
        
            {
            action: {model_name: {attribute_name: value,
                                  [attribute_name: value ...]}
                     [model_name: {attribute_name: value}] }
            }

        `action` may be one of:
        * 'require': All attributes must have values equal to the listed values.
          If any attributes does not have the listed value then the records 
          are not compatible.
        * 'recommend': All attributes *should* have values equal to the listed values.
          A warning message will be generated for every attribute that doesn't have
          the recommended value.
        * 'discourage': The logical negation of 'recommend'.  All attributes *should not* 
          have values equal to the listed values. A warning message will be generated for 
          every attribute that doesn't have the recommended value.
        * 'exclude': The logical negation of 'require'. All attributes must not have 
          values equal to the listed values. If any attribute has the listed value then 
          the records are not compatible.
          
        `value` is either a literal value to test against or a callable.  If it is callable
        it must accept these arguments:
        * `lhs`: The left hand side of the compatibility check, i.e. `self`.
        * `lhs_attr`: The attribute of `lhs` defining the `compat` property.
        * `rhs`: The right hand sde of the compatibility check, i.e. `rhs` of this function.
        * `rhs_attr`: The attribute of `rhs` listed in `compat`.
        * `given`: The given value of `rhs_attr`.

        Note that `rhs` may be `self` to perform self-consistency checks, e.g. prevent
        mutually exclusive attributes from being set in the same record.

        Args:
            rhs (Controller): Controller for the data record to check compatibility.
            
        Raises:
            ConfigurationError: The two records are not compatible.
        """
        as_tuple = lambda x: x if isinstance(x, tuple) else (x,)
        for attr, props in self.attributes.iteritems():
            try:
                compat = props['compat']
            except KeyError:
                continue
            try:
                attr_value = self[attr]
            except KeyError:
                continue
            for checked_values, conditions in compat.iteritems():
                if attr_value in as_tuple(checked_values):
                    for condition in as_tuple(conditions):
                        condition(self, attr, attr_value, rhs)
                      

class ByName(object):
    """Mixin for a model with a unique `name` attribute."""
    # Ignore missing members since this is a mixin class to be used with Controller
    # pylint: disable=no-member
    
    @classmethod
    def with_name(cls, name):
        """Return the record with the given name.  See :any:`Controller.one`"""
        return cls.one({'name': name})


def _yield_model_classes():
    for _, module_name, _ in walk_packages(__path__, __name__ + '.'):
        __import__(module_name)
        module_dict = sys.modules[module_name].__dict__
        model_class_name = util.camelcase(module_name.split('.')[-1])
        try:
            model_class = module_dict[model_class_name]
        except KeyError:
            raise InternalError("module '%s' does not define class '%s'" % (module_name, model_class_name))
        yield model_class       


def _get_props_model_name(props):
    try:
        return props['model']
    except KeyError:
        return props['collection']
    

def _construct_model(models):
    """Builds model relationships.
    
    Initializes controller classes and builds associations and references between data models.
    
    Raises:
        ModelError: A data model is invalid. 
    
    Returns:
        dict: Model controller classes indexed by model name. 
    """
    for cls_name, cls in models.iteritems():
        cls.__class_init__()
        for attr, props in cls.attributes.iteritems():
            via = props.get('via', None)
            try:
                foreign_name = _get_props_model_name(props) 
            except KeyError:
                if not via:
                    continue
                raise ModelError(cls, "Attribute '%s' defines 'via' property "
                                 "but not 'model' or 'collection'" % attr)
            try:
                foreign_cls = models[foreign_name]
            except KeyError:
                raise ModelError(cls, "Invalid model name in attribute '%s'" % attr)
            foreign_cls.__class_init__()
    
            forward = (foreign_cls, via)
            reverse = (cls, attr)
            if not via:
                foreign_cls.references.add(reverse)
            else:
                foreign_cls.associations[via] = reverse
                try:
                    via_props = foreign_cls.attributes[via]
                except KeyError:
                    raise ModelError(cls, "Found 'via' on undefined attribute '%s.%s'" % (foreign_name, via))
                try:
                    via_attr_model_name = _get_props_model_name(via_props)
                except KeyError:
                    raise ModelError(cls, "Found 'via' on non-model attribute '%s.%s'" % (foreign_name, via))
                if via_attr_model_name != cls_name:
                    raise ModelError(cls, "Attribute %s.%s referenced by 'via' in '%s' "
                                     "does not define 'collection' or 'model' of type '%s'" %
                                     (foreign_name, via, attr, cls_name))
                try:
                    existing = cls.associations[attr]
                except KeyError:
                    cls.associations[attr] = forward
                else:
                    if existing != forward:
                        raise ModelError(cls, "Conflicting associations on attribute '%s': "
                                         "%r vs. %r" % (attr, existing, forward))

MODELS = dict([(_.__name__, _) for _ in _yield_model_classes()])
_construct_model(MODELS)

