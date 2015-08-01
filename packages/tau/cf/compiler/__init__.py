#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

from tau.error import ConfigurationError, InternalError
from tau.cf.compiler.role import *

class Compiler(object):
    """Information about a compiler.
    
    Attributes:
        command: Compiler command without path, e.g. 'icpc'
        family: Compiler family string, e.g. 'Intel'
        role: CompilerRole describing this compiler's role
        tau_wrapper: The corresponding TAU wrapper script, e.g. 'tau_cxx.sh'
        short_descr: A short descriptive string for command line help
    """
    # pylint: disable=too-few-public-methods
    
    def __init__(self, command, family, role):
        from cf.tau import COMPILER_WRAPPERS
        self.command = command
        self.family = family
        self.role = role
        self.tau_wrapper = COMPILER_WRAPPERS[role.keyword]
        self.short_descr = "%s %s compiler" % (self.family, role.language)
    
    def __str__(self):
        return str(dict([(key, val) for (key, val) in self.__dict__.iteritems() if not key.startswith('_')]))


class CompilerSet(object):
    """A collection of Compiler objects, one per required role.
    
    Attributes:
        name: Identifier (hopefully unique) for this combination of compilers.
        CC: Compiler in the 'CC' role
        CXX: Compiler in the 'CXX' role
        etc.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        missing_roles = set([role.keyword for role in REQUIRED_ROLES])
        for key, comp in kwargs.iteritems():
            if key not in KNOWN_ROLES:
                raise InternalError("Invalid role: %s" % role)
            setattr(self, key, comp)
            missing_roles.remove(key)
        for role in missing_roles:
            raise InternalError("Required role %s not defined" % role)


SYSTEM_FAMILY_NAME = 'System'
GNU_FAMILY_NAME = 'GNU'
INTEL_FAMILY_NAME = 'Intel'
PGI_FAMILY_NAME = 'PGI'
MPI_FAMILY_NAME = 'MPI'

"""
Compiler commands TAU Commander can recognize.
Fuzzy matching is allowed, e.g. "gcc-4.3" will match to "gcc" 
so don't litter this list with lots of variants.
"""    
KNOWN_COMPILERS = {
    'cc': Compiler('cc', SYSTEM_FAMILY_NAME, CC_ROLE),
    'cxx': Compiler('cxx', SYSTEM_FAMILY_NAME, CXX_ROLE),
    'c++': Compiler('c++', SYSTEM_FAMILY_NAME, CXX_ROLE),
    'ftn': Compiler('ftn', SYSTEM_FAMILY_NAME, FC_ROLE),
    'f77': Compiler('f77', SYSTEM_FAMILY_NAME, F77_ROLE),
    'f90': Compiler('f90', SYSTEM_FAMILY_NAME, F90_ROLE),
    'gcc': Compiler('gcc', GNU_FAMILY_NAME, CC_ROLE),
    'g++': Compiler('g++', GNU_FAMILY_NAME, CXX_ROLE),
    'gfortran': Compiler('gfortran', GNU_FAMILY_NAME, FC_ROLE),
    'icc': Compiler('icc', INTEL_FAMILY_NAME, CC_ROLE),
    'icpc': Compiler('icpc', INTEL_FAMILY_NAME, CXX_ROLE),
    'ifort': Compiler('ifort', INTEL_FAMILY_NAME, FC_ROLE),
    'pgcc': Compiler('pgcc', PGI_FAMILY_NAME, CC_ROLE),
    'pgCC': Compiler('pgCC', PGI_FAMILY_NAME, CXX_ROLE),
    'pgf90': Compiler('pgf90', PGI_FAMILY_NAME, FC_ROLE),
    'mpicc': Compiler('mpicc', MPI_FAMILY_NAME, CC_ROLE),
    'mpicxx': Compiler('mpicxx', MPI_FAMILY_NAME, CXX_ROLE),
    'mpic++': Compiler('mpic++', MPI_FAMILY_NAME, CXX_ROLE),
    'mpif90': Compiler('mpif90', MPI_FAMILY_NAME, FC_ROLE)}

"""
Compiler families TAU Commander can recognize.
A nice way to search KNOWN_COMPILERS by family name. 
"""
KNOWN_FAMILIES = {}
for _ in KNOWN_COMPILERS.itervalues():
    fam = _.family
    KNOWN_FAMILIES.setdefault(fam, [])
    KNOWN_FAMILIES[fam].append(_)