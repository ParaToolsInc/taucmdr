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

# System modules

# TAU modules
from logger import getLogger
from model.setting import Setting

LOGGER = getLogger(__name__)

_data = {}

def _load():
  for record in Setting.all():
    key = record['key']
    val = record['value'] 
    _data[key] = val
  LOGGER.debug("Loaded settings: %r" % _data)
     
def _save():
  LOGGER.debug("Saving settings: %r" % _data)
  for key, val in _data.iteritems():
    if Setting.exists({'key': key}):
      Setting.update({'value': val}, {'key': key})
    else:
      Setting.create({'key': key, 'value': val})

def get(key):
  """
  Get the value of setting 'key' or None if not set
  """
  if not _data: 
    _load()
  return _data.get(key, None)

def set(key, val):
  """
  Set setting 'key' to value 'val'
  """
  _data[key] = val
  _save()
  
def unset(key):
  """
  Remove setting 'key' from the list of settings
  """
  Setting.delete({'key': key})