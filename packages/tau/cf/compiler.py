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
#pylint: disable=too-many-instance-attributes
#pylint: disable=too-few-public-methods
#pylint: disable=too-many-arguments

import os
import hashlib
import subprocess
import logger, util
from tau import COMPILER_WRAPPERS
from error import InternalError, ConfigurationError


LOGGER = logger.getLogger(__name__)


"""C compiler role key"""
CC = 'CC'

"""C++ compiler role key"""
CXX = 'CXX'

"""Fortran compiler role key"""
FC = 'FC'

"""Valid compiler roles"""
ROLES = [CC, CXX, FC]


class CompilerSet(object):
    """A collection of CompilerInfo objects, one per role.
    
    Used to select specific compilers for package installation.
    
    Attributes:
        id: Unique identifier for this set of compilers
        cc: C compiler CompilerInfo
        cxx: C++ compiler CompilerInfo
        fc: Fortran compiler CompilerInfo
    """
    # Short names are OK in this class
    # pylint: disable=invalid-name
    
    def __init__(self, cc, cxx, fc):
        self.cc = cc
        self.cxx = cxx
        self.fc = fc
        md5sum = hashlib.md5()
        md5sum.update(self.cc.md5sum)
        md5sum.update(self.cxx.md5sum)
        md5sum.update(self.fc.md5sum)
        self.id = md5sum.hexdigest()
 
    def __str__(self):
        return ', '.join(map(str, [self.cc, self.cxx, self.fc]))


class CompilerInfo(object):
    """Information about a compiler command.
    
    Attributes:
        command: A compiler command without path, e.g. 'gcc'
        role: One of the compiler roles listed in ROLES, e.g. CC
        family: The compiler family string, e.g. 'Intel'
        language: The language this compiler compiles, e.g. 'C'
        tau_wrapper: The corresponding TAU wrapper script, e.g. 'tau_cc.sh'
        short_descr: A short descriptive string for command line help.
        path: The absolute path to folder containing this compiler's command.
              Is None if compiler is not available on this system.
        md5sum: The md5 checksum of the compiler binary.
                Is None if compiler is not available on this system.
        version: The version string from the compiler executable.
                 Is None if compiler is not available on this system.
    """
     
    def __init__(self, command, role, family, language, 
                 path=None, md5sum=None, version=None):
        """Initializes the CompilerInfo object."""
        self.command = command
        self.role = role
        self.family = family
        self.language = language
        self.tau_wrapper = COMPILER_WRAPPERS[role]
        self.short_descr = "%s %s compiler." % (family, language)
        self.path = path
        self.md5sum = md5sum
        self.version = version
        
    def __str__(self):
        return os.path.join(self.path, self.command)
    
    @classmethod
    def identify(cls, compiler_cmd):
        """Returns a CompilerInfo object matching a given command.
        
        Args:
            compiler_cmd: The compiler command to identify, e.g. 'gcc'
        
        Returns:
            A CompilerInfo object initialized for the identified compiler.
            
        Raises:
            ConfigurationError: compiler_cmd was invalid.
        """
        LOGGER.debug("Identifying compiler: %s" % compiler_cmd)
        command = os.path.basename(compiler_cmd)
        path = util.which(compiler_cmd)
        try:
            info = KNOWN_COMPILERS[command]
        except KeyError:
            raise ConfigurationError("Unknown compiler command: '%s'", compiler_cmd)
        if not path:
            raise ConfigurationError("%s %s compiler '%s' missing or not executable." %
                                     (info.family, info.language, compiler_cmd),
                                     "Check spelling, loaded modules, PATH environment "
                                     "variable, and file permissions")
        if not util.file_accessible(path):
            raise ConfigurationError("Compiler '%s' not readable." % (os.path.join(path, command)))
        info.path = os.path.dirname(path)
        md5sum = hashlib.md5()
        with open(path, 'r') as compiler_file:
            md5sum.update(compiler_file.read())
        info.md5sum = md5sum.hexdigest()
        # TODO: Compiler version
        info.version = 'FIXME'       
        return info
    
    @classmethod
    def identify_mpiwrapper(cls, info):
        """Determine what compiler the MPI compiler wrapper is wrapping.
        
        Executes the compiler command and parses the output to determine
        the real compiler.
        
        Args:
            info: A mostly populated CompilerInfo.
            
        Returns:
            CompilerInfo for the wrapped compiler.
        """
        abspath = os.path.join(info.path, info.command) 
        cmd = [abspath, '-show']
        LOGGER.debug("Creating subprocess: cmd=%s" % abspath)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, _ = proc.communicate()
        retval = proc.returncode
        LOGGER.debug(stdout)
        LOGGER.debug("%s returned %d" % (abspath, retval))
        if retval != 0:
            raise InternalError("Command '%s' failed with return code %d" % 
                                (' '.join(cmd), retval))
        wrapped_cmd = stdout.split()[0]
        try:
            wrapped_info = KNOWN_COMPILERS[wrapped_cmd]
        except KeyError:
            raise ConfigurationError("Unknown compiler command: '%s'", wrapped_cmd)
        LOGGER.info("Determined %s is wrapping %s" % (abspath, wrapped_info.short_descr))
        return wrapped_info



KNOWN_COMPILERS = {
    'cc': CompilerInfo('cc', CC, 'system', 'C'),
    'c++': CompilerInfo('c++', CXX, 'system', 'C++'),
    'f77': CompilerInfo('f77', FC, 'system', 'FORTRAN77'),
    'f90': CompilerInfo('f90', FC, 'system', 'Fortran90'),
    'ftn': CompilerInfo('ftn', FC, 'system', 'Fortran90'),
    'gcc': CompilerInfo('gcc', CC, 'GNU', 'C'),
    'g++': CompilerInfo('g++', CXX, 'GNU', 'C++'),
    'gfortran': CompilerInfo('gfortran', FC, 'GNU', 'Fortran90'),
    'icc': CompilerInfo('icc', CC, 'Intel', 'C'),
    'icpc': CompilerInfo('icpc', CXX, 'Intel', 'C++'),
    'ifort': CompilerInfo('ifort', FC, 'Intel', 'Fortran90'),
    'pgcc': CompilerInfo('pgcc', CC, 'PGI', 'C'),
    'pgCC': CompilerInfo('pgCC', CXX, 'PGI', 'C++'),
    'pgf77': CompilerInfo('pgf77', FC, 'PGI', 'FORTRAN77'),
    'pgf90': CompilerInfo('pgf90', FC, 'PGI', 'Fortran90'),
    'mpicc': CompilerInfo('mpicc', CC, 'MPI', 'C'),
    'mpicxx': CompilerInfo('mpicxx', CXX, 'MPI', 'C++'),
    'mpic++': CompilerInfo('mpic++', CXX, 'MPI', 'C++'),
    'mpiCC': CompilerInfo('mpiCC', CXX, 'MPI', 'C++'),
    'mpif77': CompilerInfo('mpif77', FC, 'MPI', 'FORTRAN77'),
    'mpif90': CompilerInfo('mpif90', FC, 'MPI', 'Fortran90')}

KNOWN_FAMILIES = {}
for comp in KNOWN_COMPILERS.itervalues():
    fam = comp.family
    KNOWN_FAMILIES.setdefault(fam, [])
    KNOWN_FAMILIES[fam].append(comp)
del comp
