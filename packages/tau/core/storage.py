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
"""Multi-level storage system.

TODO: Docs
"""

import os
from tau import logger, TAU_HOME
from tau.error import ConfigurationError
from tau.core.database import JsonDatabase, AbstractDatabase


LOGGER = logger.get_logger(__name__)

SYSTEM_PREFIX = os.path.join(TAU_HOME, '.system')
"""str: Absolute path to system-level TAU Commander files."""

USER_PREFIX = os.path.join(os.path.expanduser('~'), '.tau')
"""str: Absolute path to user-level TAU Commander files."""

PROJECT_DIR = '.tau'
"""str: Name of the directory containing TAU Commander project files."""


class Storage(object):
    """Storage location for records and files.
    
    Pairs a database instance with a file system path.
    """
    
    def __init__(self, prefix, database):
        self.prefix = prefix
        self.database = database

        
def system_storage():
    """System-level record and file storage.
    
    System-level records are globally readable and writable, depending on the user's 
    system access level.  System-level is a good place for software package installations
    and some system-specific records, i.e. compiler configurations.
    
    If the system-level database does not exist then we will attempt to create it. If it
    can't be created then this function issues a warning and returns None.
    
    Returns:
        Storage: System-level storage or None if no system-level database exists and it
                 cannot be created.
    """      
    try:
        return system_storage.instance
    except AttributeError:
        try:
            database = JsonDatabase(os.path.join(SYSTEM_PREFIX, 'system.json'))
        except ConfigurationError as err:
            LOGGER.warning(err)
            system_storage.instance = None
        else:
            system_storage.instance = Storage(SYSTEM_PREFIX, database)
        return system_storage.instance


def user_storage():
    """User-level record and file storage.
    
    User-level records are readable and writable by (at least) the user.  User-level is
    where software is installed when the user doesn't have write access to the system-level
    filesystem prefix.  It's also a good place for user-specific records, i.e. preferences
    or encrypted login credentials.
    
    If the user-level database does not exist then we will attempt to create it. If it
    can't be created then this function issues a warning and returns None.
    
    Returns:
        Storage: User-level storage or None if no user-level database exists and it
                 cannot be created.
    """      
    try:
        return user_storage.instance
    except AttributeError:
        try:
            database = JsonDatabase(os.path.join(USER_PREFIX, 'user.json'))
        except ConfigurationError as err:
            LOGGER.warning(err)
            user_storage.instance = None
        else:
            user_storage.instance = Storage(USER_PREFIX, database)
        return user_storage.instance
    

def project_storage():
    """Project-level record and file storage.
    
    Project-level records define the project and its member components.  The user may also
    want to install software packages at the project level to avoid quotas or in situations
    where :any:`USER_PREFIX` is not accessible from cluster compute nodes.
    
    If the project-level database does not exist then this function returns None.

    Returns:
        Storage: Project-level storage or None if no project-level database exists.
    """
    try:
        return project_storage.instance
    except AttributeError:
        root = os.getcwd()
        lastroot = None
        while root and root != lastroot:
            if root not in [USER_PREFIX, SYSTEM_PREFIX]:
                prefix = os.path.join(root, PROJECT_DIR)
                dbfile = os.path.join(prefix, 'project.json')
                if os.path.exists(dbfile):
                    LOGGER.debug("Located project database at '%s'", dbfile)
                    try:
                        database = JsonDatabase(dbfile)
                    except ConfigurationError as err:
                        LOGGER.debug(err)
                        continue
                    else:
                        project_storage.instance = Storage(prefix, database)
                        break
            lastroot = root
            root = os.path.dirname(root)
        else:
            project_storage.instance = None
    return project_storage.instance

