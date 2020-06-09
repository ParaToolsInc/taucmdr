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
"""TAU Commander storage dispatch

This Storage class dispatches calls to either TinyDB or SQLite, depending on which is selected.
"""
import os

from taucmdr import logger
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
        super(StorageDispatch, self).__init__(name)
        LOGGER.debug("Initialized StorageDispatch name = %s kind = %s", name, kind)
        if kind == 'project':
            self._local_storage = ProjectStorage()
            self._sqlite_storage = SQLiteProjectStorage()
        else:
            self._local_storage = LocalFileStorage(name, prefix)
            self._sqlite_storage = SQLiteLocalFileStorage(name, prefix)
        self._backend = None
        self.set_backend(self.default_backend)

    @classmethod
    def set_default_backend(cls, default_backend):
        cls.default_backend = default_backend

    def set_backend(self, backend):
        """Set the backend that is to be used for subsequent storage method calls.

        Args:
            backend (str): The backend to use. One of 'tinydb', 'sqlite', or 'auto'.
                           If 'auto', the backend is SQLite if a SQLite database is already present,
                           and is TinyDB otherwise.
        """
        if backend not in AVAILABLE_BACKENDS:
            raise StorageError('Unrecognized backend {}; use one of {}'.format(backend, AVAILABLE_BACKENDS))
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
        raise InternalError('Bad storage type in dispatch: {}'.format(self._backend))

    def __getattr__(self, item):
        return getattr(self._get_storage(), item)

    def __len__(self):
        return len(self._get_storage())

    def __getitem__(self, key):
        return self._get_storage()[key]

    def __setitem__(self, key, value):
        self._get_storage()[key] = value

    def __delitem__(self, key):
        del self._get_storage()[key]

    def __contains__(self, key):
        return key in self._get_storage()

    def __iter__(self):
        return iter(self._get_storage())

    def iterkeys(self):
        return self._get_storage().iterkeys()

    def itervalues(self):
        return self._get_storage().iteritems()

    def iteritems(self):
        return self._get_storage().iteritems()

    def connect_filesystem(self, *args, **kwargs):
        return self._get_storage().connect_filesystem(*args, **kwargs)

    def disconnect_filesystem(self, *args, **kwargs):
        return self._get_storage().disconnect_filesystem(*args, **kwargs)

    def connect_database(self, *args, **kwargs):
        return self._get_storage().connect_database(*args, **kwargs)

    def disconnect_database(self, *args, **kwargs):
        return self._get_storage().disconnect_database(*args, **kwargs)

    @property
    def prefix(self):
        return self._get_storage().prefix

    def __enter__(self):
        return self._get_storage().__enter__()

    def __exit__(self, ex_type, value, traceback):
        return self._get_storage().__exit__(ex_type, value, traceback)

    def table(self, table_name):
        return self._get_storage().table(table_name)

    def count(self, table_name=None):
        return self._get_storage().count(table_name=table_name)

    def get(self, keys, table_name=None, match_any=False):
        return self._get_storage().get(keys, table_name=table_name, match_any=match_any)

    def search(self, keys=None, table_name=None, match_any=False):
        return self._get_storage().search(keys=keys, table_name=table_name, match_any=match_any)

    def match(self, field, table_name=None, regex=None, test=None):
        return self._get_storage().match(field, table_name=table_name, regex=regex, test=test)

    def contains(self, keys, table_name=None, match_any=False):
        return self._get_storage().contains(keys, table_name=table_name, match_any=match_any)

    def insert(self, data, table_name=None):
        return self._get_storage().insert(data, table_name=table_name)

    def update(self, fields, keys, table_name=None, match_any=False):
        return self._get_storage().update(fields, keys, table_name=table_name, match_any=match_any)

    def unset(self, fields, keys, table_name=None, match_any=False):
        return self._get_storage().unset(fields, keys, table_name=table_name, match_any=match_any)

    def remove(self, keys, table_name=None, match_any=False):
        return self._get_storage().remove(keys, table_name=table_name, match_any=match_any)

    def purge(self, table_name=None):
        return self._get_storage().purge(table_name=table_name)

    def database_exists(self):
        return self._get_storage().database_exists()


class ProjectStorageDispatch(StorageDispatch):
    def __init__(self):
        super(ProjectStorageDispatch, self).__init__(name='project', prefix=None, kind='project')

    def destroy(self, ignore_errors=False):
        self._local_storage.destroy(ignore_errors=ignore_errors)
        self._sqlite_storage.destroy(ignore_errors=ignore_errors)
