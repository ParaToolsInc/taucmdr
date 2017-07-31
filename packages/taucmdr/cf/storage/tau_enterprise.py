# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, ParaTools, Inc.
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
Backend for storing data in TAU Enterprise.

This currently means storing key-value pairs and database records accessed
through a REST API backed by MongoDB and files in Ceph through RADOSGW, an
Amazon S3 API compatible object store.
"""

import json
import requests
import six
from taucmdr import logger
from taucmdr.error import InternalError
from taucmdr.cf.storage import AbstractStorage, StorageRecord

LOGGER = logger.get_logger(__name__)


class _TauEnterpriseJsonRecord(StorageRecord):
    eid_type = unicode

    def __init__(self, database, element, eid=None):
        super(_TauEnterpriseJsonRecord, self).__init__(database, eid or element.eid, element)

    def __str__(self):
        return json.dumps(self.element)

    def __repr__(self):
        return json.dumps(self.element)


class _TauEnterpriseDatabase(object):
    """Represents a connection to the remote database

    Attributes:
        endpoint (str): The URL of the remote database
        status (int): The HTTP status code returned when the connection was opened

    """

    def __init__(self, endpoint, db_name):
        self.db_name = db_name
        self.session = requests.Session()
        # The requested database is sent as an HTTP header
        self.session.headers['Database-Name'] = self.db_name
        request = self.session.get(endpoint)
        request.raise_for_status()
        self.endpoint = endpoint
        self.status = request.status_code

    def tables(self):
        """Get a list of all the tables in the database

        Returns:
            A list of the target names for the tables in the database.

        Raises:
            ConnectionError: Unable to establish a connection to the endpoint.
            HTTPError: The server did not understand the request.
        """

        request = self.session.get(self.endpoint)
        request.raise_for_status()
        response = request.json()
        if '_links' in response and 'child' in response['_links']:
            return [table['href'] for table in response['_links']['child']]
        else:
            return []

    def table(self, table_name):
        """Get a table object for a table in this database.

        Args:
            table_name (str): The name of the table requested

        Returns:
            A table object for the table `table_name`

        Raises:
            ConnectionError: Unable to establish a connection to the endpoint.
            HTTPError: The server did not understand the request.
        """
        return _TauEnterpriseTable(self, table_name)

    def purge(self):
        """Delete every record in every table in the database.

        Raises:
            ConnectionError: Unable to establish a connection to the endpoint.
            HTTPError: The server did not understand the request.
        """
        for table in self.tables():
            _TauEnterpriseTable(self, table).purge()


class _TauEnterpriseTable(object):
    """Represents a table within the remote database.
     Operations on the table are made through this class.

    Attributes:
        database (_TauEnterpriseDatabase): The database of which this table is a member.
        name (str): The name of the table within the database.
    """

    Record = _TauEnterpriseJsonRecord

    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.endpoint = "{}/{}".format(database.endpoint, name.lower())
        self.session = database.session

    def _to_record(self, record):
        """Removes server-produced metadata from query results"""
        return _TauEnterpriseJsonRecord(self.database,
                                        {k: v for k, v in record.iteritems() if not k.startswith('_')},
                                        eid=record['_id'] if '_id' in record else None)

    @staticmethod
    def _query_to_match_any(cond):
        """Converts a query in the form of a dict from match-all form to match-any form"""
        return {'$or': [{k: v} for k, v in cond.iteritems()]}

    def search(self, cond, match_any=False):
        if cond is None:
            cond = {}
        if match_any:
            cond = self._query_to_match_any(cond)
        url = "{}/?where={}".format(self.endpoint, json.dumps(cond))
        request = self.session.get(url)
        request.raise_for_status()
        response = request.json()
        if '_meta' in response and response['_meta']['total'] > 0:
            return [self._to_record(result) for result in response['_items']]
        else:
            return []

    def _get(self, keys=None, eid=None, match_any=False, delete=False):
        if match_any and keys is not None:
            keys = self._query_to_match_any(keys)
        if eid is not None:
            url = "{}/{}".format(self.endpoint, eid)
        elif isinstance(keys, dict):
            url = "{}/?where={}".format(self.endpoint, json.dumps(keys))
        elif isinstance(keys, six.string_types):
            url = "{}/?where={}".format(self.endpoint, keys)
        else:
            return None
        if delete:
            request = self.session.delete(url)
            request.raise_for_status()
            return
        else:
            request = self.session.get(url)
        request.raise_for_status()
        response = request.json()
        if '_id' in response:
            # A single item was returned
            return self._to_record(response)
        elif '_meta' in response and response['_meta']['total'] > 0:
            # More that one item was returned
            return self._to_record(response['_items'][0])
        else:
            # No items were returned
            return None

    def get(self, keys=None, eid=None, match_any=False):
        return self._get(keys=keys, eid=eid, match_any=False)

    def remove(self, keys=None, eid=None, match_any=False):
        return self._get(keys=keys, eid=eid, match_any=False, delete=True)

    def count(self, cond, match_any=False):
        if cond is None:
            return None
        matches = self.search(cond, match_any)
        return len(matches)

    def insert(self, element):
        request = self.session.post(self.endpoint, json.dumps(element), headers={'Content-Type': 'application/json'})
        request.raise_for_status()
        return _TauEnterpriseJsonRecord(self.database, element, eid=request.json()['_id'])

    def update(self, fields, keys=None, eids=None, match_any=False):
        update_ids = []
        if isinstance(eids, (list, tuple)):
            update_ids = eids
        elif isinstance(eids, self.Record.eid_type):
            update_ids = [eids]
        elif keys is not None:
            update_ids = [record.eid for record in self.search(keys, match_any=match_any)]
        for update_id in update_ids:
            url = "{}/{}".format(self.endpoint, update_id)
            request = self.session.patch(url, json.dumps(fields), headers={'Content-Type': 'application/json'})
            request.raise_for_status()

    def purge(self):
        request = self.session.delete(self.endpoint)
        request.raise_for_status()


class TauEnterpriseStorage(AbstractStorage):
    """A remote storage system accessed through a REST API.

    Attributes:
         (str): Absolute path to database file.
    """

    Record = _TauEnterpriseJsonRecord

    def __init__(self, name, prefix):
        super(TauEnterpriseStorage, self).__init__(name)
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

    def connect_filesystem(self, *args, **kwargs):
        """Prepares the store filesystem for reading and writing."""
        # TODO
        raise NotImplementedError

    def disconnect_filesystem(self, *args, **kwargs):
        """Disconnects the store filesystem."""
        # TODO
        raise NotImplementedError

    def connect_database(self, *args, **kwargs):
        """Open the database for reading and writing.

        Args:
            url (str): URL of the database to connect to.
            db_name (str): The name of the database to use

        Returns:
            bool: True if a new connection was made, false otherwise.
        """
        if self._database is None:
            self._database = _TauEnterpriseDatabase(kwargs['url'], kwargs['db_name'])
            return True
        else:
            return False

    def disconnect_database(self, *args, **kwargs):
        """Close the database for reading and writing."""
        if self._database:
            self._database = None

    @property
    def prefix(self):
        return self._prefix

    def __str__(self):
        """Human-readable identifier for this database."""
        # pylint: disable=protected-access
        return self._database.endpoint

    def __enter__(self):
        """Initiates the database transaction."""
        # TODO
        raise NotImplementedError

    def __exit__(self, ex_type, value, traceback):
        """Finalizes the database transaction."""
        raise NotImplementedError

    def table(self, table_name):
        if self._database is None:
            raise InternalError("Attempt to get table when no database is connected.")
        if table_name is None:
            return _TauEnterpriseTable(self._database, 'key')
        else:
            return _TauEnterpriseTable(self._database, table_name)

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
        elif isinstance(keys, dict) and keys:
            return table.get(keys=keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
            return [self.get(key, table_name=table_name, match_any=match_any) for key in keys]
        else:
            raise ValueError(keys)
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
        table = self.table(table_name)
        if keys is None:
            return table.search(cond=None)
        elif isinstance(keys, self.Record.eid_type):
            element = table.get(eid=keys)
            return [element] if element else []
        elif isinstance(keys, dict) and keys:
            return table.search(keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
            result = []
            for key in keys:
                result.extend(self.search(keys=key, table_name=table_name, match_any=match_any))
            return result
        else:
            raise ValueError(keys)

    def search_inside(self, field, value, table_name=None):
        """Find multiple records such that a field either equals a value, or is a collection which contains that value.

        Args:
            field (str): Name of the data field to match.
            value: The value which the field must equal or contain
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.

        Returns:
            list: Matching data records.

        Raises:
            ValueError: Invalid value for `keys`.
        """
        query = {field: {'$in': [value]}}
        return self.search(keys=query, table_name=table_name)

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
        raise NotImplementedError


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
        if keys is None:
            return False
        elif isinstance(keys, dict):
            return self.table(table_name).count(keys, match_any=match_any) > 0
        elif isinstance(keys, (list, tuple)):
            return [self.contains(keys=key, table_name=table_name, match_any=match_any) for key in keys]
        elif isinstance(keys, self.Record.eid_type):
            return self.get(keys, table_name=table_name, match_any=match_any) is not None
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
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """
        table = self.table(table_name)
        if isinstance(keys, self.Record.eid_type):
            table.update(fields, eids=[keys])
        elif isinstance(keys, dict):
            table.update(fields, keys=keys)
        elif isinstance(keys, (list, tuple)):
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
        update_fields = {field: None for field in fields}
        table.update(update_fields, eids=[keys])

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
        if keys is None:
            return None
        elif isinstance(keys, self.Record.eid_type):
            table.remove(eid=keys)
        elif isinstance(keys, dict) and keys:
            table.remove(keys=keys, match_any=match_any)
        elif isinstance(keys, (list, tuple)):
            for key in keys:
                self.remove(key, table_name=table_name, match_any=match_any)
        else:
            raise ValueError(keys)

    def purge(self, table_name=None):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractDatabase.table`.
        """
        table = self.table(table_name)
        table.purge()
