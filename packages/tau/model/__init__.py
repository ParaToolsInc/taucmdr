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

Importing :py:mod:`tau.model` initializes the set :py:attr:`references` in each subclass
of :any:`Controller` to describe one-sided relationships.  For example::

    Model_A:
        attr_x: { 'model': 'Model_C' }
    Model_B:
        attr_y: { 'model': 'Model_C' }
    Model_C:
        references = set( (Model_A, 'attr_x'), (Model_B, 'attr_y') )

Importing :py:mod:`tau.model` also initializes the dictionary :py:attr:`associations` in
each subclass of :any:`Controller` to describe two-sided relationships.  For example::

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
    
.. _Model-View-Controller (MVC): https://en.wikipedia.org/wiki/Model-view-controller
"""

import sys
import json
from pkgutil import walk_packages
from tau import logger, requisite, util
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
    """The "C" in MVC_.

    Attributes:
        model_name (str): The name of the model.
        attributes (dict): The model attributes.
        references (set): Set of tuples defining one-sided relationships.  
        associations (dict): Dictionary of tuples keyed by attribute name defining two-sided relationships.
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

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __repr__(self):
        return json.dumps(repr(self.data))
    
    @classmethod
    def __class_init__(cls):
        if not hasattr(cls, 'model_name'):
            cls.model_name = cls.__name__
        if not hasattr(cls, 'associations'):
            cls.associations = {}
        if not hasattr(cls, 'references'):
            cls.references = set()

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

    def on_update(self): 
        """Callback to be invoked when a data record is updated."""

    def on_delete(self): 
        """Callback to be invoked when a data record is deleted."""

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
        LOGGER.debug("Searching '%s' for keys=%r, eid=%r", cls.model_name, keys, eid)
        found = USER_STORAGE.get(cls.model_name, keys=keys, eid=eid)
        return cls(found) if found else None

    @classmethod
    def all(cls):
        """Return a list of all records."""
        return [cls(result) for result in USER_STORAGE.search(cls.model_name)]

    @classmethod
    def search(cls, keys=None, eids=None):
        """Return a list of records matching all of `keys` or element id `eid`.
        
        Either `keys` or `eids` may be specified, not both.  If `keys` is given,
        then every attribute listed in `keys` must have the given value. If `eids`
        is given, return the records with those eids.  If neither is given, 
        return all records. 
        
        Args:
            keys (dict): Attributes to match.
            eids (:py:class:`list`): Record identifiers to match.
            
        Returns:
            :py:class:`list`: Controller subclass instances controlling the found records. 
        """
        if eids is not None:
            if isinstance(eids, list):
                return [cls.one(eid=i) for i in eids]
            else:
                return [cls.one(eid=eids)]
        elif keys:
            return [cls(record) for record in USER_STORAGE.search(cls.model_name, keys=keys)]
        else:
            return cls.all()

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
            :py:class:`list`: Controller subclass instances controlling the found records. 
        """
        return [cls(record) for record in USER_STORAGE.match(cls.model_name, field, regex, test)]

    @classmethod
    def exists(cls, keys=None, eids=None):
        """Test if a record matching the given keys exists.
        
        Just like :any:`Controller.search`, except only tests if the record exists without
        retrieving any data or allocating new controllers.
        
        Args:
            keys (dict): Attributes to match.
            eids (:py:class:`list`): Record identifiers to match.
            
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
            return model

    @classmethod
    def update(cls, fields, keys=None, eids=None):
        """Change recorded data and update associations.
        
        Invokes the `on_update` callback for each record **after** the records are updated.

        Args:
            fields (dict): New data for existing records.
            keys (dict): Attributes to match.
            eids (:py:class:`list`): Record identifiers to match.
        """
        if eids is not None:
            changing = cls.search(eids=eids)
        elif keys is not None:
            changing = cls.search(keys)
        else:
            raise InternalError('Controller.update() requires either keys or eids')
        with USER_STORAGE as storage:
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
                    added = new_foreign_keys - old_foreign_keys
                    deled = old_foreign_keys - new_foreign_keys
                    model._associate(foreign_model, added, via)
                    model._disassociate(
                        foreign_model.search(eids=list(deled)), via)
                    model.on_update()

    @classmethod
    def delete(cls, keys=None, eids=None):
        """Delete recorded data and update associations.
        
        Invokes the `on_delete` callback for each record **before** the record is deleted.

        Args:
            keys (dict): Attributes to match.
            eids (:py:class:`list`): Record identifiers to match.
        """
        if eids is not None:
            changing = cls.search(eids=eids)
        elif keys is not None:
            changing = cls.search(keys)
        else:
            raise InternalError('Controller.delete() requires either keys or eids')
        with USER_STORAGE as storage:
            for model in changing:
                # pylint complains because `model` is changing on every iteration so we'll have
                # a different lambda function `test` on each iteration.  This is exactly what
                # we want so we disble the warning. 
                # pylint: disable=cell-var-from-loop
                test = lambda x: model.eid in x if isinstance(x, list) else model.eid == x
                model.on_delete()
                for attr, foreign in cls.associations.iteritems():
                    foreign_model, via = foreign
                    affected = foreign_model.search(eids=model[attr])
                    LOGGER.debug("Deleting %s(eid=%s) affects '%s' in '%s'", 
                                 cls.model_name, model.eid, via, affected)
                    model._disassociate(affected, via)
                for foreign_model, via in cls.references:
                    affected = foreign_model.match(via, test=test)
                    LOGGER.debug("Deleting %s(eid=%s) affects '%s'", 
                                 cls.model_name, model.eid, affected)
                    model._disassociate(affected, via)
            storage.remove(cls.model_name, keys=keys, eids=eids)

    def _associate(self, foreign_cls, affected, attr):
        """Associates the controlled record with another record.
        
        Associations are defined by the :py:attr:`associations` and :py:attr:`references` 
        attributes of the :any:`Controller` class.
        
        Args:
            foreign_cls (Controller): Class definining the foreign record's data model.
            affected (:py:class:`list`): Identifiers for the records that will be updated to 
                             associate with the controlled record.
            attr (str): The name of the associated foreign attribute.
        """ 
        LOGGER.debug("Adding %s to '%s' in %s(eids=%s)", self.eid, attr, foreign_cls.model_name, affected)
        with USER_STORAGE as storage:
            for key in affected:
                model = foreign_cls.one(eid=key)
                if not model:
                    raise ModelError(
                        foreign_cls, "No record with ID '%s'" % key)
                if 'model' in model.attributes[attr]:
                    updated = self.eid
                elif 'collection' in model.attributes[attr]:
                    updated = list(set(model[attr] + [self.eid]))
                storage.update(
                    foreign_cls.model_name, {attr: updated}, eids=key)

    def _disassociate(self, affected, attr):
        """Disassociates the controlled record from another record.
        
        Associations are defined by the :py:attr:`associations` and :py:attr:`references` 
        attributes of the :any:`Controller` class.
        
        Args:
            affected (:py:class:`list`): Identifiers for the records that will be updated to 
                             associate with the controlled record.
            attr (str): The name of the associated foreign attribute.
        """ 
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

    def compatible_with(self, other):
        """Test the controlled record for compatibility with another record.
        
        FIXME: Compatilibity checking needs further design review.
        
        Args:
            other (Controller): Controller subclass instance controlling the other record.
            
        Raises:
            ConfigurationError: The two records are not compatible.
        """ 
        for fields in self.attributes.itervalues():
            try:
                compat = fields['compat']
            except KeyError:
                continue
            for model, attr in compat.iteritems():
                if model == other.model_name:
                    for oattr, rule in attr.iteritems():
                        LOGGER.debug("%s is oattr, while %s is self.data for %s",
                                     oattr, self.data, self.model_name)
                        LOGGER.debug("%s is oattr, while %s is other.data for %s", 
                                     oattr, other.data, other.model_name)
                        try:
                            self_oattr = util.parse_bool(self.data[oattr], 
                                                         additional_true=['fallback', 'always'], 
                                                         additional_false=['never'])
                            other_oattr = util.parse_bool(other.data[oattr], 
                                                          additional_true=['fallback', 'always'], 
                                                          additional_false=['never'])
                        except KeyError:
                            continue
                        if self_oattr and other_oattr:
                            LOGGER.debug("%s is turned on in %s and on in %s",
                                         oattr, self.model_name, other.model_name)
                        if self_oattr and (not other_oattr):
                            LOGGER.debug("%s is turned on in %s and off in %s with rule %s", 
                                         oattr, self.model_name, other.model_name, rule)
                            if rule == requisite.Required:
                                raise ConfigurationError("%s required by %s but not set in %s ", 
                                                         oattr, self.model_name, other.model_name)
                            elif rule == requisite.Recommended:
                                LOGGER.warning("%s is recommended for %s by the %s model",
                                               oattr, self.model_name, other.model_name)
                        if other_oattr and not self_oattr:
                            LOGGER.debug("%s is turned off in %s and on %s", 
                                         oattr, self.model_name, other.model_name)
                            LOGGER.debug("%s is self.data[oattr] and %s is other.data[oattr] for oattr = %s",
                                         self_oattr, other_oattr, oattr)
                        if not self_oattr and not other_oattr:
                            LOGGER.debug("%s is turned off in %s and off %s",
                                         oattr, self.model_name, other.model_name)


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
    

def _construct_model():
    """Builds model relationships.
    
    Initializes controller classes and builds forward and reverse associations
    between data models.
    
    Returns:
        dict: Model controller classes indexed by model name. 
    """
    models = dict([(cls.__name__, cls) for cls in _yield_model_classes()])
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
                    raise ModelError(cls, "Found 'via' on undefined attribute '%s.%s'" %
                                     (foreign_name, via))
                try:
                    via_attr_model_name = _get_props_model_name(via_props)
                except KeyError:
                    raise ModelError(cls, "Found 'via' on non-model attribute '%s.%s'" %
                                     (foreign_name, via))
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
    return models

MODELS = _construct_model()
