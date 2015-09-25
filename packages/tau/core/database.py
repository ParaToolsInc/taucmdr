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
"""Persistant record storage.

Provides an abstract base class (ABC) for document-based databases and a simple
implementation based on `TinyDB`_.

.. _TinyDB: http://pypi.python.org/pypi/tinydb/
"""

import os
import tinydb
from abc import ABCMeta, abstractmethod
from tau import logger, util
from tau.error import ConfigurationError


LOGGER = logger.get_logger(__name__)


class AbstractDatabase(object):
    """Abstract base class for a persistant record storage system."""
    
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def count(self, table_name):
        """Count the records in the table.
        
        Args:
            table_name (str): Name of the table to search.
            
        Returns:
            int: Number of records in the table.
        """
    
    @abstractmethod
    def get(self, table_name, keys=None, match_any=False, eid=None):
        """Find a single record.
        
        Either `keys` or `eid` should be specified, not both.  If `keys` is given,
        then every attribute listed in `keys` must have the given value. If `eid`
        is given, return the record with that eid.  If neither is given, return None.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Fields to match.
            eid (list): Record identifier to match.
            match_any (bool): If True then any key may match or if False then all keys must match.

        Returns:
            tuple: (eid, data) matching data record or (None, None) if no such record exists.
        """

    @abstractmethod
    def search(self, table_name, keys=None, match_any=False):
        """Find multiple records.
        
        If `keys` is not specified then return all records.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Fields to match.
            match_any (bool): If True then any key may match or if False then all keys must match.

        Returns:
            list: Matching data records as (eid, data) tuples.
        """

    @abstractmethod
    def match(self, table_name, field, regex=None, test=None):
        """Find records where 'field' matches 'regex'.
        
        Either `regex` or `test` may be specified, not both.  If `regex` is given,
        then all records with `field` matching the regular expression are returned.
        If test is given then all records with `field` set to a value that caues
        `test` to return True are returned. If neither is given, return all records. 
        
        Args:
            table_name (str): Name of the table to search.
            field (string): Name of the data field to match.
            regex (string): Regular expression string.
            test: A callable expression returning a boolean value.  
            
        Returns:
            list: Matching data records as (eid, data) tuples.
        """

    @abstractmethod
    def contains(self, table_name, keys=None, match_any=False, eids=None):
        """Check if the specified table contains at least one matching record.
        
        Just like :any:`Database.search`, except only tests if the record exists without retrieving any data.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
            
        Returns:
            bool: True if a record exists, False otherwise.
        """

    @abstractmethod
    def insert(self, table_name, fields):
        """Create a new record.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (dict): Data to record.
            
        Returns:
            int: The new record's element identifier (eid).                 
        """

    @abstractmethod
    def update(self, table_name, fields, keys=None, match_any=False, eids=None):
        """Update existing records.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (dict): Data to record.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """

    @abstractmethod        
    def unset(self, table_name, fields, keys=None, match_any=False, eids=None):
        """Update existing records by unsetting fields.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (list): Fields to unset.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """

    @abstractmethod
    def remove(self, table_name, keys=None, match_any=False, eids=None):
        """Delete records.
        
        Args:
            table_name (str): Name of the table to operate on.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """

    @abstractmethod
    def purge(self, table_name):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.
        """


class JsonDatabase(AbstractDatabase):
    """A persistant, transactional record storage system.  
    
    Uses :py:class:`TinyDB` to store and retrieve data as JSON strings.
    
    Attributes:
        dbfile (str): Absolute path to database file.
        database (TinyDB): Database handle.
    """
    
    class JsonFileStorage(tinydb.JSONStorage):
        """Allow read-only as well as read-write access to the JSON file."""
        def __init__(self, path):
            try:
                super(JsonDatabase.JsonFileStorage, self).__init__(path)
            except IOError:
                LOGGER.debug("Failed to open %s as read-write, attempting read-only", path)
                self.path = path
                self._handle = open(path, 'r')
                self.readonly = True
            else:
                self.readonly = False

        def write(self, *args, **kwargs):
            if self.readonly:
                raise ConfigurationError("Cannot write to '%s'" % self.path, "Check that you have `write` access.")
            else:
                super(JsonDatabase.JsonFileStorage, self).write(*args, **kwargs)

    def __init__(self, dbfile):
        """Initializes the Database instance.
        
        Args:
            dbfile (str): Absolute path to the TinyDB database file.
                          Parent directories will be created as needed.
                          
        Raises:
            ConfigurationError: The database file could not be created.
        """
        self._transaction_count = 0
        self._db_copy = None
        self.dbfile = dbfile
        prefix = os.path.dirname(dbfile)
        try:
            util.mkdirp(prefix)
        except IOError:
            raise ConfigurationError("Cannot create directory '%s'" % prefix, 
                                     "Check that you have `write` access")
        try:
            self.database = tinydb.TinyDB(self.dbfile, storage=JsonDatabase.JsonFileStorage)
        except IOError:
            raise ConfigurationError("Cannot create '%s'" % self.dbfile,
                                     "Check that you have `write` access")
        if not util.file_accessible(self.dbfile):
            raise ConfigurationError("Database file '%s' exists but cannot be read." % self.dbfile,
                                     "Check that you have `read` access")
        LOGGER.debug("Opened '%s' for read/write", self.dbfile)

    def __enter__(self):
        """Initiates the database transaction."""
        # Use protected methods to duplicate database in memory rather than on disk.
        # pylint: disable=protected-access
        if self._transaction_count == 0:
            self._db_copy = self.database._read()
        self._transaction_count += 1
        return self

    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""
        # Use protected methods to duplicate database in memory rather than on disk.
        # pylint: disable=protected-access
        self._transaction_count -= 1
        if ex_type and self._transaction_count == 0:
            self.database._write(self._db_copy)
            self._db_copy = None

    @staticmethod
    def _query(keys, match_any):
        """Returns a query object from a dictionary of keys.
        
        Args:
            keys (dict): data keys to query.
            match_any (bool): If True then any key may match or if False then all keys must match.
        
        Returns:
            Query: The query object. 
        """
        def _and(lhs, rhs): 
            return lhs & rhs
        def _or(lhs, rhs): 
            return lhs | rhs
        join = _or if match_any else _and
        itr = keys.iteritems()
        key, val = itr.next()
        query = (tinydb.where(key) == val)
        for key, value in itr:
            query = join(query, (tinydb.where(key) == value))
        return query
    
    @staticmethod
    def _tuple_list(records):
        return [(record.eid, record) for record in records]

    def count(self, table_name):
        """Count the records in the table.
        
        Args:
            table_name (str): Name of the table to search.
            
        Returns:
            int: Number of records in the table.
        """
        return len(self.database.table(table_name))
        
    def get(self, table_name, keys=None, match_any=False, eid=None):
        """Find a single record.
        
        Either `keys` or `eid` should be specified, not both.  If `keys` is given,
        then every attribute listed in `keys` must have the given value. If `eid`
        is given, return the record with that eid.  If neither is given, return None.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Fields to match.
            eid (list): Record identifier to match.
            match_any (bool): If True then any key may match or if False then all keys must match.

        Returns:
            tuple: (eid, data) matching data record or (None, None) if no such record exists.
        """
        table = self.database.table(table_name)
        if eid is not None:
            LOGGER.debug("%r: get(eid=%r)", table_name, eid)
            found = table.get(eid=eid)
        elif keys is not None:
            LOGGER.debug("%r: get(keys=%r)", table_name, keys)
            found = table.get(self._query(keys, match_any))
        else:
            found = None
        if found:
            return found.eid, found
        else:
            return None, None

    def search(self, table_name, keys=None, match_any=False):
        """Find multiple records.
        
        If `keys` is not specified then return all records.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Fields to match.
            match_any (bool): If True then any key may match or if False then all keys must match.

        Returns:
            list: Matching data records as (eid, data) tuples.
        """
        table = self.database.table(table_name)
        if keys:
            LOGGER.debug("%r: search(keys=%r)", table_name, keys)
            return self._tuple_list(table.search(self._query(keys, match_any)))
        else:
            LOGGER.debug("%r: all()", table_name)
            return self._tuple_list(table.all())

    def match(self, table_name, field, regex=None, test=None):
        """Find records where 'field' matches 'regex'.
        
        Either `regex` or `test` may be specified, not both.  If `regex` is given,
        then all records with `field` matching the regular expression are returned.
        If test is given then all records with `field` set to a value that caues
        `test` to return True are returned. If neither is given, return all records. 
        
        Args:
            table_name (str): Name of the table to search.
            field (string): Name of the data field to match.
            regex (string): Regular expression string.
            test: A callable expression returning a boolean value.  
            
        Returns:
            list: Matching data records as (eid, data) tuples.
        """
        table = self.database.table(table_name)
        if test is not None:
            LOGGER.debug('%r: search(where(%r).test(%r))', table_name, field, test)
            return self._tuple_list(table.search(tinydb.where(field).test(test)))
        elif regex is not None:
            LOGGER.debug('%r: search(where(%r).matches(%r))', table_name, field, regex)
            return self._tuple_list(table.search(tinydb.where(field).matches(regex)))
        else:
            LOGGER.debug("%r: search(where(%r).matches('.*'))", table_name, field)
            return self._tuple_list(table.search(tinydb.where(field).matches('.*')))

    def contains(self, table_name, keys=None, match_any=False, eids=None):
        """Check if the specified table contains at least one matching record.
        
        Just like :any:`Database.search`, except only tests if the record exists without retrieving any data.
        
        Args:
            table_name (str): Name of the table to search.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
            
        Returns:
            bool: True if a record exists, False otherwise.          
        """
        table = self.database.table(table_name)
        if eids is not None:
            LOGGER.debug("%r: contains(eids=%r)", table_name, eids)
            if isinstance(eids, list):
                return table.contains(eids=eids)
            else:
                return table.contains(eids=[eids])
        elif keys:
            LOGGER.debug("%r: contains(keys=%r)", table_name, keys)
            return table.contains(self._query(keys, match_any))
        else:
            return False

    def insert(self, table_name, fields):
        """Create a new record.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (dict): Data to record.
            
        Returns:
            int: The new record's identifier.                 
        """
        LOGGER.debug("%r: Inserting %r", table_name, fields)
        return self.database.table(table_name).insert(fields)

    def update(self, table_name, fields, keys=None, match_any=False, eids=None):
        """Update existing records.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (dict): Data to record.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """
        table = self.database.table(table_name)
        if eids is not None:
            LOGGER.debug("%s: update(%r, eids=%r)", table_name, fields, eids)
            if isinstance(eids, list):
                table.update(fields, eids=eids)
            else:
                table.update(fields, eids=[eids])
        else:
            LOGGER.debug("%s: update(%r, keys=%r)", table_name, fields, keys)
            table.update(fields, self._query(keys, match_any))

    def unset(self, table_name, fields, keys=None, match_any=False, eids=None):
        """Update existing records by unsetting fields.
        
        Args:
            table_name (str): Name of the table to operate on.
            fields (list): Fields to unset.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """
        table = self.database.table(table_name)
        if eids is not None:
            LOGGER.debug("%s: unset(%r, eids=%r)", table_name, fields, eids)
            if not isinstance(eids, list):
                eids = [eids]
            for field in fields:
                table.update(tinydb.operations.delete(field), eids=eids)
        else:
            LOGGER.debug("%s: update(%r, keys=%r)", table_name, fields, keys)
            for field in fields:
                table.update(tinydb.operations.delete(field), self._query(keys, match_any))

    def remove(self, table_name, keys=None, match_any=False, eids=None):
        """Delete records.
        
        Args:
            table_name (str): Name of the table to operate on.
            keys (dict): Attributes to match.
            match_any (bool): If True then any key may match or if False then all keys must match.
            eids (list): Record identifiers to match.
        """
        table = self.database.table(table_name)
        if eids is not None:
            LOGGER.debug("%s: remove(eids=%r)", table_name, eids)
            if isinstance(eids, list):
                table.remove(eids=eids)
            else:
                table.remove(eids=[eids])
        else:
            LOGGER.debug("%s: remove(keys=%r)", table_name, keys)
            table.remove(self._query(keys, match_any))

    def purge(self, table_name):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.
        """
        LOGGER.debug("%s: purge()", table_name)
        self.database.table(table_name).purge()
