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
"""TODO: FIXME: Docs"""

from tau import logger
from tau.error import ConfigurationError, ModelError, InternalError
from tau.mvc.controller import Controller

LOGGER = logger.get_logger(__name__)


class ModelMeta(type):
    """Metaclass TODO: FIXME: Docs"""

    def __new__(mcs, name, bases, dct):
        if dct['__module__'] != __name__:
            if dct.get('__controller__', NotImplemented) is NotImplemented:
                dct['__controller__'] = Controller
            if '__attributes__' not in dct:
                raise InternalError("Model class %s does not define classmethod __attributes__" % name)
            if dct.get('name', NotImplemented) is NotImplemented:
                dct['name'] = name
            if dct.get('key_attribute', NotImplemented) is NotImplemented:
                dct['key_attribute'] = None
            dct.update({'associations': dict(), 'references': set()}) 
        return type.__new__(mcs, name, bases, dct)

    @property
    def attributes(cls):
        try:
            return cls._attributes
        except AttributeError:
            cls._attributes = cls.__attributes__()
            cls._construct_relationships()
            return cls._attributes 


class Model(object):
    """The "M" in `MVC`_.
    
    TODO: Docs    

    Attributes:
        name (str): Name of the model.
        key_attribute (str): Name of an attribute that serves as a unique identifier. 
        attributes (dict): Model attributes.
        references (set): (Controller, str) tuples listing foreign models referencing this model.  
        associations (dict): (Controller, str) tuples keyed by attribute name defining attribute associations.
        record (Record): Model data record.
        
    .. _MVC: https://en.wikipedia.org/wiki/Model-view-controller
    """
    
    __metaclass__ = ModelMeta
    __controller__ = NotImplemented
    __attributes__ = NotImplemented
    name = NotImplemented
    key_attribute = NotImplemented
    associations = NotImplemented
    references = NotImplemented
    
    def __init__(self, record):
        self.record = record
        
    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        raise InternalError("Use controller(storage).update() to alter records")
 
    def __delitem__(self, key):
        raise InternalError("Use controller(storage).update() to alter records")
 
    def __iter__(self):
        return iter(self.record)
 
    def __len__(self):
        return len(self.record)
    
    def __str__(self):
        return str(self.record)
    
    @classmethod
    def controller(cls, storage):
        return cls.__controller__(cls, storage)
    
    @classmethod
    def _construct_relationships(cls):
        for attr, props in cls.attributes.iteritems():
            model_attr_name = cls.name + "." + attr
            if 'collection' in props and not 'via' in props:
                raise ModelError(cls, "%s: collection does not define 'via'" % model_attr_name)
            if 'via' in props and not ('collection' in props or 'model' in props):
                raise ModelError(cls, "%s: defines 'via' property but not 'model' or 'collection'" % model_attr_name)
            if not isinstance(props.get('unique', False), bool):
                raise ModelError(cls, "%s: invalid value for 'unique'" % model_attr_name)
            if not isinstance(props.get('description', ''), basestring):
                raise ModelError(cls, "%s: invalid value for 'description'" % model_attr_name)

            via = props.get('via', None)
            foreign_cls = props.get('model', props.get('collection', None))
            if not foreign_cls:
                continue
            try:
                if not issubclass(foreign_cls, Model):
                    raise TypeError
            except TypeError:
                raise ModelError(cls, "%s: Invalid foreign model controller: %r" % (model_attr_name, foreign_cls))
            
            forward = (foreign_cls, via)
            reverse = (cls, attr)
            if not via:
                foreign_cls.references.add(reverse)
            else:
                foreign_cls.associations[via] = reverse
                foreign_model_attr_name = foreign_cls.name + "." + via
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
                                     (foreign_model_attr_name, attr, cls.name))
                try:
                    existing = cls.associations[attr]
                except KeyError:
                    cls.associations[attr] = forward
                else:
                    if existing != forward:
                        raise ModelError(cls, "%s: conflicting associations: '%s' vs. '%s'" % 
                                         (model_attr_name, existing, forward))

    @classmethod
    def validate(cls, data):
        """Validates data against the model.
        
        Args:
            data (dict): Data to validate, may be None.

        Returns:
            dict: Validated data or None if `data` is None.
            
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
          
    @classmethod
    def construct_condition(cls, args, attr_defined=None, attr_undefined=None, attr_eq=None, attr_ne=None):
        """Constructs a compatibility condition, see :any:`check_compatibility`.
        
        The returned condition is a callable that accepts four arguments:
            * lhs (Model): The left-hand side of the `check_compatibility` operation.
            * lhs_attr (str): Name of the attribute that defines the 'compat' property.
            * lhs_value: The value of the attribute that defines the 'compat' property.
            * rhs (Model): Controller of the data record we are checking against.
        
        The `condition` callable raises a :any:`ConfigurationError` if the compared attributes 
        are fatally incompatibile, i.e. the user's operation is guaranteed to fail with the chosen 
        records. It may emit log messages to indicate that the records are not perfectly compatible 
        but that the user's operation is still likely to succeed with the chosen records.
        
        See :any:`require`, :any:`encourage`, :any:`discourage`, :any:`exclude` for common conditions.
        
        args[0] specifies a model attribute to check.  If args[1] is given, it is a value to
        compare the specified attribute against or a callback function as described below.
        
        The remaining arguments are callback functions accepting these arguments:
            * lhs (Model): The model invoking `check_compatibility`.
            * lhs_attr (str): Name of the attribute that defines the 'compat' property.
            * lhs_value: Value of the attribute that defines the 'compat' property.
            * rhs (Model): Model we are checking against (argument to `check_compatibility`).
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
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
            raise ConfigurationError("%s = %s in %s requires %s be defined in %s" % 
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name))
        def attr_ne(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
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
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
            LOGGER.warning("%s = %s in %s recommends %s be defined in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name)
        def attr_ne(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
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
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
            LOGGER.warning("%s = %s in %s recommends %s be undefined in %s",
                           lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name)
        def attr_eq(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
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
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
            raise ConfigurationError("%s = %s in %s requires %s be undefined in %s" %
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_name))
        def attr_eq(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
            lhs_name = lhs.name.lower()
            rhs_name = rhs.name.lower()
            rhs_value = rhs[rhs_attr]
            raise ConfigurationError("%s = %s in %s is incompatible with %s = %s in %s" %
                                     (lhs_attr, lhs_value, lhs_name, rhs_attr, rhs_value, rhs_name))
        return cls.construct_condition(args, attr_defined=attr_defined, attr_eq=attr_eq)        

    def check_compatibility(self, rhs):
        """Test this record for compatibility with another record.
        
        Operations combining data from multiple records must know that the records are mutually 
        compatible.  This routine checks the 'compat' property of each attribute (if set) to enforce
        compatibility.  'compat' is a dictionary where the keys are values or callables and the 
        values are tuples of compatibility conditions.  If the attribute with the 'compat' property
        is one of the key values then the conditions are checked.  The general form of 'compat' is::
        
            {
            (value|callable): (condition, [condition, ...]),
            [(value|callable): (condition, [condition, ...]), ...]
            }
            
        Use tuples to join multiple conditions.  If only one condition is needed then you do
        not need to use a tuple.
        
        'value' may either be a literal value (e.g. True or "oranges") or a callable accepting
        one argument and returning either True or False.  The attribute's value is passed to the
        callable to determine if the listed conditions should be checked.  If 'value' is a literal
        then the listed conditions are checked when the attribute's value matches 'value'.     
        
        See :any:`require`, :any:`encourage`, :any:`discourage`, :any:`exclude` for common conditions.
        
        Args:
            rhs (Model): Check compatibility with this data record.
            
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
                
            These expressions raise :any:`ConfigurationError`::
            
                bob.check_compatibility(world_o_cheese)   # Because have_cheese == False
                bob.check_compatibility(keith)            # Because steals_food == True
            
            These expressions generate warning messages::
            
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

