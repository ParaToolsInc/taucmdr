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

# TAU modules
import cf
import logger
import error

LOGGER = logger.getLogger(__name__)


class Compiler(object):
  def __init__(self, cmd, role, family, language):
    self.cmd = cmd
    self.tau_cmd = cf.tau.COMPILER_WRAPPERS[role]
    self.family = family
    self.language = language
    self.short_descr = "%s Compiler." % language
    self.usage = "tau build %s [args ...]" % cmd
    self.help = "Invokes the TAU compiler wrapper script '%s' for %s." % (self.tau_cmd, cmd)
    

cc = Compiler('cc', 'CC', 'system', 'C')
c_plus_plus = Compiler('c++', 'CXX', 'system', 'C++')
f77 = Compiler('f77', 'F77', 'system', 'FORTRAN77')
f90 = Compiler('f90', 'F90', 'system', 'Fortran90')
ftn = Compiler('ftn', 'F90', 'system', 'Fortran90')

gcc = Compiler('gcc', 'CC', 'GNU', 'C')
g_plus_plus = Compiler('g++', 'CXX', 'GNU', 'C++')
gfortran = Compiler('gfortran', 'F90', 'GNU', 'Fortran90')

icc = Compiler('icc', 'CC', 'Intel', 'C')
icpc = Compiler('icpc', 'CXX', 'Intel', 'C++')
ifort = Compiler('ifort', 'F90', 'Intel', 'Fortran90')

pgcc = Compiler('pgcc', 'CC', 'Portland Group', 'C')
pgCC = Compiler('pgCC', 'CXX', 'Portland Group', 'C++')
pgf77 = Compiler('pgf77', 'F77', 'Portland Group', 'FORTRAN77')
pgf90 = Compiler('ptf90', 'F90', 'Portland Group', 'Fortran90')

mpicc = Compiler('mpicc', 'CC', 'MPI', 'C')
mpicxx = Compiler('mpicxx', 'CXX', 'MPI', 'C++')
mpic_plus_plus = Compiler('mpic++', 'CXX', 'MPI', 'C++')
mpiCC = Compiler('mpiCC', 'CXX', 'MPI', 'C++')
mpif77 = Compiler('mpif77', 'F77', 'MPI', 'FORTRAN77')
mpif90 = Compiler('mpif90', 'F90', 'MPI', 'Fortran90')


COMPILERS = {'cc': cc,
             'c++': c_plus_plus,
             'f77': f77,
             'f90': f90,
             'ftn': ftn,
             'gcc': gcc,
             'g++': g_plus_plus,
             'gfortran': gfortran,
             'icc': icc,
             'icpc': icpc,
             'ifort': ifort,
             'pgcc': pgcc,
             'pgCC': pgCC,
             'pgf77': pgf77,
             'pgf90': pgf90,
             'mpicc': mpicc,
             'mpicxx': mpicxx,
             'mpic++': mpic_plus_plus,
             'mpiCC': mpiCC,
             'mpif77': mpif77,
             'mpif90': mpif90}

def getFamily(roles):
  pass