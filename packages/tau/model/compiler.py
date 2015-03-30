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
import os
import hashlib

# TAU modules
import cf
import logger
import settings
import error
import controller
import util
from model.project import Project
from model.target import Target


LOGGER = logger.getLogger(__name__)


class Compiler(controller.Controller):
  """
  Compiler data model controller
  """
  
  attributes = {
    'target': {
      'model': 'Target',
      'required': True,
    },
    'command': {
      'type': 'string',
      'required': True,
    },
    'path': {
      'type': 'string',
      'required': True,
    },
    'md5': {
      'type': 'string',
      'required': True,
    },
    'version': {
      'type': 'string',
      'required': True
    },
    'role': {
      'type': 'string',
      'required': True
    },
    'family': {
      'type': 'string',
      'required': True
    },
    'language': {
      'type': 'string',
      'required': True
    },
    'tau_wrapper': {
      'type': 'string',
      'required': True
    }
  }

  @classmethod
  def identify(cls, target, cmd):
    """
    Identifies a compiler executable from `cmd`
    """
    LOGGER.debug("Identifying compiler: %s" % cmd)
    command = os.path.basename(cmd)
    path = util.which(cmd)
    if not path:
      raise error.ConfigurationError("'%s' missing or not executable", 
                                     "Check the command spelling, PATH environment variable, and file permissions")

    md5sum = hashlib.md5()
    with open(path, 'r') as compiler_file:
      md5sum.update(compiler_file.read())
    md5 = md5sum.hexdigest()

    # TODO: Compiler version
    version = 'FIXME'
    
    info = cf.compiler.getCompilerInfo(command)
    fields = {'target': target.eid,
              'command': command,
              'path': path,
              'md5': md5,
              'version': version,
              'role': info.role,
              'family': info.family,
              'language': info.language,
              'tau_wrapper': info.tau_wrapper}
    
    found = cls.one(keys=fields)
    if found:
      LOGGER.debug("Found compiler record: %s" % found)
    else:
      LOGGER.debug("No compiler record found. Creating new record: %s" % fields)
      found = cls.create(fields)

    if not util.file_accessible(found['path']):
      raise error.ConfigurationError("Compiler '%s' at '%s' not readable." % (found['command'], found['path']))
    
    return found
