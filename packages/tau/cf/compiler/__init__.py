# -*- coding: utf-8 -*-
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
#
"""TAU compiler knowledgebase.

TAU Commander uses this knowledgebase to try to work out what kind of compiler
the user is using to build their code.  We can get away with this because TAU 
itself will take care of most of the version-specific details if only we get 
the configuration line correct.

TAU depends very strongly on compiler characteristics. Each TAU configuration
is only valid for a single compiler, TAU's feature set changes depending on compiler
family and version, TAU's configure script is easily confused by compilers with
strange names or unusual installation paths, etc.  In most cases, TAU doesn't even 
try to detect the compiler and trusts the user to specify the right "magic words" 
at configuration. Worse, TAU sometimes does probe the compiler to discover things
like MPI headers, except it does such a poor job that many time we get the wrong
answer or simply cause the configure script to fail entirely. This has been a major
painpoints for TAU users.

Unfortunately, compiler detection is very hard.  Projects like `SciPy`_ that depend 
on a compiler's stdout stream for compiler detection have more or less failed in this
since compiler messages are exceptionally difficult to parse.  `CMake`_ does a good
job by invoking the compiler command and parsing strings out of a compiled object to
detect compiler characteristcs, but that approach is complex and still breaks easily.

The TAU Commander compiler knowledgebase associates a compiler command (`icc`)
with characteristics like family (`Intel`) and role (`CC`).  Any compiler commands
intercepted by TAU Commander are matched against the database to discover their
characteristics, hence we do not need to invoke the compiler to identify it.

.. _SciPy: http://www.scipy.org/
.. _CMake: http://www.cmake.org/
"""

import os
import re
import subprocess
from tau import logger
from tau.error import ConfigurationError
from tau.cf import TrackedInstance, KeyedRecord
from tau.error import InternalError 


LOGGER = logger.get_logger(__name__)


class CompilerRole(KeyedRecord):
    """Information about a compiler's role.
    
    A compiler role identifies how the compiler is used in the build process. All compilers
    play at least one *role* in their compiler family.  Many compilers can play multiple 
    roles, e.g. icpc can be a C++ compiler in the CXX role, a C compiler in the CC role, 
    or even a linker.  TAU Commander must identify a compiler's role so it can configure TAU.
    
    Attributes:
        keyword (str): Name of the compiler's role, e.g. 'CXX'.
        language (str): Name of the programming language corresponding to the compiler role, e.g. 'C++'.
        required (bool): True if this role must be filled to compile TAU, False otherwise.
    """
    
    __key__ = 'keyword'
    
    def __init__(self, keyword, language):
        self.keyword = keyword
        self.language = language


class CompilerInfo(TrackedInstance):
    """Information about a compiler.
    
    A compiler's basic information includes it's family (e.g. `Intel`) and role (e.g. CXX).
    The compiler might not be installed.  
    
    Attributes:
        command (str): Command without path or arguments, e.g. 'icpc'
        family (CompilerFamily): The family this compiler belongs to.
        role (CompilerRole): This compiler's *primary* role in the family.
        short_descr (str): A short description for command line help.
    """

    def __init__(self, command, family, role):
        self.command = command
        self.family = family
        self.role = role
        self.short_descr = "%s %s compiler" % (family.name, role.language)
        
    @classmethod
    def _find(cls, command, family, role):
        # pylint: disable=too-many-return-statements
        if command and family and role:
            return [info for info in family.members[role] if info.command == command]
        elif command and family:
            return [info for info_list in family.members.itervalues() for info in info_list if info.command == command]
        elif command and role:
            return [info for info in cls.all() if info.role is role and info.command == command]
        elif family and role:
            return family.members[role]
        elif command:
            return [info for info in cls.all() if info.command == command]
        elif family:
            return [info for info_list in family.members.itervalues() for info in info_list]
        elif role:
            return [info for info in cls.all() if info.role is role]
        else:
            return []

    @classmethod
    def find(cls, command=None, family=None, role=None):
        """Find CompilerInfo instances that matches the given command and/or family and/or role.
        
        Args:
            command (str): A compiler command without path.
            family (CompilerFamily): Compiler family to search for.
            role (CompilerRole): Compiler role to search for.

        Returns:
            list: CompilerInfo instances matching given compiler information.
        """
        assert command is None or isinstance(command, basestring)
        assert family is None or isinstance(family, CompilerFamily)
        assert role is None or isinstance(role, CompilerRole)
        found = cls._find(command, family, role)
        if not found:
            if command:
                # Strip version info and try again
                for part in command.split('-'):
                    found = cls._find(part, family, role)
                    if found:
                        break
                else:
                    found = []
        return found

