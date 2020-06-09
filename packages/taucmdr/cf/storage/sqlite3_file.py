# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, ParaTools, Inc.
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
Local file backend for SQLite databases.

A persistent, transactional record storage system using :py:class:`sqlite3` for
both the database and the key/value store.
"""

from __future__ import print_function

import os
import json
import re
import sqlite3
import six
from taucmdr import logger, util
from taucmdr.cf.storage.local_file import LocalFileStorage
from taucmdr.cf.storage import StorageRecord, StorageError

LOGGER = logger.get_logger(__name__)


class _SQLiteJsonRecord(StorageRecord):
    eid_type = int

    def __init__(self, database, element, eid=None):
        super(_SQLiteJsonRecord, self).__init__(database, eid or element.eid, element)

    def __str__(self):
        return json.dumps(self)

    def __repr__(self):
        return json.dumps(self)


class SQLiteStorageError(StorageError):
    """Indicates that the database connection has not been initialized."""

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "Please contact %(contact)s for assistance.")

    def __init__(self, table_name=None):
        """Initialize the error object.

        Args:
            table_name (str): Table on which access was attempted
        """
        if table_name:
            value = "Attempt to access table {} before database connection established".format(table_name)
        else:
            value = "Attempt to access database before connection established"
        super(SQLiteStorageError, self).__init__(value)
        self.table_name = table_name


class SQLiteDatabase(object):
    """Represents a connection to the database.

    Attributes:
        dbfile (str): Path to database file
    """

    def __init__(self, dbfile, storage=None):
        self.dbfile = dbfile
        self.storage = storage
        self._connection = None
        self._transaction_level = 0

    class _LoggingCursor(object):
        def __init__(self, cursor):
            self._cursor = cursor

        def execute(self, sql, parameters=()):
            LOGGER.debug("Executing `{}` with parameters {}".format(sql, parameters))
            return self._cursor.execute(sql, parameters)

        def fetchone(self):
            return self._cursor.fetchone()

        def fetchall(self):
            return self._cursor.fetchall()

        def close(self):
            return self._cursor.close()

        @property
        def lastrowid(self):
            return self._cursor.lastrowid

    def open(self):
        """Open the database connection specified in this object's dbfile attribute"""
        if self._connection is None:
            # isolation_level = None is required to prevent Python SQLite wrapper from interfering with transactions.
            # check_same_thread = False allows connection to be used from a different thread than the one that
            # created it, but note that the connection may not be used from multiple threads at the same time.
            # See https://stackoverflow.com/questions/24374242/python-sqlite-how-to-manually-begin-and-end-transactions
            self._connection = sqlite3.connect(self.dbfile, isolation_level=None, check_same_thread=False)
            LOGGER.debug("Connected to SQLite database at {}".format(self.dbfile))

    def close(self):
        """Close the database connection"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def cursor(self):
        """Returns a cursor which can be used to query the SQLite database"""
        if self._connection is None:
            raise SQLiteStorageError('Database connection is not open')
        return self._LoggingCursor(self._connection.cursor())

    def start_transaction(self):
        """Begin a transaction, which can be reverted with :any:`_SQLiteDatabase.revert_transaction`
        or committed with :any:`_SQLiteDatabase.commit_transaction`.
        """
        self.cursor().execute('BEGIN EXCLUSIVE TRANSACTION;')

    def revert_transaction(self):
        """Revert a transaction previously started with :any:`_SQLiteDatabase.start_transaction` """
        self.cursor().execute('ROLLBACK;')

    def commit_transaction(self):
        """Commit a transaction previously started with :any:`_SQLiteDatabase.start_transaction` """
        self.cursor().execute('END TRANSACTION;')

    def tables(self):
        """Get a list of all the tables in the database
        Returns:
            A list of the target names for the tables in the database.
        Raises:
            SQLiteStorageError: Attempt to perform and operation on a database which is not open
        """
        c = self.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
        result = [name for (name,) in c.fetchall() if not name.startswith('_')]
        c.close()
        return result

    def table(self, table_name):
        """Get a table object for a table in this database.
        Args:
            table_name (str): The name of the table requested
        Returns:
            A table object for the table `table_name`
        Raises:
            SQLiteStorageError: Attempt to perform and operation on a database which is not open
        """
        return _SQLiteJsonTable(self, table_name)

    def purge(self):
        """Delete every record in every table in the database.
        Raises:
            SQLiteStorageError: Attempt to perform and operation on a database which is not open
        """
        for table_name in self.tables():
            self.table(table_name).purge()
        self.table('_toplevel').purge()


class _SQLiteJsonTable(object):
    """Represents a JSON Table within the SQLite database.
    Operations on the table are made through this class.

    Attributes:

    """

    Record = _SQLiteJsonRecord

    def __init__(self, database, name):
        self.database = database
        self.name = name
        self._ensure_exists()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, v):
        if v.isalpha() or (v[0] == '_' and v[1:].isalpha()):
            self._name = v
        else:
            raise StorageError('Invalid table name {}'.format(v))

    def _ensure_exists(self):
        c = self.database.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY, data JSON NOT NULL);".format(self.name))
        c.close()

    def insert(self, element):
        c = self.database.cursor()
        c.execute("INSERT INTO {} (data) VALUES(?)".format(self.name), [json.dumps(element)])
        result = _SQLiteJsonRecord(self.database.storage, element, eid=c.lastrowid)
        c.close()
        return result

    @staticmethod
    def _json_query(keys=None, match_any=False):
        join_string = " OR " if match_any else " AND "
        where_clause = join_string.join(
            ["json_extract(data, '$.{}') == {}".format(key, (
                int(val) if isinstance(val, int) else json.dumps(val) if isinstance(val, six.string_types) else
                "json('{}')".format(json.dumps(val)))) for (key, val) in six.iteritems(keys)])
        if where_clause:
            where_clause = "WHERE {}".format(where_clause)
        return where_clause

    def _get(self, keys=None, eid=None, match_any=False, remove=False):
        db_row = None
        result = None
        c = self.database.cursor()
        command = 'DELETE' if remove else 'SELECT id, data'

        if eid is not None:
            c.execute('{} FROM {} WHERE id == ?'.format(command, self.name), [eid])
            db_row = c.fetchone()
        elif isinstance(keys, dict):
            query_string = '{} FROM {} {};'.format(
                command, self.name, self._json_query(keys, match_any=match_any))
            c.execute(query_string)
            db_row = c.fetchone()

        if db_row is not None:
            (row_eid, row_data) = db_row
            result = _SQLiteJsonRecord(self.database.storage, json.loads(row_data), eid=row_eid)

        c.close()
        return result

    def get(self, keys=None, eid=None, match_any=False):
        return self._get(keys=keys, eid=eid, match_any=match_any)

    def remove(self, keys=None, eid=None, match_any=False):
        return self._get(keys=keys, eid=eid, match_any=match_any, remove=True)

    def search(self, cond, match_any=False):
        if cond is None:
            cond = {}
        c = self.database.cursor()
        query_string = 'SELECT id, data FROM {} {};'.format(
            self.name, self._json_query(cond, match_any=match_any))
        c.execute(query_string)
        db_rows = c.fetchall()
        result = [_SQLiteJsonRecord(self.database.storage, json.loads(row_data), eid=row_eid)
                  for (row_eid, row_data) in db_rows]
        c.close()
        return result

    def count(self, cond, match_any=False):
        if cond is None:
            return None
        matches = self.search(cond, match_any)
        return len(matches)

    def update(self, fields, keys=None, eids=None, match_any=False, unset=False):
        # Construct the json_set expression
        if len(fields) == 0:
            # We were asked to update no fields, which is a no-op
            return
        if unset:
            if not isinstance(fields, (list, tuple)):
                raise ValueError('fields must be a collection type but was {}'.format(type(fields)))
            json_set_expr = "json_remove(data{})".format("".join([", '$.{}'".format(key) for key in fields]))
        else:
            if not isinstance(fields, dict):
                raise ValueError('fields must be a dictionary but was {}'.format(type(fields)))
            json_set_expr = "json_set(data{})".format(
                "".join(
                    [", '$.{}', json('{}')".format(key, json.dumps(value)) for (key, value) in six.iteritems(fields)]))

        # Then construct the WHERE clause to match either the EIDs provided
        # or the keys provided.
        if eids is not None and keys is not None:
            raise ValueError('Both keys and eids provided but only one should be provided')
        if eids is not None:
            if isinstance(eids, (list, tuple)):
                update_ids = eids
            elif isinstance(eids, self.Record.eid_type):
                update_ids = [eids]
            else:
                raise ValueError('eids, if set, must be of type {0} or collection of {0}, but was {1}'.format(
                    self.Record.eid_type, type(eids)))
            where_clause = 'WHERE {}'.format(" OR ".join(["id == {}".format(eid) for eid in update_ids]))
        elif isinstance(keys, dict):
            where_clause = self._json_query(keys, match_any)
        else:
            raise ValueError('Either keys or eids must be provided')

        # Assemble the whole UPDATE statement
        update_statement = "UPDATE {} SET data = {} {};".format(self.name, json_set_expr, where_clause)

        # Run it
        c = self.database.cursor()
        c.execute(update_statement)
        c.close()

    def exists(self, field):
        c = self.database.cursor()
        c.execute("SELECT * FROM {} WHERE json_extract(data, '$.{}') IS NOT NULL;".format(self.name, field))
        db_rows = c.fetchall()
        result = [_SQLiteJsonRecord(self.database.storage, json.loads(row_data), eid=row_eid)
                  for (row_eid, row_data) in db_rows]
        c.close()
        return result

    def purge(self):
        c = self.database.cursor()
        c.execute('DROP TABLE IF EXISTS {};'.format(self.name))
        c.close()
        self._ensure_exists()


class SQLiteLocalFileStorage(LocalFileStorage):
    """A persistent, transactional record storage system.

    Uses :py:class:`sqlite3` for both the database and the key/value store.

    Attributes:
        dbfile (str): Absolute path to database file.
    """

    Record = _SQLiteJsonRecord

    def __init__(self, name, prefix):
        super(SQLiteLocalFileStorage, self).__init__(name, prefix)
        self._database = None

    @property
    def dbfile(self):
        return os.path.join(self.prefix, self.name + '.sqlite3')

    def connect_database(self, *args, **kwargs):
        """Open the database for reading and writing."""

        if self._database is None:
            util.mkdirp(self.prefix)
            try:
                self._database = SQLiteDatabase(self.dbfile, storage=self)
                self._database.open()
            except IOError as err:
                raise StorageError("Failed to access %s database '%s': %s" % (self.name, self.dbfile, err),
                                   "Check that you have `write` access")
            if not util.path_accessible(self.dbfile):
                raise StorageError("Database file '%s' exists but cannot be read." % self.dbfile,
                                   "Check that you have `read` access")
            LOGGER.debug("Initialized %s database '%s'", self.name, self.dbfile)

    def disconnect_database(self, *args, **kwargs):
        """Close the database for reading and writing."""
        if self._database:
            self._database.close()
            self._database = None

    def __str__(self):
        """Human-readable identifier for this database."""
        # pylint: disable=protected-access
        return "<SQLiteLocalFileStorage dbfile={}>".format(self.dbfile)

    def __enter__(self):
        """Initiates the database transaction."""
        # pylint: disable=protected-access
        if self._transaction_count == 0:
            self._database.start_transaction()
        self._transaction_count += 1
        return self

    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""
        # pylint: disable=protected-access
        self._transaction_count -= 1
        if self._transaction_count == 0:
            if ex_type:
                self._database.revert_transaction()
                return False
            else:
                self._database.commit_transaction()
                return True
        return bool(ex_type)

    def table(self, table_name):
        self.connect_database()
        if table_name is None:
            table_name = '_toplevel'
        return self._database.table(table_name)

    def count(self, table_name=None):
        """Count the records in the database.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.

        Returns:
            int: Number of records in the table.
        """
        return self.table(table_name).count({})

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
            return table.get(eid=keys)
        elif isinstance(keys, dict):
            return table.get(keys=keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
            return [self.get(key, table_name=table_name, match_any=match_any) for key in keys]
        else:
            raise ValueError(keys)

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
        table = self.table(table_name)
        if keys is None:
            return table.search(cond=None)
        elif isinstance(keys, self.Record.eid_type):
            element = table.get(eid=keys)
            return [element] if element else []
        elif isinstance(keys, dict):
            return table.search(keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
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
        # Since `test` can be an arbitrary Python function, the test can't actually happen inside SQLite.
        # Instead we retrieve all potentially matching records (those for which the field in question exists)
        # and filter them afterwards.
        # TODO This could be made more efficient if we make this function less general.
        # This is only used in controller.py in the delete function
        possible_records = self.table(table_name).exists(field)
        if test is not None and regex is not None:
            raise ValueError('At most one of "test" and "regex" can be provided')
        elif test is not None:
            return [record for record in possible_records if test(record[field])]
        elif regex is not None:
            pattern = re.compile(regex)
            return [record for record in possible_records if pattern.match(record[field])]
        else:
            return possible_records

    def contains(self, keys, table_name=None, match_any=False):
        """Check if the specified table contains at least one matching record.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: check for the record with that element identifier.
            * dict: check for the record with attributes matching `keys`.
            * list or tuple: return the equivalent of ``map(contains, keys)``.
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
        if keys is None:
            return False
        elif isinstance(keys, dict):
            return self.table(table_name).count(keys, match_any=match_any) > 0
        elif isinstance(keys, (list, tuple)):
            return [self.contains(keys=key, table_name=table_name, match_any=match_any) for key in keys]
        elif isinstance(keys, self.Record.eid_type):
            return self.get(keys, table_name=table_name, match_any=match_any) is not None
        else:
            raise ValueError(
                '"keys" must be dict, list, tuple, or {}, but was {}'.format(self.Record.eid_type, type(keys)))

    def insert(self, data, table_name=None):
        """Create a new record.

        If the table doesn't exist it will be created.

        Args:
            data (dict): Data to insert in table.
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.

        Returns:
            Record: The new record.
        """
        return self.table(table_name).insert(data)

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
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.eid_type):
            table.update(fields, eids=[keys])
        elif isinstance(keys, dict):
            table.update(fields, keys=keys)
        elif isinstance(keys, (list, tuple)):
            table.update(fields, eids=keys)
        else:
            raise ValueError(
                '"keys" must be dict, list, tuple, or {}, but was {}'.format(self.Record.eid_type, type(keys)))

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
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, (self.Record.eid_type, list, tuple)):
            table.update(fields, eids=keys, unset=True)
        elif isinstance(keys, dict):
            table.update(fields, keys=keys, unset=True)
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
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
        """
        table = self.table(table_name)
        if keys is None:
            return None
        elif isinstance(keys, self.Record.eid_type):
            table.remove(eid=keys)
        elif isinstance(keys, dict):
            table.remove(keys=keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
            # TODO Change this to use a single operation
            for key in keys:
                self.remove(key, table_name=table_name, match_any=match_any)
        else:
            raise ValueError(keys)

    def purge(self, table_name=None):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
        """
        self.table(table_name).purge()
