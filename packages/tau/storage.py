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
from tinyrecord import transaction

# TAU modules
from tau import USER_PREFIX, SYSTEM_PREFIX, HELP_CONTACT, EXIT_FAILURE
from logger import getLogger
from error import Error
from util import mkdirp


LOGGER = getLogger(__name__)


class StorageError(Error):
    """
    Indicates that there is a problem with storage
    """
    def __init__(self, value, hint="Contact %s for help" % HELP_CONTACT):
        super(StorageError, self).__init__(value)
        self.hint = hint
        
    def handle(self):
        hint = 'Hint: %s\n' % self.hint if self.hint else ''
        message = """
%(value)s

%(hint)s""" % {'value': self.value, 'hint': hint}
        LOGGER.critical(message)
        sys.exit(EXIT_FAILURE)


def _safe_openDB(prefix, db_name='local.json'):
  """
  Create the local storage location and return a TinyDB object
  """
  try:
    mkdirp(prefix)
  except:
    raise StorageError('Cannot create directory %r' % path, 'Check that you have `write` access')
  try:
    return TinyDB(os.path.join(prefix, db_name))
  except:
    raise StorageError('Cannot create %r' % path, 'Check that you have `write` access')

# Initialize the user-space database
_user_db = _safe_openDB(USER_PREFIX, 'local.json')

# Initialize the system-space database
_system_db = _safe_openDB(SYSTEM_PREFIX, 'local.json')


def _get_table(table_name, system=False):
  """
  Returns a handle for the table with the given name
  """
  db = _system_db if system else _user_db
  return db.table(table_name)


def _get_query(keys, operator='or'):
  """
  Returns a query object from a dictionary of keys
  """
  def _and(lhs, rhs): return (lhs & rhs)
  def _or(lhs, rhs): return (lhs | rhs)
  join = {'and': _and, 'or': _or}[operator]
  iter = keys.iteritems()
  key, val = iter.next()
  query = (where(key) == val)
  for key, value in iter:
    query = join(query, (where(key) == value))
  return query


def transact(table_name, callback, system=False):
  """
  Execute a database transaction on the specified table
  """
  table = _get_table(table_name, system)
  with transaction(table) as tr:
    return callback(tr)


def insert(table_name, model, system=False):
  """
  Create a new record in the specified table
  """
  for attr, desc in model.attributes.iteritems():
    if desc.get('unique', False):
      try:
        value = getattr(model, attr)
      except AttributeError:
        pass
      else:
        if contains(table_name, {attr: value}):
          raise StorageError('A record with %r == %r already exists in %r' % (attr, value, table_name))

  return transact(table_name,
                  lambda table: table.insert(model.data()))


def search(table_name, keys=None, system=False):
  """
  Return a list of records from the specified table that 
  match the provided keys
  """
  table = _get_table(table_name, system)
  if keys:
    # FIXME: transactions don't have a search() method
    return transact(table_name,
                    lambda _: table.search(_get_query(keys)))
  else:
    # FIXME: transactions don't have an all() method
    return transact(table_name,
                lambda _: table.all())

    
def contains(table_name, keys, system=False):
  """
  Return True if the specified table contains at least one 
  record that matches the provided keys
  """
  table = _get_table(table_name, system)
  # FIXME: transactions don't have a contains() method
  return transact(table_name,
                  lambda _: table.contains(_get_query(keys)))


def update(table_name, keys, fields, system=False):
  """
  Updates the record that matches keys to contain values from fields
  """
  return transact(table_name,
                  lambda table: table.update(fields,
                                             _get_query(keys)))


def remove(table_name, keys, system=False):
  """
  Remove all records that match keys
  """
  return transact(table_name,
                  lambda table: table.remove(_get_query(keys)))

