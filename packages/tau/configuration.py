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
"""TAU Commander installation configuration.

TODO: Docs
"""

from tau import logger
from tau.storage import AbstractStorage
from tau.storage.levels import ORDERED_LEVELS
from tau.storage.project import ProjectStorageError

LOGGER = logger.get_logger(__name__)


def get(key, storage=None):
    """Returns the value of a configuration item.
    
    If a storage object is given then returns the value held in that storage.
    Otherwise, searches :any:`ORDERED_LEVELS` for the first storage containing ``key``.
    
    Args:
        key (str): Key string.
        storage (AbstractStorage): Optional storage container.
    
    Returns:
        str: The value mapped to ``key``.
        
    Raises:
        KeyError: no storage contains ``key`` or ``storage != None`` and ``key not in storage``.
    """
    if storage:
        assert isinstance(storage, AbstractStorage)
        return storage[key]
    else:
        for storage in ORDERED_LEVELS:
            try:
                return storage[key]
            except (ProjectStorageError, KeyError):
                # Project storage hasn't been initialized yet, or default isn't set
                continue
        raise KeyError
    

def put(key, value, storage=None):
    """Sets the value of a configuration item.
    
    If a storage object is given then sets ``key=value`` in that storage.
    Otherwise, searches :any:`ORDERED_LEVELS` for the first storage that 
    contains ``key`` and updates the value of ``key`` in that storage container.
    If no storage contains ``key`` then the value is set in :any:`ORDERED_LEVELS[0]`.
    
    Args:
        key (str): Key string.
        value (str): Value string.
        storage (AbstractStorage): Optional storage container.
    """
    if storage:
        assert isinstance(storage, AbstractStorage)
        storage[key] = value
    else:
        for storage in ORDERED_LEVELS:
            if key in storage:
                storage[key] = value
                return
        ORDERED_LEVELS[0][key] = value
            

def delete(key, storage=None):
    """Unsets the value of a configuration item.
    
    If a storage object is given then unsets ``key`` in that storage.
    Otherwise, searches :any:`ORDERED_LEVELS` for the first storage that 
    contains ``key`` and unsets ``key`` in that storage container.  
    If no storage contains ``key`` then the value is unset in :any:`ORDERED_LEVELS[0]`.
    
    Args:
        key (str): Key string.
        storage (AbstractStorage): Optional storage container.

    Raises:
        KeyError: no storage contains ``key`` or ``storage != None`` and ``key not in storage``.
    """
    if storage:
        assert isinstance(storage, AbstractStorage)
        del storage[key]
    else:
        for storage in ORDERED_LEVELS:
            if key in storage:
                del storage[key]
                return
        del ORDERED_LEVELS[0][key]
