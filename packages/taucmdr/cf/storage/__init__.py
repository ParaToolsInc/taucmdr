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
TAU Storage Containers.

A storage container provides a record database, a persistent filesystem, and a key/value store.
The database is accessed via member methods like :any:`insert`, :any:`search`, etc.
The filesystem is accessed via its filesystem prefix (e.g. ``/usr/local/packages``) via :any:`prefix`.
The key/value store is accessed via the `[]` operator, i.e. treat the storage object like a dictionary.
"""


from abc import ABCMeta, abstractmethod
from taucmdr.error import Error


class StorageError(Error):
    """Indicates a failure in the storage system."""

    message_fmt = ("%(value)s\n"
                   "%(hints)s\n")


class StorageRecord(object):
    """A record in the storage container's database.
    
    Attributes:
        eid_type: Element identifier type.
        storage: Storage container whos database contains this record.
        eid: Element identifier value.
        element (dict): The database element as a dictionary. 
    """
    eid_type = str

    def __init__(self, storage, eid, element):
        self.storage = storage
        self.eid = eid
        self.element = element

    def __getitem__(self, key):
        return self.element[key]
    
    def get(self, key, default=None):
        return self.element.get(key, default)

    def __iter__(self):
        return iter(self.element)
    
    def __contains__(self, key):
        return key in self.element

    def items(self):
        return self.element.items()

    def keys(self):
        return self.element.keys()
    
    def iteritems(self):
        return self.element.iteritems()
    
    def iterkeys(self):
        return self.element.iterkeys()
 
    def itervalues(self):
        return self.element.itervalues()
 
    def __len__(self):
        return len(self.element)
    
    def __str__(self):
        return str(self.element)
    
    def __repr__(self):
        return repr(self.element)


class AbstractStorage(object):
    """Abstract base class for storage containers.
    
    A storage container provides a record database, a persistent filesystem, and a key/value store.
    The database is accessed via member methods like :any:`insert`, :any:`search`, etc.
    The filesystem is accessed via its filesystem prefix (e.g. ``/usr/local/packages``) via :any:`prefix`.
    The key/value store is accessed via the `[]` operator, i.e. treat the storage object like a dictionary.
    
    Attributes:
        name (str): The storage container's name, e.g. "system" or "user".
        prefix (str): Absolute path to the top-level directory of the container's filesystem.
        database (str): Database object implementing :any:`AbstractDatabase`. 
    """

    __metaclass__ = ABCMeta
    
    Record = StorageRecord

    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.name

    @abstractmethod
    def __len__(self):
        """Return the number of items in the key/value store."""
    
    @abstractmethod    
    def __getitem__(self, key):
        """Retrieve a value from the key/value store."""
    
    @abstractmethod
    def __setitem__(self, key, value):
        """Store a value in the key/value store."""
        
    @abstractmethod
    def __delitem__(self, key):
        """Remove a value from the key/value store."""
        
    @abstractmethod
    def __contains__(self, key):
        """Returns True if ``key`` maps to a value is in the key/value store."""
        
    @abstractmethod
    def __iter__(self):
        """Iterate over keys in the key/value store."""
    
    @abstractmethod
    def iterkeys(self):
        """Iterate over keys in the key/value store."""

    @abstractmethod
    def itervalues(self):
        """Iterate over values in the key/value store."""

    @abstractmethod
    def iteritems(self):
        """Iterate over items in the key/value store."""
    
    @abstractmethod
    def connect_filesystem(self, *args, **kwargs):
        """Prepares the store filesystem for reading and writing."""

    @abstractmethod
    def disconnect_filesystem(self, *args, **kwargs):
        """Makes the store filesystem unreadable and unwritable."""

    @abstractmethod
    def connect_database(self, *args, **kwargs):
        """Open the database for reading and writing."""

    @abstractmethod
    def disconnect_database(self, *args, **kwargs):
        """Close the database for reading and writing."""

    @abstractmethod
    def prefix(self):
        """Get the filesystem prefix for file storage.
        
        The filesystem must be persistent and provide the usual POSIX filesystem calls.
        In particular, GNU software packages should be installable in the filesystem.
        
        Returns:
            str: Absolute path in the filesystem.
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
    def count(self, table_name=None):
        """Count the records in the database.
        
        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            
        Returns:
            int: Number of records in the table.
        """

    @abstractmethod    
    def get(self, keys, table_name=None, match_any=False, populate=None):
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
            populate (list): Names of fields containing foreign keys to populate, or None to disable

        Returns:
            Record: The matching data record if `keys` was a self.Record.eid_type or dict.
            list: All matching data records if `keys` was a list or tuple.
            None: No record found or ``bool(keys) == False``.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """

    @abstractmethod
    def search(self, keys=None, table_name=None, match_any=False, populate=None):
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
            populate (list): Names of fields containing foreign keys to populate, or None to disable

        Returns:
            list: Matching data records.
            
        Raises:
            ValueError: Invalid value for `keys`.
        """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def contains(self, keys, table_name=None, match_any=False):
        """Check if the specified table contains at least one matching record.
        
        The behavior depends on the type of `keys`:
            * self.Record.eid_type: check for the record with that element identifier.
            * dict: check for the record with attributes matching `keys`.
            * list or tuple: return the equivilent of ``map(contains, keys)``.
        
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

    @abstractmethod
    def insert(self, data, table_name=None):
        """Create a new record.
        
        If the table doesn't exist it will be created.
        
        Args:
            data (dict): Data to insert in table.
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
            
        Returns:
            Record: The new record.
        """

    @abstractmethod
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
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """

    @abstractmethod      
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
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """

    @abstractmethod        
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
            ValueError: ``bool(keys) == False`` or invaild value for `keys`.
        """

    @abstractmethod
    def purge(self, table_name=None):
        """Delete all records.

        Args:
            table_name (str): Name of the table to operate on.  See :any:`AbstractStorage.table`.
        """

    @abstractmethod
    def is_remote(self):
        """Indicates whether this storage class represents a remote connection

        Returns:
            bool: True if remote, False if local
        """

