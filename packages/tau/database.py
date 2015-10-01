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
import json
from abc import ABCMeta, abstractmethod
from tau import logger, util
from tau.error import ConfigurationError


LOGGER = logger.get_logger(__name__)
    

class AbstractDatabase(object):
    """Abstract base class for a persistant record storage system."""
    
    __metaclass__ = ABCMeta
    
    Record = NotImplemented
    """A database record (a.k.a. "document").
    
    The constructor must be able to set the element ID and data directly via::
        Record(eid=eid, data=data, *args, **kwargs)
    
    or::
        Record(element=element, *args, **kwargs)
    
    Attributes:
        ElementIdentifier: Type of the element identifier.
        eid: Element identifier.
    """

    @abstractmethod
    def __enter__(self):
        """Initiates the database transaction."""

    @abstractmethod
    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""

    @abstractmethod
    def table(self, table_name):
        """Return a handle to a table.
        
        Return a handle to the named table or, if `table_name` is None, return the default table.
        
        Args:
            table_name (str): Name of the table or None.
            
        Returns:
            object: A database table object.
        """
        
    @abstractmethod
    def construct_query(self, keys, match_any):
        """Construct a query object from a dictionary of keys.
        
        Args:
            keys (dict): data keys to query.
            match_any (bool): If True then any key may match or if False then all keys must match.
        
        Returns:
            Query: The query object. 
        """
    
    def count(self, table_name=None):
        """Count the records in the database.
        
        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            
        Returns:
            int: Number of records in the table.
        """
        return len(self.table(table_name))
    
    def get(self, keys, table_name=None, match_any=False):
        """Find a single record.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: return the record with that element identifier.
            * dict: return the record with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * ``bool(keys) == False``: return None.
        
        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            Record: The matching data record if `keys` was a Record.ElementIdentifier or dict.
            list: All matching data records if `keys` was a list or tuple.
            None: No record found or ``bool(keys) == False``.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """
        table = self.table(table_name)
        if not keys:
            return None
        elif isinstance(keys, self.Record.ElementIdentifier):
            LOGGER.debug("%s: get(eid=%r)", table_name, keys)
            element = table.get(eid=keys)
        elif isinstance(keys, dict):
            LOGGER.debug("%s: get(keys=%r)", table_name, keys)
            element = table.get(self.construct_query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            return [self.get(table_name, key, match_any) for key in keys]
        else:
            raise ValueError(keys)
        if element:
            return self.Record(element=element)
        return None

    def search(self, keys=None, table_name=None, match_any=False):
        """Find multiple records.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: return the record with that element identifier.
            * dict: return all records with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * ``bool(keys) == False``: return all records.
        
        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            list: Matching data records.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """
        table = self.table(table_name)
        if not keys:
            LOGGER.debug("%s: all()", table_name)
            return [self.Record(element=elem) for elem in table.all()]
        elif isinstance(keys, self.Record.ElementIdentifier):
            LOGGER.debug("%s: search(eid=%r)", table_name, keys)
            element = table.get(eid=keys)
            return [element] if element else []
        elif isinstance(keys, dict):
            LOGGER.debug("%s: search(keys=%r)", table_name, keys)
            return [self.Record(element=elem) for elem in table.search(self.construct_query(keys, match_any))]
        elif isinstance(keys, (list, tuple)):
            result = []
            for key in keys:
                result.extend(self.search(table_name, key, match_any))
            return result
        else:
            raise ValueError(keys)

    def match(self, field, table_name=None, regex=None, test=None):
        """Find records where `field` matches `regex` or `test`.
        
        Either `regex` or `test` may be specified, not both.  
        If `regex` is given, then all records with `field` matching the regular expression are returned.
        If test is given then all records with `field` set to a value that caues `test` to return True are returned. 
        If neither is given, return all records where `field` is set to any value. 
        
        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            field (string): Name of the data field to match.
            regex (string): Regular expression string.
            test: Callable returning a boolean value.  

        Returns:
            list: Matching data records.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """
        table = self.table(table_name)
        if test is not None:
            LOGGER.debug('%s: search(where(%s).test(%r))', table_name, field, test)
            return [self.Record(element=elem) for elem in table.search(tinydb.where(field).test(test))]
        elif regex is not None:
            LOGGER.debug('%s: search(where(%s).matches(%r))', table_name, field, regex)
            return [self.Record(element=elem) for elem in table.search(tinydb.where(field).matches(regex))]
        else:
            LOGGER.debug("%s: search(where(%s).matches('.*'))", table_name, field)
            return [self.Record(element=elem) for elem in table.search(tinydb.where(field).matches(".*"))]

    def contains(self, keys=None, table_name=None, match_any=False):
        """Check if the specified table contains at least one matching record.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: check for the record with that element identifier.
            * dict: check for the record with attributes matching `keys`.
            * list or tuple: return the equivilent of ``map(contains, keys)``.
            * ``bool(keys) == False``: return False.
        
        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            bool: True if the table contains at least one matching record, False otherwise.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """
        table = self.table(table_name)
        if not keys:
            return False
        elif isinstance(keys, self.Record.ElementIdentifier):
            LOGGER.debug("%s: contains(eid=%r)", table_name, keys)
            return table.contains(eid=keys)
        elif isinstance(keys, dict):
            LOGGER.debug("%s: contains(keys=%r)", table_name, keys)
            return table.contains(self.construct_query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            return [self.contains(table_name, key, match_any) for key in keys]
        else:
            raise ValueError(keys)

    def insert(self, data, table_name=None):
        """Create a new record.
        
        If the table doesn't exist it will be created.
        
        Args:
            data (dict): Data to insert in table.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            
        Returns:
            Record: The new record.       
        """
        LOGGER.debug("%s: insert(%r)", table_name, data)
        eid = self.table(table_name).insert(data)
        return self.Record(eid=eid, value=data)

    def update(self, fields, keys, table_name=None, match_any=False):
        """Update records.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.
        
        Args:
            fields (dict): Data to record.
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.
            
        Raises:
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.ElementIdentifier):
            LOGGER.debug("%s: update(%r, eid=%r)", table_name, fields, keys)
            table.update(fields, eids=[keys])
        elif isinstance(keys, dict):
            LOGGER.debug("%s: update(%r, keys=%r)", table_name, fields, keys)
            table.update(fields, self.construct_query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            LOGGER.debug("%s: update(%r, eids=%r)", table_name, fields, keys)
            table.update(fields, eids=keys)
        else:
            raise ValueError(keys)
      
    def unset(self, fields, keys, table_name=None, match_any=False):
        """Update records by unsetting fields.
        
        Update only allows you to update a record by adding new fields or overwriting existing fields. 
        Use this method to remove a field from the record.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.
        
        Args:
            fields (list): Names of fields to remove from matching records.
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.
            
        Raises:
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.ElementIdentifier):
            for field in fields:
                LOGGER.debug("%s: unset(%s, eid=%r)", table_name, field, keys)
                table.update(tinydb.operations.delete(field), eids=[keys])
        elif isinstance(keys, dict):
            for field in fields:
                LOGGER.debug("%s: unset(%s, keys=%r)", table_name, field, keys)
                table.update(tinydb.operations.delete(field), self.construct_query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            for field in fields:
                LOGGER.debug("%s: unset(%s, eids=%r)", table_name, field, keys)
                table.update(tinydb.operations.delete(field), eids=keys)
        else:
            raise ValueError(keys)
        
    def remove(self, keys, table_name=None, match_any=False):
        """Delete records.
        
        The behavior depends on the type of `keys`:
            * Record.ElementIdentifier: delete the record with that element identifier.
            * dict: delete all records with attributes matching `keys`.
            * list or tuple: delete all records matching the elements of `keys`.
            * ``bool(keys) == False``: raise ValueError.
        
        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key 
                              in `keys` may match or if False then all keys in `keys` must match.
            
        Raises:
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.ElementIdentifier):
            LOGGER.debug("%s: remove(eid=%r)", table_name, keys)
            table.remove(eids=[keys])
        elif isinstance(keys, dict):
            LOGGER.debug("%s: remove(keys=%r)", table_name, keys)
            table.remove(self.construct_query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            LOGGER.debug("%s: remove(eids=%r)", table_name, keys)
            table.remove(eids=keys)
        else:
            raise ValueError(keys)

    def purge(self, table_name=None):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
        """
        LOGGER.debug("%s: purge()", table_name)
        self.table(table_name).purge()


class JsonDatabase(AbstractDatabase):
    """A persistant, transactional record storage system.  
    
    Uses :py:class:`TinyDB` to store and retrieve data as JSON strings.
    
    Attributes:
        dbfile (str): Absolute path to database file.
        database (TinyDB): Database handle.
    """
    
    class Record(dict):
        """A database record (a.k.a. "document").
        
        Attributes:
            ElementIdentifier: The type of the element identifier.
            eid: Unique identifier for the data record, None if the data has not been recorded.
        """
        
        ElementIdentifier = int

        def __init__(self, *args, **kwargs):
            """Initialize the record.
            
            The record's element ID and value may be set directly via::
                Record(eid=eid, value=value, *args, **kwargs)
                
            Otherwise the record's element ID and value should be set from a :any:`TinyDB.Element`::
                Record(element=element, *args, **kwargs)
            
            Args:
                *args: Positional arguments to be passed to :any:`dict()`
                **kwargs: Keyword arguments specifying element ID, record value, and additional
                          arguments to be passed to :any:`dict()`.
            """
            try:
                element = kwargs.pop('element')
            except KeyError:
                eid = kwargs.pop('eid')
                value = kwargs.pop('value')
            else:
                eid = element.eid
                value = element
            super(JsonDatabase.Record, self).__init__(value, *args, **kwargs)
            self.eid = eid
    
        def __repr__(self):
            return json.dumps(self)

    
    class JsonFileStorage(tinydb.JSONStorage):
        """Allow read-only as well as read-write access to the JSON file.
        
        TinyDB's default storage (:any:`tinydb.JSONStorage`) assumes write access to the JSON file.
        This isn't the case for system-level storage and possibly others.
        """
        def __init__(self, path):
            try:
                super(JsonDatabase.JsonFileStorage, self).__init__(path)
            except IOError:
                self.path = path
                self._handle = open(path, 'r')
                self.readonly = True
                LOGGER.debug("'%s' opened read-only", path)
            else:
                self.readonly = False
                LOGGER.debug("'%s' opened read-write", path)

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

    def table(self, table_name):
        if table_name is None:
            return self.database
        else:
            return self.database.table(table_name)
    
    def construct_query(self, keys, match_any):
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
