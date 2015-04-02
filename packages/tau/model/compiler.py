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
import logger
import settings
import error
import controller
import util
import cf.tau
from model.project import Project
from model.target import Target


LOGGER = logger.getLogger(__name__)


class CompilerInfo(object):
  """
  Information about a compiler command
  """
  def __init__(self, cmd, role, family, language):
    self.command = cmd
    self.role = role
    self.family = family
    self.language = language
    self.tau_wrapper = cf.tau.COMPILER_WRAPPERS[role]
    self.short_descr = "%s %s compiler." % (family, language)
  def __repr__(self):
    return repr(self.__dict__)

KNOWN_COMPILERS = {
    'cc': CompilerInfo('cc', 'CC', 'system', 'C'),
    'c++': CompilerInfo('c++', 'CXX', 'system', 'C++'),
    'f77': CompilerInfo('f77', 'FC', 'system', 'FORTRAN77'),
    'f90': CompilerInfo('f90', 'FC', 'system', 'Fortran90'),
    'ftn': CompilerInfo('ftn', 'FC', 'system', 'Fortran90'),
    'gcc': CompilerInfo('gcc', 'CC', 'GNU', 'C'),
    'g++': CompilerInfo('g++', 'CXX', 'GNU', 'C++'),
    'gfortran': CompilerInfo('gfortran', 'FC', 'GNU', 'Fortran90'),
    'icc': CompilerInfo('icc', 'CC', 'Intel', 'C'),
    'icpc': CompilerInfo('icpc', 'CXX', 'Intel', 'C++'),
    'ifort': CompilerInfo('ifort', 'FC', 'Intel', 'Fortran90'),
    'pgcc': CompilerInfo('pgcc', 'CC', 'PGI', 'C'),
    'pgCC': CompilerInfo('pgCC', 'CXX', 'PGI', 'C++'),
    'pgf77': CompilerInfo('pgf77', 'FC', 'PGI', 'FORTRAN77'),
    'pgf90': CompilerInfo('pgf90', 'FC', 'PGI', 'Fortran90'),
    'mpicc': CompilerInfo('mpicc', 'CC', 'MPI', 'C'),
    'mpicxx': CompilerInfo('mpicxx', 'CXX', 'MPI', 'C++'),
    'mpic++': CompilerInfo('mpic++', 'CXX', 'MPI', 'C++'),
    'mpiCC': CompilerInfo('mpiCC', 'CXX', 'MPI', 'C++'),
    'mpif77': CompilerInfo('mpif77', 'FC', 'MPI', 'FORTRAN77'),
    'mpif90': CompilerInfo('mpif90', 'FC', 'MPI', 'Fortran90')
    }

KNOWN_FAMILIES = {}
for comp in KNOWN_COMPILERS.itervalues():
  family = comp.family
  KNOWN_FAMILIES.setdefault(family, [])
  KNOWN_FAMILIES[family].append(comp)
del comp

class Compiler(controller.Controller):
  """
  Compiler data model controller
  """
  
  attributes = {
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
  
  def __str__(self):
    return self['command']
  
  def absolutePath(self):
    return os.path.join(self['path'], self['command'])

  @classmethod
  def identify(cls, compiler_cmd):
    """
    Identifies a compiler executable from `compiler_cmd`
    """
    LOGGER.debug("Identifying compiler: %s" % compiler_cmd)
    command = os.path.basename(compiler_cmd)
    path = util.which(compiler_cmd)
    try:
      info = KNOWN_COMPILERS[command]
    except KeyError:
      raise error.ConfigurationError("Unknown compiler command: '%s'", compiler_cmd)
    if not path:
      raise error.ConfigurationError("%s %s compiler '%s' missing or not executable." % 
                                     (info.family, info.language, compiler_cmd), 
                                     "Check spelling, loaded modules, PATH environment variable, and file permissions")
    if not util.file_accessible(path):
      raise error.ConfigurationError("Compiler '%s' not readable." % (os.path.join(path, command)))

    md5sum = hashlib.md5()
    with open(path, 'r') as compiler_file:
      md5sum.update(compiler_file.read())
    md5 = md5sum.hexdigest()

    # TODO: Compiler version
    version = 'FIXME'
    
    fields = {'command': command,
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
    return found

  @classmethod
  def getSiblings(cls, compiler):
    """
    TODO: Docs
    """
    LOGGER.debug("Getting compilers for '%s'" % compiler)

    compilers = {compiler['role']: compiler}
    for known in KNOWN_COMPILERS.itervalues():
      LOGGER.debug("Checking %s" % known)
      if (known.family == compiler['family']) and (known.role != compiler['role']):
        try:
          other = cls.identify(known.command)
        except error.ConfigurationError, e:
          LOGGER.debug(e)
          continue
        if os.path.dirname(other['path']) == os.path.dirname(compiler['path']):
          LOGGER.debug("Found %s compiler '%s' matching '%s'" % (other['role'], other['command'], compiler['command']))
          compilers[other['role']] = other

    try:
      cc = compilers['CC']
    except KeyError:
      raise error.ConfigurationError("Cannot find C compiler for %s" % compiler)
    try:
      cxx = compilers['CXX']
    except KeyError:
      raise error.ConfigurationError("Cannot find C++ compiler for %s" % compiler)
    try:
      fc = compilers['FC']
    except KeyError:
      raise error.ConfigurationError("Cannot find Fortran compiler for %s" % compiler)

    return cc, cxx, fc
