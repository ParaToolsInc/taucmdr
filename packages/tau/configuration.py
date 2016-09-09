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

import textwrap
from configobj import ConfigObj
from tau.storage import AbstractStorage, StorageError
from tau.storage.levels import ORDERED_LEVELS
from tau.storage.project import ProjectStorageError
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement



def get(key=None, storage=None):
    """Returns a dictionary of all configuration items or the value of one configuration item.
    
    If a storage object is given then returns the value(s) held in that storage.
    Otherwise, searches :any:`ORDERED_LEVELS` for the first storage containing ``key``.
    
    Args:
        key (str): Optional key string.
        storage (AbstractStorage): Optional storage container.
    
    Returns:
        dict: If ``key == None``, a dictionary of configuration items.
        object: If ``key != None``, the value mapped to ``key``.
        
    Raises:
        KeyError: no storage contains ``key`` or ``storage != None`` and ``key not in storage``.
    """
    if storage is not None:
        assert isinstance(storage, AbstractStorage)
        if key:
            return storage[key]
        else:
            return dict(storage.iteritems())
    else:
        if key:
            for storage in ORDERED_LEVELS:
                try:
                    return storage[key]
                except (ProjectStorageError, KeyError):
                    # Project storage hasn't been initialized yet, or default isn't set
                    continue
            raise KeyError
        else:
            items = {}
            for storage in reversed(ORDERED_LEVELS):
                try:
                    items.update(storage.iteritems())
                except StorageError:
                    # Storage hasn't been initialized yet
                    continue
            return items    


def put(key, value, storage=None):
    """Sets the value of a configuration item.
    
    If a storage object is given then sets ``key=value`` in that storage.
    Otherwise, searches :any:`ORDERED_LEVELS` for the first storage that 
    contains ``key`` and updates the value of ``key`` in that storage container.
    If no storage contains ``key`` then the value is set in :any:`ORDERED_LEVELS[0]`.
    
    Args:
        key (str): Key string.
        value (object): Value.
        storage (AbstractStorage): Optional storage container.
    """
    if storage is not None:
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
    if storage is not None:
        assert isinstance(storage, AbstractStorage)
        del storage[key]
    else:
        for storage in ORDERED_LEVELS:
            if key in storage:
                del storage[key]
                return
        del ORDERED_LEVELS[0][key]


def config_file_comment(msg, box=False, width=78, line_comment='#', line_char='='):
    """Formats a string as a configuration file comment.
    
    Adds a comment character to the start of each line and wraps lines at the specified
    line width.  Empty lines are preserved.
    
    Args:
        msg (str): Comment string.
        box (bool): If true, draw horizontal lines before and after the message and add some whitespace.
        width (int): Line width.
        line_comment (str): String that starts a line comment.
        line_char (str): Single character to replicate to form a horizontal line.
    
    Returns:
        list: Lines of the comment without terminating '\n' characters.
    """
    lines = []
    hline = line_char*(width-len(line_comment)-1)
    if box:
        lines.extend(['', hline])
    for line in msg.splitlines():
        if line.strip():
            lines.append(textwrap.fill(line, width=width-1, 
                                       initial_indent=line_comment+' ', subsequent_indent=line_comment+' '))
        else:
            lines.append(line_comment)
    if box:
        lines.append(hline)
    return lines


def default_config():
    """Build a configuration object with default values from :any:`tau.model`.
    
    Adds "Target", "Application", and "Measurement" sections defining default values for each model attribute.
    
    Returns:
        ConfigObj: Initialized configuration object.
    """
    config = ConfigObj(write_empty_values=True)
    for model in Application, Measurement, Target:
        config[model.name] = {}
        config.comments[model.name] = \
                config_file_comment("System-level %s configuration defaults.\n\n"
                                    "New target configurations will use these values as the default"
                                    " if no better value is available.\n" % model.name.lower(), box=True)
        for attr, props in sorted(model.attributes.iteritems()):
            if 'primary_key' not in props and 'collection' not in props: 
                config[model.name][attr] = props.get('default', '')
                config[model.name].comments[attr] = config_file_comment(props.get('description', ''))
    return config


def import_from_file(filepath, storage):
    """Import configuration options from a config file.
    
    Sets new or overrides existing configuration options.
    
    Args:
        filepath (str): Path to the configuration file.
        stoarge (AbstractStorage): Storage container.
    """ 
    config = ConfigObj(filepath)
    for section in config.sections:
        for key, val in config[section].iteritems():
            if not val:
                continue
            # pylint: disable=redefined-variable-type
            if isinstance(val, basestring):
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
            put('%s.%s' % (section, key), val, storage)


def open_config_file(filepath):
    """Return a configuration object initialized from values in `filepath` if it exists."""
    return ConfigObj(filepath, write_empty_values=True)

