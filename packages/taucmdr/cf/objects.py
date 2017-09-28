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
"""TAU Common Framework (CF) common objects."""
import six


class TrackedInstance(object):
    """Base class for classes that need to keep track of their instances.
    
    Each subclass tracks of its own instances separately.  Unliked :any:`KeyedRecordCreator`
    there is no restriction on the value of the class instance attributes.
    
    Example:
    ::

        class Foo(TrackedInstance):
            def __init__(self, x):
                self.x = x
                
        class Bar(Foo):
            def __init__(self, x, y):
                super(Bar,self).__init__(x)
                self.y = y
                
        fish = Foo('haddock')
        chips = Foo('potatoes')
        fries = Foo('potatoes')
        drink = Bar('water', 'sugar')
        
        for inst in Foo.all():
            print inst.x
            
        >>> haddock
        >>> potatoes
        >>> potatoes
        
        for inst in Bar.all():
            print inst.x
        
        >>> water
    """
    
    def __new__(cls, *args, **kwargs):
        """Ensure that __instances__ is set and track new instances."""
        instance = object.__new__(cls, *args, **kwargs)
        if "__instances__" not in cls.__dict__:
            cls.__instances__ = set()
        cls.__instances__.add(instance)
        return instance

    @classmethod
    def all(cls):
        """Iterate over class instances."""
        for instance in cls.__instances__:
            yield instance
    


class KeyedRecordCreator(type):
    """Metaclass to create a new :any:`KeyedRecord` instance.
    
    Change object creation proceedure so that only one instance of a :any:`KeyedRecord`
    exists for a given key argument.  Overridding ``__new__`` would be less creepy,
    but then we can't prevent ``__init__`` from being called on the returned class instance,
    i.e. the instance returned is reinitialized every time the it is retrieved.  Using
    this metaclass guarantees we call ``__new__`` and ``__init__`` only once per class instance.
    
    To learn more about metaclasses:
    * http://docs.python.org/2/reference/datamodel.html
    * http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    * http://stackoverflow.com/questions/100003/what-is-a-metaclass-in-python
    """
    def __new__(mcs, name, bases, dct):
        """Set ``__instances__`` attribute as soon as the class is created.
        
        We do this in ``__new__`` so that each subclass has its own ``__instances__`` attribute.
        This is how we keep subclass instances from being listed among their base class instances.
        """
        dct['__instances__'] = {}
        return type.__new__(mcs, name, bases, dct)
    
    def __call__(cls, *args, **kwargs):
        """Create the new instance."""
        key = args[0]
        try:
            instance = cls.__instances__[key]
        except KeyError:
            instance = super(KeyedRecordCreator, cls).__call__(*args, **kwargs)
            cls.__instances__[key] = instance
        return instance


class KeyedRecord(object):
    """Data record with a unique key.
    
    Subclasses must declare a ``__key__`` member defining the attribute to be used as the key.
    The first parameter to __init__ must be the key value for the new instances. Only one 
    instance of a :any:`KeyedRecord` subclass exists per key.  Calling the constructor with 
    a previously used key will return the existing instance, unmodified.  
    
    Example:
    ::

        class Foo(KeyedRecord):
            def __init__(self, a):
                self.a = a
            
        potato = Foo('vegtable')
        carrot = Foo('vegtable')
        steak = Foo('meat')
        
        for inst in Foo.all():
            print inst.a
            
        >>> vegtable
        >>> meat
        
        potato is carrot
        >>> True
        
        carrot is steak
        >>> False
    """
    # Some members of this class are set by the metaclass __new__ method. 
    # pylint: disable=no-member
    
    __metaclass__ = KeyedRecordCreator
    
    def __str__(self):
        return str(getattr(self, self.__key__))

    def __eq__(self, other):
        return self is other
    
    def __len__(self):
        return len(getattr(self, self.__key__))

    @classmethod
    def all(cls):
        """Iterate over class instances."""
        for instance in six.itervalues(cls.__instances__):
            yield instance
    
    @classmethod
    def keys(cls):
        """Get the name of the key field in all instances.
        
        Returns:
            list: All instance keys.
        """ 
        return cls.__instances__.keys()
    
    @classmethod
    def find(cls, key):
        """Find an instance.
        
        Args:
            key: An instance key value.
            
        Raises:
            KeyError: No instance has this key value.
        
        Returns:
            KeyedRecord: The instance with the matching key value.
        """
        return cls.__instances__[key]
    
