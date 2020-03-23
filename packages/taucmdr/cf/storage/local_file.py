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
"""
Local file backend for storage containers.

A persistant, transactional record storage system useing :py:class:`TinyDB` for
both the database and the key/value store.
"""

from __future__ import absolute_import
import os
import json
import six
import tempfile
import tinydb
from tinydb import operations
from tinydb.middlewares import CachingMiddleware
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.storage import AbstractStorage, StorageRecord, StorageError

LOGGER = logger.get_logger(__name__)



class _JsonRecord(StorageRecord):
    eid_type = int

    def __init__(self, database, element, eid=None):
        super(_JsonRecord, self).__init__(database, eid or element.eid, element)

    def __str__(self):
        return json.dumps(self)

    def __repr__(self):
        return json.dumps(self)


class _JsonFileStorage(tinydb.JSONStorage):
    """Allow read-only as well as read-write access to the JSON file.

    TinyDB's default storage (:any:`tinydb.JSONStorage`) assumes write access to the JSON file.
    This isn't the case for system-level storage and possibly others.
    """
    def __init__(self, path):
        try:
            super(_JsonFileStorage, self).__init__(path)
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
            super(_JsonFileStorage, self).write(*args, **kwargs)


class LocalFileStorage(AbstractStorage):
    """A persistant, transactional record storage system.

    Uses :py:class:`TinyDB` for both the database and the key/value store.

    Attributes:
        dbfile (str): Absolute path to database file.
    """

    Record = _JsonRecord

    def __init__(self, name, prefix):
        super(LocalFileStorage, self).__init__(name)
        self._transaction_count = 0
        self._db_copy = None
        self._database = None
        self._prefix = prefix

    def __len__(self):
        return self.count()

    def __getitem__(self, key):
        record = self.get({'key': key})
        if record is not None:
            return record['value']
        raise KeyError

    def __setitem__(self, key, value):
        if self.contains({'key': key}):
            self.update({'value': value}, {'key': key})
        else:
            self.insert({'key': key, 'value': value})

    def __delitem__(self, key):
        if not self.contains({'key': key}):
            raise KeyError
        self.remove({'key': key})

    def __contains__(self, key):
        return self.contains({'key': key})

    def __iter__(self):
        for item in self.search():
            yield item['key']

    def iterkeys(self):
        for item in self.search():
            yield item['key']

    def itervalues(self):
        for item in self.search():
            yield item['value']

    def iteritems(self):
        for item in self.search():
            yield item['key'], item['value']

    def is_writable(self):
        """Check if the storage filesystem is writable.

        Attempts to create and delete a file in ``prefix``.
        See https://github.com/ParaToolsInc/taucmdr/issues/231.

        Returns:
            bool: True if a file could be created and deleted in ``prefix``, False otherwise.
        """
        self.connect_filesystem()
        if not os.access(self.prefix, os.W_OK):
            return False
        try:
            with tempfile.NamedTemporaryFile(dir=self.prefix, delete=True) as tmp_file:
                tmp_file.write("Write test. Delete this file.")
        except (OSError, IOError):
            return False
        return True

    def connect_filesystem(self, *args, **kwargs):
        """Prepares the store filesystem for reading and writing."""
        if not os.path.isdir(self._prefix):
            try:
                util.mkdirp(self._prefix)
            except Exception as err:
                raise StorageError("Failed to access %s filesystem prefix '%s': %s" % (self.name, self._prefix, err))
            LOGGER.debug("Initialized %s filesystem prefix '%s'", self.name, self._prefix)

    def disconnect_filesystem(self, *args, **kwargs):
        """Disconnects the store filesystem."""
        self.disconnect_database()

    def connect_database(self, *args, **kwargs):
        """Open the database for reading and writing."""
        if self._database is None:
            util.mkdirp(self.prefix)
            dbfile = os.path.join(self.prefix, self.name + '.json')
            try:
                storage = CachingMiddleware(_JsonFileStorage)
                storage.WRITE_CACHE_SIZE = 0
                self._database = tinydb.TinyDB(dbfile, storage=storage)
            except IOError as err:
                raise StorageError("Failed to access %s database '%s': %s" % (self.name, dbfile, err),
                                   "Check that you have `write` access")
            if not util.path_accessible(dbfile):
                raise StorageError("Database file '%s' exists but cannot be read." % dbfile,
                                   "Check that you have `read` access")
            LOGGER.debug("Initialized %s database '%s'", self.name, dbfile)

    def disconnect_database(self, *args, **kwargs):
        """Close the database for reading and writing."""
        if self._database:
            self._database.close()
            self._database = None

    @property
    def prefix(self):
        return self._prefix

    def __str__(self):
        """Human-readable identifier for this database."""
        # pylint: disable=protected-access
        return self._database._storage.path

    def __enter__(self):
        """Initiates the database transaction."""
        # Use protected methods to duplicate database in memory rather than on disk.
        # pylint: disable=protected-access
        if self._transaction_count == 0:
            self.connect_database()
            self._db_copy = self._database._read()
        self._transaction_count += 1
        return self

    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""
        # Use protected methods to duplicate database in memory rather than on disk.
        # pylint: disable=protected-access
        self._transaction_count -= 1
        if ex_type and self._transaction_count == 0:
            self._database._write(self._db_copy)
            self._db_copy = None
            return False

    def table(self, table_name):
        self.connect_database()
        if table_name is None:
            return self._database
        else:
            return self._database.table(table_name)

    @staticmethod
    def _query(keys, match_any):
        """Construct a TinyDB query object."""
        def _and(lhs, rhs):
            return lhs & rhs
        def _or(lhs, rhs):
            return lhs | rhs
        join = _or if match_any else _and
        itr = six.iteritems(keys)
        key, val = next(itr)
        query = (tinydb.where(key) == val)
        for key, value in itr:
            query = join(query, (tinydb.where(key) == value))
        return query

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
            * self.Record.eid_type: return the record with that element identifier.
            * dict: return the record with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * None: return None.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            Record: The matching data record if `keys` was a self.Record.eid_type or dict.
            list: All matching data records if `keys` was a list or tuple.
            None: No record found or ``bool(keys) == False``.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        table = self.table(table_name)
        if keys is None:
            return None
        elif isinstance(keys, self.Record.eid_type):
            #LOGGER.debug("%s: get(eid=%r)", table_name, keys)
            element = table.get(eid=keys)
        elif isinstance(keys, dict) and keys:
            #LOGGER.debug("%s: get(keys=%r)", table_name, keys)
            element = table.get(self._query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            #LOGGER.debug("%s: get(keys=%r)", table_name, keys)
            return [self.get(key, table_name=table_name, match_any=match_any) for key in keys]
        else:
            raise ValueError(keys)
        if element:
            return self.Record(self, element=element)
        return None

    def search(self, keys=None, table_name=None, match_any=False):
        """Find multiple records.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: return the record with that element identifier.
            * dict: return all records with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * None: return all records.

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
        #LOGGER.debug("Search '%s' for '%s'", table_name, keys)
        table = self.table(table_name)
        if keys is None:
            #LOGGER.debug("%s: all()", table_name)
            return [self.Record(self, element=element) for element in table.all()]
        elif isinstance(keys, self.Record.eid_type):
            #LOGGER.debug("%s: search(eid=%r)", table_name, keys)
            element = table.get(eid=keys)
            return [self.Record(self, element=element)] if element else []
        elif isinstance(keys, dict) and keys:
            #LOGGER.debug("%s: search(keys=%r)", table_name, keys)
            return [self.Record(self, element=element) for element in table.search(self._query(keys, match_any))]
        elif isinstance(keys, (list, tuple)):
            #LOGGER.debug("%s: search(keys=%r)", table_name, keys)
            result = []
            for key in keys:
                result.extend(self.search(keys=key, table_name=table_name, match_any=match_any))
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
            #LOGGER.debug('%s: search(where(%s).test(%r))', table_name, field, test)
            return [self.Record(self, element=elem) for elem in table.search(tinydb.where(field).test(test))]
        elif regex is not None:
            #LOGGER.debug('%s: search(where(%s).matches(%r))', table_name, field, regex)
            return [self.Record(self, element=elem) for elem in table.search(tinydb.where(field).matches(regex))]
        else:
            #LOGGER.debug("%s: search(where(%s).matches('.*'))", table_name, field)
            return [self.Record(self, element=elem) for elem in table.search(tinydb.where(field).matches(".*"))]

    def contains(self, keys, table_name=None, match_any=False):
        """Check if the specified table contains at least one matching record.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: check for the record with that element identifier.
            * dict: check for the record with attributes matching `keys`.
            * list or tuple: return the equivilent of ``map(contains, keys)``.
            * None: return False.

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
        if keys is None:
            return False
        elif isinstance(keys, self.Record.eid_type):
            #LOGGER.debug("%s: contains(eid=%r)", table_name, keys)
            return table.contains(eid=keys)
        elif isinstance(keys, dict) and keys:
            #LOGGER.debug("%s: contains(keys=%r)", table_name, keys)
            return table.contains(self._query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            return [self.contains(keys=key, table_name=table_name, match_any=match_any) for key in keys]
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
        eid = self.table(table_name).insert(data)
        record = self.Record(self, eid=eid, element=data)
        return record

    def update(self, fields, keys, table_name=None, match_any=False):
        """Update records.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.

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
        if isinstance(keys, self.Record.eid_type):
            #LOGGER.debug("%s: update(%r, eid=%r)", table_name, fields, keys)
            table.update(fields, eids=[keys])
        elif isinstance(keys, dict):
            #LOGGER.debug("%s: update(%r, keys=%r)", table_name, fields, keys)
            table.update(fields, self._query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            #LOGGER.debug("%s: update(%r, eids=%r)", table_name, fields, keys)
            table.update(fields, eids=keys)
        else:
            raise ValueError(keys)

    def unset(self, fields, keys, table_name=None, match_any=False):
        """Update records by unsetting fields.

        Update only allows you to update a record by adding new fields or overwriting existing fields.
        Use this method to remove a field from the record.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.

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
        if isinstance(keys, self.Record.eid_type):
            for field in fields:
                #LOGGER.debug("%s: unset(%s, eid=%r)", table_name, field, keys)
                table.update(operations.delete(field), eids=[keys])
        elif isinstance(keys, dict):
            for field in fields:
                #LOGGER.debug("%s: unset(%s, keys=%r)", table_name, field, keys)
                table.update(operations.delete(field), self._query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            for field in fields:
                #LOGGER.debug("%s: unset(%s, eids=%r)", table_name, field, keys)
                table.update(operations.delete(field), eids=keys)
        else:
            raise ValueError(keys)

    def remove(self, keys, table_name=None, match_any=False):
        """Delete records.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: delete the record with that element identifier.
            * dict: delete all records with attributes matching `keys`.
            * list or tuple: delete all records matching the elements of `keys`.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Raises:
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.eid_type):
            #LOGGER.debug("%s: remove(eid=%r)", table_name, keys)
            table.remove(eids=[keys])
        elif isinstance(keys, dict):
            #LOGGER.debug("%s: remove(keys=%r)", table_name, keys)
            table.remove(self._query(keys, match_any))
        elif isinstance(keys, (list, tuple)):
            #LOGGER.debug("%s: remove(eids=%r)", table_name, keys)
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
