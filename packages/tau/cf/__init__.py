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
from weakref import WeakSet, WeakValueDictionary


class TrackedInstance(object):
    """Base class for classes that need to keep track of their instances.
    
    Each subclass of base will keep track of its own instances separately.
    We use weak references to the class's instances to so that the bookkeeping code 
    doesn't prevent instances from garbage collected.
    """
    
    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls, *args, **kwargs)
        if "_INSTANCES" not in cls.__dict__:
            cls._INSTANCES = WeakSet()
        cls._INSTANCES.add(instance)
        return instance

    @classmethod
    def all(cls):
        for instance in cls._INSTANCES:
            yield instance
    

class KeyedRecord(TrackedInstance):
    """Data record with a unique key.
    
    Subclasses must declare a KEY member defining the attribute to be used as the key.
    Subclass constructors may use the 'key' keyword argument to set the key value or.
    If the 'key' keyword argument is not present, calls to the subclass constructor must
    pass the new key value as the first argument.
    
    Only one instance of a KeyedRecord subclass exists per key.  Creating a new instance 
    with a previously used key will return the existing instance. 
    """
    
    def __new__(cls, *args, **kwargs):
        key = kwargs.get(cls.KEY, args[0])
        if '_INSTANCES' not in cls.__dict__:
            cls._INSTANCES = WeakValueDictionary()
        try:
            instance = cls._INSTANCES[key]
        except KeyError:
            instance = object.__new__(cls)
            cls._INSTANCES[key] = instance
        return instance
    
    @classmethod
    def all(cls):
        for instance in cls._INSTANCES.itervalues():
            yield instance
    
    @classmethod
    def keys(cls):
        return cls._INSTANCES.keys()
    
    @classmethod
    def find(cls, key):
        return cls._INSTANCES[key]
    
    def __str__(self):
        return getattr(self, self.KEY)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (getattr(other, other.KEY) == getattr(self, self.KEY))
    
    def __len__(self):
        return len(getattr(self, self.KEY))