class CompilerFamily(KeyedRecord):
    """Information about a compiler family.
    
    A compiler's family creates associations between different compiler commands
    and assigns compilers to roles.  All compiler commands within a family accept
    similar arguments, and produce compatible object files.

    Attributes:
        name (str): Family name, e.g. "Intel".
        family_regex (str): Regular expression identifying compiler family in compiler version string.
        version_flags (list): Command line flags that show the compiler version, e.g. '--version'.
        include_path_flags (list): Command line flags that add a directory to the compiler's include path, e.g. '-I'. 
        library_path_flags (list): Command line flags that add a directory to the compiler's library path, e.g. '-L'.
        link_library_flags (list): Command line flags that link a library, e.g. '-l'.
        show_wrapper_flags (list): Command line flags that show the wrapped compiler's command line, e.g. '-show'.
    """
    
    __key__ = 'name'
    
    _probe_cache = {}
    
    def __init__(self, name,
                 version_flags=None,
                 include_path_flags=None, 
                 library_path_flags=None, 
                 link_library_flags=None,
                 show_wrapper_flags=None,
                 family_regex=None):
        self.name = name
        self.family_regex = family_regex
        self.version_flags = version_flags or ['--version', '-E']
        self.include_path_flags = include_path_flags or ['-I']
        self.library_path_flags = library_path_flags or ['-L']
        self.link_library_flags = link_library_flags or ['-l']
        self.show_wrapper_flags = show_wrapper_flags or []
        self.members = {}

    @staticmethod
    def _env_preferred_compilers(var_roles):
        """"Check environment variables for default compilers."""
        from tau.cf.compiler.installed import InstalledCompiler
        for var, role in var_roles.iteritems():
            try:
                comp = InstalledCompiler.probe(os.environ[var], role=role)
            except KeyError:
                # Environment variable not set
                continue
            except ConfigurationError as err:
                LOGGER.debug(err)
                continue
            else:
                return comp.info.family
        return None

    @classmethod
    def preferred(cls):
        """The preferred compiler family for the host architecture.

        For example, Cray machines prefer Cray compilers, Linux hosts prefer GNU compilers, etc.
        See :any:`tau.cf.target.host` for more info.
        
        May probe environment variables and file systems in cases where the arch 
        isn't immediately known to Python.  These tests may be expensive so the 
        detected value is cached to improve performance.
        
        Returns:
            CompilerFamily: The host's preferred compiler family.
        """
        try:
            inst = cls._preferred
        except AttributeError:
            from tau.cf import target
            from tau.cf.target import host
            var_roles = {'CC': CC_ROLE, 'CXX': CXX_ROLE, 'FC': FC_ROLE, 'F77': FC_ROLE, 'F90': FC_ROLE}
            inst = cls._env_preferred_compilers(var_roles)
            if inst:
                LOGGER.debug("Preferring %s compilers by environment", inst.name)
            else:
                host_tau_arch = host.tau_arch()
                if host_tau_arch is target.TAU_ARCH_CRAYCNL:
                    inst = CRAY_COMPILERS
                elif host_tau_arch in (target.TAU_ARCH_BGP, target.TAU_ARCH_BGQ):
                    inst = IBM_BG_COMPILERS
                elif host_tau_arch is target.TAU_ARCH_IBM64_LINUX:
                    inst = IBM_COMPILERS
                elif host_tau_arch is target.TAU_ARCH_MIC_LINUX:
                    inst = INTEL_COMPILERS
                else:
                    inst = GNU_COMPILERS
                LOGGER.debug("%s prefers %s compilers by default", host_tau_arch, inst.name)
            cls._preferred = inst
        return inst
    
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
        # Settle down pylint... the __instances__ member is created by the metaclass
        # pylint: disable=no-member
        for instance in cls.__instances__.itervalues():
            if instance is not preferred:
                yield instance
                
    @classmethod
    def family_names(cls):
        """Return an alphabetical list of all known compiler family names."""
        return sorted([inst.name for inst in cls.all()])
    
    @classmethod
    def probe(cls, absolute_path):
        """
        TODO: Docs
        """
        try:
            return cls._probe_cache[absolute_path]
        except KeyError:
            pass
        last_version_flags = None
        # Settle down pylint... the __instances__ member is created by the metaclass
        # pylint: disable=no-member
        for family in cls.__instances__.itervalues():
            if family.family_regex:
                if family.version_flags != last_version_flags:
                    LOGGER.debug("Probing compiler '%s' to discover compiler family", absolute_path)
                    cmd = [absolute_path] + family.version_flags
                    LOGGER.debug("Creating subprocess: %s", cmd)
                    try:
                        stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                    except subprocess.CalledProcessError as err:
                        LOGGER.debug("%s failed with return code %d: %s", cmd, err.returncode, err.output)
                        continue
                    LOGGER.debug(stdout)
                    LOGGER.debug("%s returned 0", cmd)
                    last_version_flags = family.version_flags
                if re.search(family.family_regex, stdout):
                    LOGGER.debug("'%s' is a %s compiler", absolute_path, family.name)
                    cls._probe_cache[absolute_path] = family
                    return family
                LOGGER.debug("'%s' is not a %s compiler", absolute_path, family.name)
        cls._probe_cache[absolute_path] = None
        return None

    def add(self, role, *commands):
        """Register compiler commands in the given role.
        
        Commands should be ordered by preference.  For example, if we prefer to build
        C++ codes with "c++" instead of "CC" so that case-insensitive file systems
        (looking at you OS X) don't try to use a C compiler for C++ codes::
        
            family.add(CXX_ROLE, 'c++', 'CC')
        
        Args:
            role (CompilerRole) Role these commands fill in the family.
            *commands: Command strings without arguments.
        """ 
        assert isinstance(role, CompilerRole)
        for command in commands:
            assert isinstance(command, basestring)
            info = CompilerInfo(command, self, role)
            self.members.setdefault(role, []).append(info)


