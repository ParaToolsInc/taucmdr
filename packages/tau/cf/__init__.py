#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""


class TrackedInstance(object):
    """Base class for classes that need to keep track of their instances.
    
    Each subclass of base will keep track of its own instances separately.
    """
    
    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls, *args, **kwargs)
        if "__instances__" not in cls.__dict__:
            cls.__instances__ = set()
        cls.__instances__.add(instance)
        return instance

    @classmethod
    def all(cls):
        for instance in cls.__instances__:
            yield instance


class KeyedRecordCreator(type):
    """Metaclass to create a new keyed record.
    
    Change object creation proceedure so that only one instance of a KeyedRecord
    subclass exists for each key argument.
    """
    def __new__(mcs, name, bases, dct):
        dct['__instances__'] = {}
        return type.__new__(mcs, name, bases, dct)
    
    def __call__(cls, *args, **kwargs):
        key = kwargs.get(cls.__key__, args[0])
        try:
            instance = cls.__instances__[key]
        except KeyError:
            instance = super(KeyedRecordCreator,cls).__call__(*args, **kwargs)
            cls.__instances__[key] = instance
        return instance


class KeyedRecord(object):
    """Data record with a unique key.
    
    Subclasses must declare a __key__ member defining the attribute to be used as the key.
    Subclass constructors may use the 'key' keyword argument to set the key value or, if 
    the 'key' keyword argument is not present, calls to the subclass constructor must
    pass the new key value as the first argument.
    
    Only one instance of a KeyedRecord subclass exists per key.  Creating a new instance 
    with a previously used key will return the existing instance.  For example:
    
    class Derived(KeyedRecord):
        def __init__(a):
            self.a = a
        
    x = Derived('a')
    y = Derived('a')
    z = Derived('b')
    x is y  ==>  True
    x is z  ==>  False
    """
    
    __metaclass__ = KeyedRecordCreator
    
    @classmethod
    def all(cls):
        for instance in cls.__instances__.itervalues():
            yield instance
    
    @classmethod
    def keys(cls):
        return cls.__instances__.keys()
    
    @classmethod
    def find(cls, key):
        return cls.__instances__[key]
    
    def __str__(self):
        return str(getattr(self, self.__key__))

    def __eq__(self, other):
        return self is other
    
    def __len__(self):
        return len(getattr(self, self.__key__))
