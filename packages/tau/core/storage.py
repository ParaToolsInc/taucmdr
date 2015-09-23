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
from tau import logger
from tau import PROJECT_DIR, SYSTEM_PREFIX, USER_PREFIX
from tau.core.database import JsonDatabase, AbstractDatabase

LOGGER = logger.get_logger(__name__)


class Storage(AbstractDatabase):
    """TAU Commander's hirarchical storage system.
    
    Manages project records, software packages, and performance data in three repositories:
        * System: Globally readable, likely only writable by the system administrator.
          Ideal location for software installations.
        * User: User readable and writable.  Ideal location for configuration records 
          (i.e. Application) and fallback location for software installation.
        * Project: User readable and writable.  Location for project configurations and
          application performance data. 
    """
    
    def __init__(self, system_prefix, user_prefix):
        self.system_prefix = system_prefix
        self.user_prefix = user_prefix
        self.system_database = JsonDatabase(os.path.join(system_prefix, 'system.json'))
        self.user_database = JsonDatabase(os.path.join(user_prefix, 'user.json'))

    @property
    def project_database(self):
        """Gets the project database.
        
        Walks up the filesystem tree until a project directory is located.
        
        Returns:
            AbstractDatabase: A database object for project-level record storage
                              or None if the project directory was not found.
        """
        # pylint: disable=no-member,attribute-defined-outside-init
        try:
            return self._project_database
        except AttributeError:
            root = os.getcwd()
            lastroot = None
            while root != lastroot:
                dbfile = os.path.join(root, PROJECT_DIR, 'project.json')
                if os.path.exists(dbfile) and dbfile not in (self.user_database.dbfile, self.system_database.dbfile):
                    LOGGER.debug("Located project database at '%s'", dbfile)
                    self._project_database = JsonDatabase(dbfile)
                lastroot = root
                root = os.path.dirname(root)
            self._project_database = None
        return self._project_database
    
    def _apply(self, func, *args, **kwargs):
        found = None
        if self.project_database:
            found = getattr(self.project_database, func)(*args, **kwargs)
        if found is None:
            found = getattr(self.user_database, func)(*args, **kwargs)
        if found is None:
            found = getattr(self.system_database, func)(*args, **kwargs)
        return found

    def get(self, table_name, keys=None, match_any=False, eid=None):
        return self._apply('get', table_name, keys=keys, match_any=match_any, eid=eid)
        
    def search(self, table_name, keys=None, match_any=False):
        return self._apply('search', table_name, keys=keys, match_any=match_any)
        
    def match(self, table_name, field, regex=None, test=None):
        return self._apply('match', table_name, field, regex=regex, test=test)

    def contains(self, table_name, keys=None, match_any=False, eids=None):
        return self._apply('contains', table_name, keys=keys, match_any=match_any, eids=eids)

    def insert(self, table_name, fields):
        return self._apply('insert', table_name, fields)

    def update(self, table_name, fields, keys=None, match_any=False, eids=None):
        return self._apply('update', table_name, fields, keys=keys, match_any=match_any, eids=eids)

    def remove(self, table_name, keys=None, match_any=False, eids=None):
        return self._apply('remove', table_name, keys=keys, match_any=match_any, eids=eids)

    def purge(self, table_name):
        return self._apply('purge', table_name)

#USER_STORAGE = Storage(SYSTEM_PREFIX, USER_PREFIX)
USER_STORAGE = JsonDatabase(os.path.join(USER_PREFIX, 'local.json'))
