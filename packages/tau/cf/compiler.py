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

# TAU modules
import cf
import logger
import error

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
    self.short_descr = "%s Compiler." % language
  
  def __repr__(self):
    return repr(self.__dict__)


COMPILERS = {
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
    'pgcc': CompilerInfo('pgcc', 'CC', 'Portland Group', 'C'),
    'pgCC': CompilerInfo('pgCC', 'CXX', 'Portland Group', 'C++'),
    'pgf77': CompilerInfo('pgf77', 'FC', 'Portland Group', 'FORTRAN77'),
    'pgf90': CompilerInfo('ptf90', 'FC', 'Portland Group', 'Fortran90'),
    'mpicc': CompilerInfo('mpicc', 'CC', 'MPI', 'C'),
    'mpicxx': CompilerInfo('mpicxx', 'CXX', 'MPI', 'C++'),
    'mpic++': CompilerInfo('mpic++', 'CXX', 'MPI', 'C++'),
    'mpiCC': CompilerInfo('mpiCC', 'CXX', 'MPI', 'C++'),
    'mpif77': CompilerInfo('mpif77', 'FC', 'MPI', 'FORTRAN77'),
    'mpif90': CompilerInfo('mpif90', 'FC', 'MPI', 'Fortran90')
    }

FAMILIES = {}
for comp in COMPILERS.itervalues():
  try:
    FAMILIES[comp.family].append(comp)
  except KeyError:
    FAMILIES[comp.family] = [comp]
del comp


def getCompilerInfo(cmd):
  """
  Returns compiler information for `cmd`
  """
  cmd = os.path.basename(cmd)
  try:
    return COMPILERS[cmd]
  except KeyError:
    raise error.ConfigurationError("Unknown compiler command: '%s'", cmd)


def getCompilerFamily(cmd):
  """
  Returns a list of compilers in the same family as `cmd`
  """
  family = FAMILIES[getCompilerInfo(cmd).family]
  LOGGER.debug("Found compiler family for '%s': %s" % (cmd, family))
  return family

