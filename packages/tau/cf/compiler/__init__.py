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
# pylint: disable=too-few-public-methods

import os
from tau import logger
from tau.cf import TrackedInstance, KeyedRecord
from tau.error import InternalError 


LOGGER = logger.getLogger(__name__)


class CompilerRole(KeyedRecord):
    """Information about a compiler's role.
    
    Attributes:
        keyword: String identifying how the compiler is used in the build process, e.g. 'CXX'
        language: Language corresponding to the compiler role, e.g. 'C++'
        required: True if this role must be filled to compile TAU, False otherwise
    """
    
    KEY = 'keyword'
    
    def __init__(self, keyword, language, required=False):
        self.keyword = keyword
        self.language = language
        self.required = required
        
    @classmethod
    def required(cls):
        """Yield all roles that must be filled to get TAU to compile."""
        for role in cls.all():
            if role.required:
                yield role


class CompilerInfo(TrackedInstance):
    """Information about a compiler.
    
    The compiler might not be installed in the system.  See InstalledCompiler.  
    
    Attributes:
        command: Command string without path or arguments, e.g. 'icpc'
        family: CompilerFamily this compiler belongs to
        role: CompilerRole describing this compiler's family role
        short_descr: A short descriptive string for command line help
    """

    def __init__(self, command, family, role):
        self.command = command
        self.family = family
        self.role = role
        self.short_descr = "%s %s compiler" % (family.name, role.language)
    
    @classmethod
    def find(cls, command):
        """Find compiler info that matches the given command.
        
        If an exact match cannot be found then information for the longest command
        contained in the passed command is returned.
        
        Examples:
            find("gcc-4.7-x86_64") returns info for "gcc" from possible candidates ["gcc", "cc"]
        
        Args:
            command: Absolute or relative path to a compiler command

        Returns:
            A CompilerInfo object.
            
        Raises:
            KeyError: No compiler info matches the given command.
        """
        command = os.path.basename(command)
        for info in cls.all():
            if info.command == command:
                return info
        # Guess that the longest string is the best match
        LOGGER.debug("No compiler info exactly matches %s, trying approximate match" % command)
        candidates = filter(lambda comp: comp.command in command, cls.all())
        if not candidates:
            raise KeyError
        return max(candidates, key=len)



class CompilerFamily(KeyedRecord):
    """Information about a compiler family.
    
    Attributes:
        name: String identifying this family, e.g. "Intel"
    """
    
    KEY = 'name'
    
    def __init__(self, name):
        self.name = name
        self._info_by_command = {}
        self._info_by_role = {}

    @classmethod
    def all(cls):
        """Iterate over all compiler families.
        
        First value yielded is the host's preferred compiler family.
        Subsequent values can be in any order.
        
        Yields:
           A CompilerFamily object.
        """
        preferred = cls.preferred()
        yield preferred
        for fam in cls._INSTANCES.itervalues():
            if fam.name != preferred.name:
                yield fam
                
    @classmethod
    def preferred(cls):
        """Return the host's preferred compiler family."""
        from tau.cf.target import host
        return host.preferred_compilers()

    @classmethod
    def family_names(cls):
        """Return an alphabetical list of all known compiler family names."""
        return sorted(map(str, cls.all()))
    
    def __iter__(self):
        """Yield information about all compilers in the family.
        
        May yield zero, one, or more CompilerInfo objects for any role,
        however it will not yield the same command multiple times.
        """  
        for info in self._info_by_command.itervalues():
            yield info

    def add(self, role, *commands):
        """Register compiler commands in the given role.
        
        Commands should be ordered by preference.  For example, we prefer to build
        C++ codes with "c++" instead of "CC" so that case-insensitive file systems
        (looking at you Mac OS) don't try to use a C compiler for C++ codes. 
        
        Args:
            role: CompilerRole object specifying role these commands fill in the family
            commands: Command strings without arguments
        """ 
        assert isinstance(role, CompilerRole)
        for command in commands:
            assert isinstance(command, basestring)
            if command in self._info_by_command:
                raise InternalError('Command %s already a member of %s' % (command, self.name))
            info = CompilerInfo(command, self, role)
            self._info_by_command[command] = info
            self._info_by_role.setdefault(role.keyword, []).append(info)
                
    def members_by_role(self, role):
        """Get all compilers in the specified role.
         
        Args:
            role: CompilerRole object
             
        Returns:
            List of CompilerInfo objects
        """
        return self._info_by_role[role.keyword]
     
    def member_by_command(self, command):
        """Get the compiler with the specified command.
         
        Args:
            command: Command string to search for
         
        Returns:
            CompilerInfo object
        """
        return self._info_by_command[command]


CC_ROLE = CompilerRole('CC', 'C', True)
CXX_ROLE = CompilerRole('CXX', 'C++', True)
FC_ROLE = CompilerRole('FC', 'Fortran', True)
UPC_ROLE = CompilerRole('UPC', 'Universal Parallel C')

SYSTEM_COMPILERS = CompilerFamily('System')
SYSTEM_COMPILERS.add(CC_ROLE, 'cc')
SYSTEM_COMPILERS.add(CXX_ROLE, 'c++', 'cxx', 'CC')
SYSTEM_COMPILERS.add(FC_ROLE, 'ftn', 'f90', 'f77')
SYSTEM_COMPILERS.add(UPC_ROLE, 'upc')

GNU_COMPILERS = CompilerFamily('GNU')
GNU_COMPILERS.add(CC_ROLE, 'gcc')
GNU_COMPILERS.add(CXX_ROLE, 'g++')
GNU_COMPILERS.add(FC_ROLE, 'gfortran')
GNU_COMPILERS.add(UPC_ROLE, 'gupc')

INTEL_COMPILERS = CompilerFamily('Intel')
INTEL_COMPILERS.add(CC_ROLE, 'icc')
INTEL_COMPILERS.add(CXX_ROLE, 'icpc')
INTEL_COMPILERS.add(FC_ROLE, 'ifort')

PGI_COMPILERS = CompilerFamily('PGI')
PGI_COMPILERS.add(CC_ROLE, 'pgcc')
PGI_COMPILERS.add(CXX_ROLE, 'pgc++', 'pgcxx', 'pgCC')
PGI_COMPILERS.add(FC_ROLE, 'pgf90', 'pgf77')

IBM_COMPILERS = CompilerFamily('IBM')
IBM_COMPILERS.add(CC_ROLE, 'xlc', )
IBM_COMPILERS.add(CXX_ROLE, 'xlc++', 'xlC')
IBM_COMPILERS.add(FC_ROLE, 'xlf')

CRAY_COMPILERS = SYSTEM_COMPILERS
