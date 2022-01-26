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
"""TAU Commander storage dispatch

This Storage class dispatches calls to either TinyDB or SQLite, depending on which is selected.
"""
import os

from taucmdr import logger
from taucmdr import util
from taucmdr.cf.storage import AbstractStorage, StorageError
from taucmdr.cf.storage.local_file import LocalFileStorage
from taucmdr.cf.storage.sqlite3_file import SQLiteLocalFileStorage
from taucmdr.cf.storage.project import ProjectStorage
from taucmdr.cf.storage.sqlite3_project import SQLiteProjectStorage
from taucmdr.error import InternalError

LOGGER = logger.get_logger(__name__)

DB_TINYDB = 1
DB_SQLITE = 2
DB_AUTO = 3

AVAILABLE_BACKENDS = {'tinydb': DB_TINYDB, 'sqlite': DB_SQLITE, 'auto': DB_AUTO}


class StorageDispatch(AbstractStorage):
    """Dispatches storage method calls to backend storage based on runtime selection of the type."""

    default_backend = os.environ.get('__TAUCMDR_DB_BACKEND__', 'auto')

    def __init__(self, name=None, prefix=None, kind=None):
        super().__init__(name)
        LOGGER.debug("Initialized StorageDispatch name = %s kind = %s", name, kind)
        if kind == 'project':
            self._local_storage = ProjectStorage()
            self._sqlite_storage = SQLiteProjectStorage()
        else:
            self._local_storage = LocalFileStorage(name, prefix)
            self._sqlite_storage = SQLiteLocalFileStorage(name, prefix)
        self._backend = None
        self.set_backend(self.default_backend)

    def set_backend(self, backend):
        """Set the backend that is to be used for subsequent storage method calls.

        Args:
            backend (str): The backend to use. One of 'tinydb', 'sqlite', or 'auto'.
                           If 'auto', the backend is SQLite if a SQLite database is already present,
                           and is TinyDB otherwise.
        """
        if backend not in AVAILABLE_BACKENDS:
            raise StorageError(f'Unrecognized backend {backend}; use one of {AVAILABLE_BACKENDS}')
        if backend == 'tinydb':
            LOGGER.debug("Using TinyDB database as requested for %s", self.name)
            self._backend = DB_TINYDB
        elif backend == 'sqlite':
            LOGGER.debug("Using SQLite database as requested for %s", self.name)
            self._backend = DB_SQLITE
        elif backend == 'auto':
            if self._sqlite_storage.database_exists():
                LOGGER.debug("Using SQLite database in AUTO mode because one already exists for %s", self.name)
                self._backend = DB_SQLITE
            else:
                LOGGER.debug("Using TinyDB (default) in AUTO because no database already exists for %s", self.name)
                self._backend = DB_TINYDB

    def _get_storage(self):
        if self._backend == DB_TINYDB:
            return self._local_storage
        elif self._backend == DB_SQLITE:
            return self._sqlite_storage
        raise InternalError(f'Bad storage type in dispatch: {self._backend}')

    def __getattr__(self, item):
        """Dispatches any messages not otherwise caught to the selected storage backend."""
        return getattr(self._get_storage(), item)

    def __len__(self):
        """Return the number of items in the key/value store."""
        return len(self._get_storage())

    def __getitem__(self, key):
        """Retrieve a value from the key/value store."""
        return self._get_storage()[key]

    def __setitem__(self, key, value):
        """Store a value in the key/value store."""
        self._get_storage()[key] = value

    def __delitem__(self, key):
        """Remove a value from the key/value store."""
        del self._get_storage()[key]

    def __contains__(self, key):
        """Returns True if ``key`` maps to a value is in the key/value store."""
        return key in self._get_storage()

    def __iter__(self):
        """Iterate over keys in the key/value store."""
        return iter(self._get_storage())

    def keys(self):
        """Iterate over keys in the key/value store."""
        return self._get_storage().keys()

    def values(self):
        """Iterate over values in the key/value store."""
        return self._get_storage().items()

    def items(self):
        """Iterate over items in the key/value store."""
        return self._get_storage().items()

    def connect_filesystem(self, *args, **kwargs):
        """Prepares the store filesystem for reading and writing."""
        return self._get_storage().connect_filesystem(*args, **kwargs)

    def disconnect_filesystem(self, *args, **kwargs):
        """Makes the store filesystem unreadable and unwritable."""
        return self._get_storage().disconnect_filesystem(*args, **kwargs)

    def connect_database(self, *args, **kwargs):
        """Open the database for reading and writing."""
        return self._get_storage().connect_database(*args, **kwargs)

    def disconnect_database(self, *args, **kwargs):
        """Close the database for reading and writing."""
        return self._get_storage().disconnect_database(*args, **kwargs)

    @property
    def prefix(self):
        """Get the filesystem prefix for file storage.

        The filesystem must be persistent and provide the usual POSIX filesystem calls.
        In particular, GNU software packages should be installable in the filesystem.

        Returns:
            str: Absolute path in the filesystem.
        """
        return self._get_storage().prefix

    def __enter__(self):
        """Initiates the database transaction."""
        return self._get_storage().__enter__()

    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""
        return self._get_storage().__exit__(ex_type, value, traceback)

    def table(self, table_name):
        """Return a handle to a table.

        Return a handle to the named table or, if `table_name` is None, return the default table.

        Args:
            table_name (str): Name of the table or None.

        Returns:
            object: A database table object.
        """
        return self._get_storage().table(table_name)

    def count(self, table_name=None):
        """Count the records in the database.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.

        Returns:
            int: Number of records in the table.
        """
        return self._get_storage().count(table_name=table_name)

    def get(self, keys, table_name=None, match_any=False):
        """Find a single record.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: return the record with that element identifier.
            * dict: return the record with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * None: return None.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            Record: The matching data record if `keys` was a self.Record.eid_type or dict.
            list: All matching data records if `keys` was a list or tuple.
            None: No record found or ``bool(keys) == False``.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        return self._get_storage().get(keys, table_name=table_name, match_any=match_any)

    def search(self, keys=None, table_name=None, match_any=False):
        """Find multiple records.

        The behavior depends on the type of `keys`:
            * Record.eid_type: return the record with that element identifier.
            * dict: return all records with attributes matching `keys`.
            * list or tuple: return a list of records matching the elements of `keys`
            * None: return all records.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            list: Matching data records.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        return self._get_storage().search(keys=keys, table_name=table_name, match_any=match_any)

    def match(self, field, table_name=None, regex=None, test=None):
        """Find records where `field` matches `regex` or `test`.

        Either `regex` or `test` may be specified, not both.
        If `regex` is given, then all records with `field` matching the regular expression are returned.
        If test is given then all records with `field` set to a value that caues `test` to return True are returned.
        If neither is given, return all records where `field` is set to any value.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            field (string): Name of the data field to match.
            regex (string): Regular expression string.
            test: Callable returning a boolean value.

        Returns:
            list: Matching data records.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        return self._get_storage().match(field, table_name=table_name, regex=regex, test=test)

    def contains(self, keys, table_name=None, match_any=False):
        """Check if the specified table contains at least one matching record.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: check for the record with that element identifier.
            * dict: check for the record with attributes matching `keys`.
            * list or tuple: return the equivalent of ``map(contains, keys)``.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Returns:
            bool: True if the table contains at least one matching record, False otherwise.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        return self._get_storage().contains(keys, table_name=table_name, match_any=match_any)

    def insert(self, data, table_name=None):
        """Create a new record.

        If the table doesn't exist it will be created.

        Args:
            data (dict): Data to insert in table.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.

        Returns:
            Record: The new record.

        Raises:
            TypeError: If bytes, bytearray or memoryview found in data
        """
        if not util.is_clean_container(data):
            raise TypeError(f"Bad binary type (bytes, bytearray, etc.) found in data(dict):\n{data}")
        return self._get_storage().insert(data, table_name=table_name)

    def update(self, fields, keys, table_name=None, match_any=False):
        """Update records.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: update the record with that element identifier.
            * dict: update all records with attributes matching `keys`.
            * list or tuple: apply update to all records matching the elements of `keys`.

        Args:
            fields (dict): Data to record.
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Raises:
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
            TypeError: If binary data (bytes, bytearray, memoryview) found in fields or key dict
        """
        if not util.is_clean_container(fields):
          raise TypeError(f"Bad types (bytes, bytearray, etc.) passed as fields:\n{fields}")
        if isinstance(keys, dict) and not util.is_clean_container(keys):
            raise TypeError(f"Bad types (bytes, bytearray, etc. passed as keys:\n{keys}")
        return self._get_storage().update(fields, keys, table_name=table_name, match_any=match_any)

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
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Raises:
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
        """
        return self._get_storage().unset(fields, keys, table_name=table_name, match_any=match_any)

    def remove(self, keys, table_name=None, match_any=False):
        """Delete records.

        The behavior depends on the type of `keys`:
            * self.Record.eid_type: delete the record with that element identifier.
            * dict: delete all records with attributes matching `keys`.
            * list or tuple: delete all records matching the elements of `keys`.

        Args:
            keys: Fields or element identifiers to match.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            match_any (bool): Only applies if `keys` is a dictionary.  If True then any key
                              in `keys` may match or if False then all keys in `keys` must match.

        Raises:
            ValueError: ``bool(keys) == False`` or invalid value for `keys`.
        """
        return self._get_storage().remove(keys, table_name=table_name, match_any=match_any)

    def purge(self, table_name=None):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
        """
        return self._get_storage().purge(table_name=table_name)

    def database_exists(self):
        """Determine if the database file backing this Storage object exists.

        Returns:
            bool: True if database exists; false otherwise.
        """
        return self._get_storage().database_exists()


class ProjectStorageDispatch(StorageDispatch):
    """Dispatches Project storage method calls to the backing Project storage class"""
    def __init__(self):
        super().__init__(name='project', prefix=None, kind='project')

    def destroy(self, ignore_errors=False):
        self._local_storage.destroy(ignore_errors=ignore_errors)
        self._sqlite_storage.destroy(ignore_errors=ignore_errors)
