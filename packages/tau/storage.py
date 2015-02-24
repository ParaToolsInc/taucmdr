"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief 

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# Sytem modules
import os
import sys
from tinydb import TinyDB, where
 

# TAU modules
from tau import HELP_CONTACT, EXIT_FAILURE
from environment import USER_PREFIX, SYSTEM_PREFIX
from logger import getLogger
from error import InternalError
from util import mkdirp


LOGGER = logger.getLogger(__name__)


class StorageError(InternalError):
    """
    Indicates that there is a problem with storage
    """
    pass


class Storage(object):
  """
  TODO: Classdocs
  """
  def __init__(self, prefix, db_name='local.json'):
    """
    Create the local storage location
    """
    self._transaction_count = 0
    try:
      mkdirp(prefix)
      LOGGER.debug("Created '%s'" % prefix)
    except:
      raise StorageError('Cannot create directory %r' % path, 'Check that you have `write` access')
    self.dbfile = os.path.join(prefix, db_name)
    try:
      self.db = TinyDB(self.dbfile)
    except:
      raise StorageError('Cannot create %r' % path, 'Check that you have `write` access')
    LOGGER.debug("Opened '%s' for read/write" % self.dbfile)
    
  def __enter__(self):
    """
    Initiates the database transaction
    """
    if self._transaction_count == 0:
      self._db_copy = self.db._read()
    self._transaction_count += 1
    return self
  
  def __exit__(self, type, value, traceback):
    """
    Finalizes the database transaction
    """
    self._transaction_count -= 1
    if type and self._transaction_count == 0:
      self.db._write(self._db_copy)
      self._db_copy = None

  def _getQuery(self, keys, any):
    """
    Returns a query object from a dictionary of keys
    """
    operator = 'or' if any else 'and'
    def _and(lhs, rhs): return (lhs & rhs)
    def _or(lhs, rhs): return (lhs | rhs)
    join = {'and': _and, 'or': _or}[operator]
    iter = keys.iteritems()
    key, val = iter.next()
    query = (where(key) == val)
    for key, value in iter:
      query = join(query, (where(key) == value))
    return query

  def get(self, table_name, keys=None, any=False, eid=None):
    """
    Return the record with the specified keys or element id
    """
    table = self.db.table(table_name)
    if eid is not None:
      LOGGER.debug("%r: get(eid=%r)" % (table_name, eid))
      return table.get(eid=eid)
    elif keys is not None:
      LOGGER.debug("%r: get(keys=%r)" % (table_name, keys))
      return table.get(self._getQuery(keys, any))
    else:
      return None

  def search(self, table_name, keys=None, any=False):
    """
    Return a list of records from the specified table that 
    match any one of the provided keys
    """
    table = self.db.table(table_name)
    if keys:
      LOGGER.debug("%r: search(keys=%r)" % (table_name, keys))
      return table.search(self._getQuery(keys, any))
    else:
      LOGGER.debug("%r: all()" % table_name)
      return table.all()

  def match(self, table_name, field, regex=None, test=None):
    """
    Return a list of records where 'field' matches 'regex'
    """
    table = self.db.table(table_name)
    if test is not None:
      LOGGER.debug('%r: search(where(%r).test(%r))' % (table_name, field, test))
      return table.search(where(field).test(test))
    elif regex is not None:
      LOGGER.debug('%r: search(where(%r).matches(%r))' % (table_name, field, regex))
      return table.search(where(field).matches(regex))
    else:
      LOGGER.debug("%r: search(where(%r).matches('.*'))" % (table_name, field))
      return table.search(where(field).matches('.*'))
  
  def contains(self, table_name, keys=None, any=False, eids=None):
    """
    Return True if the specified table contains at least one 
    record that matches the provided keys or element IDs
    """
    table = self.db.table(table_name)
    if eids is not None:
      LOGGER.debug("%r: contains(eids=%r)" % (table_name, eids))
      if isinstance(eids, list):
        return table.contains(eids=eids)
      else:
        return table.contains(eids=[eids])
    elif keys:
      LOGGER.debug("%r: contains(keys=%r)" % (table_name, keys))
      return table.contains(self._getQuery(keys, any))
    else:
      return False

  def insert(self, table_name, fields):
    """
    Create a new record in the specified table
    """
    LOGGER.debug("%r: Inserting %r" % (table_name, fields))
    return self.db.table(table_name).insert(fields)
  
  def update(self, table_name, fields, keys=None, any=False, eids=None):
    """
    Updates the record that matches keys to contain values from fields
    """
    table = self.db.table(table_name)
    if eids is not None:
      LOGGER.debug("%r: update(%r, eids=%r)" % (table_name, fields, eids))
      if isinstance(eids, list):
        return table.update(fields, eids=eids)
      else:
        return table.update(fields, eids=[eids])
    else:
      LOGGER.debug("%r: update(%r, keys=%r)" % (table_name, fields, keys))
      return table.update(fields, self._getQuery(keys, any))

  def remove(self, table_name, keys=None, any=False, eids=None):
    """
    Remove all records that match keys or eids from table_name 
    """
    table = self.db.table(table_name)
    if eids is not None:
      LOGGER.debug("%r: remove(eids=%r)" % (table_name, eids))
      if isinstance(eids, list):
        return table.remove(eids=eids)
      else:
        return table.remove(eids=[eids])
    else:
      LOGGER.debug("%r: remove(keys=%r)" % (table_name, keys))
      return table.remove(self._getQuery(keys, any))

  def purge(self, table_name):
    """
    Removes all records from the table_name
    """
    LOGGER.debug("%r: purge()" % (table_name))
    return self.db.table(table_name).purge()


user_storage = Storage(USER_PREFIX, 'local.json')
system_storage = Storage(SYSTEM_PREFIX, 'local.json')
