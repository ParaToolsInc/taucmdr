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
"""TAU Commander data model core components.

See :any:`tau.core` for details.
"""

import sys
import json
from tau import logger, util
from tau.error import ConfigurationError, ModelError, UniqueAttributeError, InternalError
from tau.storage import USER_STORAGE


LOGGER = logger.get_logger(__name__)


class Controller(object):
    """The "C" in `MVC`_.

    Attributes:
        model_name (str): The name of the model.
        attributes (dict): The model attributes.
        references (set): (Controller, str) tuples listing foreign models referencing this model.  
        associations (dict): (Controller, str) tuples keyed by attribute name defining attribute associations.
        eid (int): Unique identifier for the controlled data record, None if the data has not been recorded.
        data (dict): The controlled data.
    
    .. _MVC: https://en.wikipedia.org/wiki/Model-view-controller
    """
    # Class methods may access the protected members of the class instances. 
    # pylint: disable=protected-access
    
    @classmethod
    def __class_init__(cls):
        """Initializes the controller class object.
        
        Initializes class members that define relationships and model attributes and
        checks the model attributes for correctness.
        """
        if hasattr(cls, 'attributes'):
            return
        module_name_parts = cls.__module__.split('.')
        model_name = util.camelcase(module_name_parts[-2])
        if cls.__name__ != model_name:
            raise InternalError("Class %s should be named %s to control model %s" % 
                                (cls.__name__, model_name, model_name))
        cls.model_name = model_name
        cls.associations = {}
        cls.references = set()
        attrs_module_name = '.'.join(module_name_parts[:-1] + ['attributes'])
        __import__(attrs_module_name)
        cls.attributes = sys.modules[attrs_module_name].ATTRIBUTES
        for attr, props in cls.attributes.iteritems():
            model_attr_name = cls.model_name + "." + attr
            if 'collection' in props and not 'via' in props:
                raise ModelError(cls, "%s: collection does not define 'via'" % model_attr_name)
            if 'via' in props and not ('collection' in props or 'model' in props):
                raise ModelError(cls, "%s: defines 'via' property but not 'model' or 'collection'" % model_attr_name)
            if not isinstance(props.get('unique', False), bool):
                raise ModelError(cls, "%s: invalid value for 'unique'" % model_attr_name)
            if not isinstance(props.get('description', ''), basestring):
                raise ModelError(cls, "%s: invalid value for 'description'" % model_attr_name)

    @classmethod
    def __construct_relationships__(cls):
        """Constructs relationships defined by the model attributes.
        
        Parses the model attributes to determine relationships between this model and others and
        populates the :any:`associations` and :any:`references` members.
        """
        if hasattr(cls, 'attributes'):
            return
        cls.__class_init__()
        for attr, props in cls.attributes.iteritems():
            model_attr_name = cls.model_name + "." + attr
            via = props.get('via', None)
            foreign_cls = props.get('model', props.get('collection', None))
            if not foreign_cls:
                continue
            try:
                if not issubclass(foreign_cls, Controller):
                    raise TypeError
            except TypeError:
                raise ModelError(cls, "%s: Invalid foreign model controller: %r" % (model_attr_name, foreign_cls))
            foreign_cls.__class_init__()
            
            forward = (foreign_cls, via)
            reverse = (cls, attr)
            if not via:
                foreign_cls.references.add(reverse)
            else:
                foreign_cls.associations[via] = reverse
                foreign_model_attr_name = foreign_cls.model_name + "." + via
                try:
                    via_props = foreign_cls.attributes[via]
                except KeyError:
                    raise ModelError(cls, "%s: 'via' references undefined attribute '%s'" % 
                                     (model_attr_name, foreign_model_attr_name))
                via_attr_model = via_props.get('model', via_props.get('collection', None))
                if not via_attr_model:
                    raise ModelError(cls, "%s: 'via' on non-model attribute '%s'" %
                                     (model_attr_name, foreign_model_attr_name))
                if via_attr_model is not cls:
                    raise ModelError(cls, "Attribute '%s' referenced by 'via' in '%s' "
                                     "does not define 'collection' or 'model' of type '%s'" %
                                     (foreign_model_attr_name, attr, cls.model_name))
                try:
                    existing = cls.associations[attr]
                except KeyError:
                    cls.associations[attr] = forward
                else:
                    if existing != forward:
                        raise ModelError(cls, "%s: conflicting associations: '%s' vs. '%s'" % 
                                         (model_attr_name, existing, forward))
    
    def __init__(self, fields):
        """Initializes the controller instance.
        
        A :any:`Controller` instance is attached to a specific data record via the :any:`data`
        and possibly :any:`eid` members.

        Args:
            fields: A dictionary-like object with the optional `eid` attribute.
        """
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
    def _validate(cls, data):
        """Validates data against the model.
        
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
        if data is None:
            return None
        for key in data:
            if not key in cls.attributes:
                raise ModelError(cls, "no attribute named '%s'" % key)
        validated = {}
        for attr, props in cls.attributes.iteritems():
            # Check required fields and defaults
            try:
                validated[attr] = data[attr]
            except KeyError:
                if 'required' in props:
                    if props['required']:
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
                    foreign_model = props['model']
                except KeyError:
                    try:
                        foreign_model = props['collection']
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
            for attr in fields:
                if not attr in cls.attributes:
                    raise ModelError(cls, "Model '%s' has no attribute named '%s'" % (cls.model_name, attr))
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
    def construct_condition(cls, args, attr_defined=None, attr_undefined=None, attr_eq=None, attr_ne=None):
        """Constructs a compatibility condition, see :any:`check_compatibility`.
        
        The returned condition is a callable that accepts four arguments:
            * lhs (Controller): The left-hand side of the `check_compatibility` operation.
            * lhs_attr (str): Name of the attribute that defines the 'compat' property.
            * lhs_value: The value in the controlled data record of the attribute that defines the 'compat' property.
            * rhs (Controller): Controller of the data record we are checking against.
        
        The `condition` callable raises a :any:`ConfigurationError` if the compared attributes 
        are fatally incompatibile, i.e. the user's operation is guaranteed to fail with the chosen 
        records. It may emit log messages to indicate that the records are not perfectly compatible 
        but that the user's operation is still likely to succeed with the chosen records.
        
        See :any:`require`, :any:`encourage`, :any:`discourage`, :any:`exclude` for common conditions.
        
        args[0] specifies a model attribute to check.  If args[1] is given, it is a value to
        compare the specified attribute against or a callback function as described below.
        
        The remaining arguments are callback functions accepting these arguments:
            * lhs (Controller): The controller invoking `check_compatibility`.
            * lhs_attr (str): Name of the attribute that defines the 'compat' property.
            * lhs_value: Value of the attribute that defines the 'compat' property.
            * rhs (Controller): Controller we are checking against (argument to `check_compatibility`).
            * rhs_attr (str): The right-hand side attribute we are checking for compatibility.
        
        To enable complex conditions, args[1] may be a callback function.  In this case,
        args[1] must check attribute existance and value correctness and throw the appropriate
        exception and/or emit log messages.  See :py:func:`tau.model.measurement.intel_only` 
        for an example of such a callback function.
        
        Args:
            args (tuple): Attribute name in args[0] and, optionally, attribute value in args[1].
            attr_defined: Callback function to be invoked when the attribute is defined.
            attr_undefined: Callback function to be invoked when the attribute is undefined.
            attr_eq: Callback function to be invoked when the attribute is equal to args[1].
            attr_ne: Callback function to be invoked when the attribute is not equal to args[1].

        Returns:
            Callable condition object for use with :any:`check_compatibility`.
        """
        rhs_attr = args[0]
        try:
            checked_value = args[1]
        except IndexError:
            def condition(lhs, lhs_attr, lhs_value, rhs):
                if isinstance(rhs, cls):
                    if rhs_attr in rhs:
                        if attr_defined:
                            attr_defined(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
                    else:
                        if attr_undefined:
                            attr_undefined(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
        else:
            if callable(checked_value):
                def condition(lhs, lhs_attr, lhs_value, rhs):
                    if isinstance(rhs, cls): 
                        checked_value(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
            else:
                def condition(lhs, lhs_attr, lhs_value, rhs):
                    if isinstance(rhs, cls):
                        try:
                            rhs_value = rhs[rhs_attr]
                        except KeyError:
                            if attr_undefined:
                                attr_undefined(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
                        else:
                            if attr_eq:
                                if rhs_value == checked_value:
                                    attr_eq(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
                            elif attr_ne:
                                if rhs_value != checked_value:
                                    attr_ne(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
                            elif attr_defined:
                                attr_defined(lhs, lhs_attr, lhs_value, rhs, rhs_attr)
        return condition

    @classmethod
    def require(cls, *args):
        """Constructs a compatibility condition to enforce required conditions.
        
        The condition will raise a :any:`ConfigurationError` if the specified attribute is
        undefined or not equal to the specified value (if given).
        
        Args:
            *args: Corresponds to `args` in :any:`construct_condition`. 
        
        Returns:
            Callable condition object for use with :any:`check_compatibility`
            
        Examples:
            'have_cheese' must be True::
            
                CheeseShop.require('have_cheese', True)
             
            'have_cheese' must be set to any value::
                
                CheeseShop.require('have_cheese')
            
            The value of 'have_cheese' will be checked for correctness by 'cheese_callback'::
            
                CheeseShop.require('have_cheese', cheese_callback)
        """ 
        def attr_undefined(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            raise ConfigurationError("%s = %s in %s requires %s be defined in %s" % 
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name))
        def attr_ne(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            rhs_value = rhs[rhs_attr]
            raise ConfigurationError("%s = %s in %s requires %s = %s in %s" % 
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_value, rhs_name))
        return cls.construct_condition(args, attr_undefined=attr_undefined, attr_ne=attr_ne)

    @classmethod
    def encourage(cls, *args):
        """Constructs a compatibility condition to make recommendations.
        
        The condition will emit warnings messages if the specified attribute is
        undefined or not equal to the specified value (if given).
        
        Args:
            *args: Corresponds to `args` in :any:`construct_condition`. 
        
        Returns:
            Callable condition object for use with :any:`check_compatibility`
            
        Examples:
            'have_cheese' should be True::
            
                CheeseShop.encourage('have_cheese', True)
             
            'have_cheese' should be set to any value::
                
                CheeseShop.encourage('have_cheese')
            
            The value of 'have_cheese' will be checked for correctness by 'cheese_callback'::
            
                CheeseShop.encourage('have_cheese', cheese_callback)
        """
        def attr_undefined(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            LOGGER.warning("%s = %s in %s recommends %s be defined in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name)
        def attr_ne(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            rhs_value = rhs[rhs_attr]
            LOGGER.warning("%s = %s in %s recommends %s = %s in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_value, rhs_name)
        return cls.construct_condition(args, attr_undefined=attr_undefined, attr_ne=attr_ne)

    @classmethod
    def discourage(cls, *args):
        """Constructs a compatibility condition to make recommendations.
        
        The condition will emit warnings messages if the specified attribute is
        defined or equal to the specified value (if given).
        
        Args:
            *args: Corresponds to `args` in :any:`construct_condition`. 
        
        Returns:
            Callable condition object for use with :any:`check_compatibility`
            
        Examples:
            'have_cheese' should not be True::
            
                CheeseShop.discourage('have_cheese', True)
             
            'have_cheese' should not be set to any value::
                
                CheeseShop.discourage('have_cheese')
            
            The value of 'have_cheese' will be checked for correctness by 'cheese_callback'::
            
                CheeseShop.discourage('have_cheese', cheese_callback)
        """
        def attr_defined(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            LOGGER.warning("%s = %s in %s recommends %s be undefined in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name)
        def attr_eq(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            rhs_value = rhs[rhs_attr]
            LOGGER.warning("%s = %s in %s recommends against %s = %s in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_value, rhs_name)
        return cls.construct_condition(args, attr_defined=attr_defined, attr_eq=attr_eq)

    @classmethod
    def exclude(cls, *args):
        """Constructs a compatibility condition to enforce required conditions.
        
        The condition will raise a :any:`ConfigurationError` if the specified attribute is
        defined or equal to the specified value (if given).
        
        Args:
            *args: Corresponds to `args` in :any:`construct_condition`. 
        
        Returns:
            Callable condition object for use with :any:`check_compatibility`
            
        Examples:
            'yellow_cheese' must not be 'American'::
            
                CheeseShop.exclude('yellow_cheese', 'American')
             
            'blue_cheese' must not be set to any value::
                
                CheeseShop.exclude('blue_cheese')
            
            The value of 'have_cheese' will be checked for correctness by 'cheese_callback'::
            
                CheeseShop.exclude('have_cheese', cheese_callback)
        """
        def attr_defined(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            raise ConfigurationError("%s = %s in %s requires %s be undefined in %s" %
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name))
        def attr_eq(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.model_name.lower()
            rhs_name = rhs.model_name.lower()
            rhs_value = rhs[rhs_attr]
            raise ConfigurationError("%s = %s in %s is incompatible with %s = %s in %s" %
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_value, rhs_name))
        return cls.construct_condition(args, attr_defined=attr_defined, attr_eq=attr_eq)        

    def check_compatibility(self, rhs):
        """Test the controlled record for compatibility with another record.
        
        Operations combining data from multiple records (e.g. selecting a project configuration)
        must know that the records are mutually compatible.  This routine checks the 'compat'
        property of each attribute (if set) to enforce compatibility.  'compat' is a dictionary.
        The keys of 'compat' are values or callables and the values are tuples of compatibility
        conditions.  If the attribute with the 'compat' property is one of the key values then 
        the conditions are checked.  The general form of 'compat' is:
        ::
        
            {
            (value|callable): (condition, [condition, ...]),
            [(value|callable): (condition, [condition, ...]), ...]
            }
            
        Use tuples to join multiple conditions.  If only one condition is needed then you do
        not need to use a tuple.
        
        `value` may either be a literal value (e.g. True or "oranges") or a callable accepting
        one argument and returning either True or False.  The attribute's value is passed to the
        callable to determine if the listed conditions should be checked.  If `value` is a literal
        then the listed conditions are checked when the attribute's value matches `value`.     
        
        See :any:`require`, :any:`encourage`, :any:`discourage`, :any:`exclude` for common conditions.
        
        Args:
            rhs (Controller): Controller for the data record to check compatibility.
            
        Raises:
            ConfigurationError: The two records are not compatible.

        Examples:

            Suppose we have this data:
            ::
            
                Programmer.attributes = {
                    'hungry': {
                        'type': 'boolean',
                        'compat': {True: (CheeseShop.require('have_cheese', True),
                                          CheeseShop.encourage('chedder', 'Wisconsin'),
                                          ProgramManager.discourage('holding_long_meeting', True),
                                          Roommate.exclude('steals_food', True)}
                    }
                }

                bob = Programmer({'hungry': True})
                world_o_cheese = CheeseShop({'have_cheese': False, 'chedder': 'Wisconsin'})
                cheese_wizzard = CheeseShop({'have_cheese': True, 'chedder': 'California'})
                louis = ProgramManager({'holding_long_meeting': True})
                keith = Roommate({'steals_food': True})
                
            These expressions raise :any:`ConfigurationError`:
            ::
            
                bob.check_compatibility(world_o_cheese)   # Because have_cheese == False
                bob.check_compatibility(keith)            # Because steals_food == True
            
            These expressions generate warning messages:
            ::
            
                bob.check_compatibility(cheese_wizzard)   # Because chedder != Wisconsin
                bob.check_compatibility(louis)            # Because holding_long_meeting == True
                
            If ``bob['hungry'] == False`` or if the 'hungry' attribute were not set then all 
            the above expressions do nothing.
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
            for value, conditions in compat.iteritems():
                if (callable(value) and value(attr_value)) or attr_value == value: 
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