CC_ROLE = CompilerRole('CC', 'C')
CXX_ROLE = CompilerRole('CXX', 'C++')
FC_ROLE = CompilerRole('FC', 'Fortran')
UPC_ROLE = CompilerRole('UPC', 'Universal Parallel C')

SYSTEM_COMPILERS = CompilerFamily('System')
SYSTEM_COMPILERS.add(CC_ROLE, 'cc')
SYSTEM_COMPILERS.add(CXX_ROLE, 'c++', 'cxx', 'CC')
SYSTEM_COMPILERS.add(FC_ROLE, 'ftn', 'f90', 'f77')
SYSTEM_COMPILERS.add(UPC_ROLE, 'upc')

GNU_COMPILERS = CompilerFamily('GNU', family_regex=r'Free Software Foundation, Inc')
GNU_COMPILERS.add(CC_ROLE, 'gcc')
GNU_COMPILERS.add(CXX_ROLE, 'g++')
GNU_COMPILERS.add(FC_ROLE, 'gfortran')
GNU_COMPILERS.add(UPC_ROLE, 'gupc')

INTEL_COMPILERS = CompilerFamily('Intel', family_regex=r'Intel Corporation')
INTEL_COMPILERS.add(CC_ROLE, 'icc')
INTEL_COMPILERS.add(CXX_ROLE, 'icpc')
INTEL_COMPILERS.add(FC_ROLE, 'ifort')

PGI_COMPILERS = CompilerFamily('PGI', family_regex=r'The Portland Group')
PGI_COMPILERS.add(CC_ROLE, 'pgcc')
PGI_COMPILERS.add(CXX_ROLE, 'pgc++', 'pgcxx', 'pgCC')
PGI_COMPILERS.add(FC_ROLE, 'pgfortran', 'pgf90', 'pgf77')

IBM_COMPILERS = CompilerFamily('IBM')
IBM_COMPILERS.add(CC_ROLE, 'xlc')
IBM_COMPILERS.add(CXX_ROLE, 'xlc++', 'xlC')
IBM_COMPILERS.add(FC_ROLE, 'xlf')

IBM_BG_COMPILERS = CompilerFamily('BlueGene')
IBM_BG_COMPILERS.add(CC_ROLE, 'bgxlc', 'bgxlc_r', 'bgcc', 'bgcc_r', 'bgc89', 'bgc89_r', 'bgc99', 'bgc99_r')
IBM_BG_COMPILERS.add(CXX_ROLE, 'bgxlc++', 'bgxlc++_r', 'bgxlC', 'bgxlC_r')
IBM_BG_COMPILERS.add(FC_ROLE, 'bgxlf', 'bgxlf_r', 'bgf77', 'bgfort77', 'bgxlf90', 'bgxlf90_r', 'bgf90', 
                     'bgxlf95', 'bgxlf95_r', 'bgf95', 'bgxlf2003', 'bgxlf2003_r', 'bgf2003', 'bgxlf2008', 
                     'bgxlf2008_r', 'bgf2008')

CRAY_COMPILERS = CompilerFamily('Cray', show_wrapper_flags=['-craype-verbose', '--version', '-E'])
CRAY_COMPILERS.add(CC_ROLE, 'cc')
CRAY_COMPILERS.add(CXX_ROLE, 'CC')
CRAY_COMPILERS.add(FC_ROLE, 'ftn')
CRAY_COMPILERS.add(UPC_ROLE, 'upc')

