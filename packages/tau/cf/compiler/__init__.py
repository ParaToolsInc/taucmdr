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
will take care of most of the version-specific details if only we get the 
configuration line correct.

TAU depends very strongly on compiler characteristics. Each TAU configuration
is only valid for a single compiler, TAU's feature set changes depending on compiler
family and version, TAU's configure script is easily confused by compilers with
strange names or unusual installation paths, etc.  In most cases, TAU doesn't even 
try to detect the compiler and trusts the user to specify the right "magic words" 
at configuration. Worse, TAU sometimes does probe the compiler to discover things
like MPI headers, except it does such a poor job that many time we get the wrong
answer or simply cause the configure script to fail entirely. This has been a major
painpoints for TAU users.

The reason for this mess is that compiler detection is very hard.  Projects like 
`SciPy`_ that depend on a compiler's stdout stream for compiler detection have more
or less failed in this since compiler messages are exceptionally difficult to parse.
`CMake`_ does a good job by invoking the compiler command and parsing strings out of
a compiled object to detect compiler characteristcs, but that approach is complex 
and still breaks easily.

The TAU Commander compiler knowledgebase associates a compiler command (`icc`)
with characteristics like family (`Intel`) and role (`CC`).  Any compiler commands
intercepted by TAU Commander are matched against the database to discover their
characteristics.

The knowledgebase lists all compilers known to TAU Commander but only some of those
will actually be available on any given system.  Use :any:`InstalledCompiler` and  
related classes to discover installed compilers and to determine features that 
change from system to system.

.. _SciPy: http://www.scipy.org/
.. _CMake: http://www.cmake.org/
"""

import os
import re
import hashlib
import subprocess
from tau import logger, util
from tau.error import ConfigurationError
from tau.cf.objects import TrackedInstance, KeyedRecord

LOGGER = logger.get_logger(__name__)



class Knowledgebase(object):
    """TAU compiler knowledgebase front-end."""
    
    def __init__(self, keyword, description, **kwargs):
        self.keyword = keyword
        self.description = description
        self._families = {}
        self._roles = {}
        for key, val in kwargs.iteritems():
            language, envars = val
            if isinstance(envars, basestring):
                envars = (envars,) 
            self._roles[key] = _CompilerRole(keyword+'_'+key, language, envars, self)

    @classmethod
    def all_roles(cls):
        """Return all known compiler roles."""
        return _CompilerRole.all() 
    
    @classmethod
    def find_role(cls, keyword):
        """Find a compiler role with the given keyword."""
        return _CompilerRole.find(keyword)
    
    @classmethod
    def all_compilers(cls):
        return _CompilerInfo.all()
    
    @classmethod
    def find_compiler(cls, command=None, family=None, role=None):
        return _CompilerInfo.find(command, family, role)

    @property
    def roles(self):
        return self._roles

    @property
    def families(self):
        return self._families

    def iterfamilies(self):
        """Iterate over compiler families in the knowledgebase.
        
        The first family yielded is the host's preferred compiler family.
        All other families may be yielded in any order.
        """
        from tau.cf import target
        host_tau_arch = target.host.tau_arch()
        preferred = host_tau_arch.preferred_families[self]
        yield preferred
        for family in self._families.itervalues():
            if family is not preferred:
                yield family

    def add(self, name, *args, **kwargs):
        """Add a new compiler family to the knowledgebase.
        
        Compilers in the family are specified via keyword arguments.  The key is the same that was
        used to define the role in the knowledgebase **not** :any:`_CompilerRole.keyword`, which is
        calculated from the knowledgebase name and the role keyword. The value is a string or 
        collection of strings specifying compiler commands, e.g. 'gcc' or ('xlf', 'xlf_r').
        
        Args:
            name (str): The compiler family name.
            *args: Positional arguments passed to the :any:`_CompilerFamily` constructor.
            **kwargs: Keyword arguments passed to the :any:`_CompilerFamily` constructor, after
                      any keyword arguments specifying compiler commands are removed.
        
        Returns:
            _CompilerFamily: The new compiler family object.
        """
        members = {}
        for key, role in self._roles.iteritems():
            try:
                member_arg = kwargs.pop(key)
            except KeyError:
                continue
            members[role] = (member_arg,) if isinstance(member_arg, basestring) else member_arg
        kwargs['members'] = members
        family = _CompilerFamily(self, name, *args, **kwargs)
        self._families[name] = family
        return family
    
    def family_names(self):
        """Return an alphabetical list of all compiler family names."""
        return sorted(self._families.keys())


class _CompilerRole(KeyedRecord):
    """Information about a compiler's role.
    
    A compiler role identifies how the compiler is used in the build process. All compilers
    play at least one *role* in their compiler family.  Many compilers can play multiple 
    roles, e.g. icpc can be a C++ compiler in the CXX role, a C compiler in the CC role, 
    or even a linker.  TAU Commander must identify a compiler's role so it can configure TAU.
    
    Attributes:
        keyword (str): Name of the compiler's role, e.g. 'CXX'.
        language (str): Name of the programming language corresponding to the compiler role, e.g. 'C++'.
        envars (tuple): Environment variables commonly used to identify the compiler in  this role, e.g. "CXX" or "CC".
        kbase (Knowledgebase): The knowledgebase instance that created this object.
    """
    
    __key__ = "keyword"
    
    def __init__(self, keyword, language, envars, kbase):
        self.keyword = keyword
        self.language = language
        self.envars = envars
        self.kbase = kbase


class _CompilerFamily(TrackedInstance):
    """Information about a compiler family.
    
    A compiler's family creates associations between different compiler commands
    and assigns compilers to roles.  All compiler commands within a family accept
    similar arguments, and produce compatible object files.

    Attributes:
        kbase (Knowledgebase): The knowledgebase instance that created this object.
        name (str): Family name, e.g. "Intel".
        family_regex (str): Regular expression identifying compiler family in compiler version string.
        version_flags (list): Command line flags that show the compiler version, e.g. '--version'.
        include_path_flags (list): Command line flags that add a directory to the compiler's include path, e.g. '-I'. 
        library_path_flags (list): Command line flags that add a directory to the compiler's library path, e.g. '-L'.
        link_library_flags (list): Command line flags that link a library, e.g. '-l'.
        show_wrapper_flags (list): Command line flags that show the wrapped compiler's command line, e.g. '-show'.
        members (dict): Compilers in this family indexed by role.
    """
    
    _probe_cache = {}
    
    def __init__(self, kbase, name, members,
                 version_flags=None,
                 include_path_flags=None, 
                 library_path_flags=None, 
                 link_library_flags=None,
                 show_wrapper_flags=None,
                 family_regex=None):
        self.kbase = kbase
        self.name = name
        self.family_regex = family_regex
        self.version_flags = version_flags or ['--version', '-E']
        self.include_path_flags = include_path_flags or ['-I']
        self.library_path_flags = library_path_flags or ['-L']
        self.link_library_flags = link_library_flags or ['-l']
        self.show_wrapper_flags = show_wrapper_flags or []
        self.members = {}
        for role, commands in members.iteritems():
            self.members[role] = [_CompilerInfo(self, cmd, role) for cmd in commands]
            
    def installation(self):
        return InstalledCompilerFamily(self)

    @classmethod
    def probe(cls, absolute_path):
        """Determine the compiler family of a given command.

        Executes the command with :any:`version_flags` from all families
        and compares the output against :any:`family_regex`.

        Args:
            absolute_path (str): Absolute path to a compiler command.

        Raises:
            ConfigurationError: Compiler family could not be determined.

        Returns:
            _CompilerFamily: The compiler's family.
        """
        try:
            return cls._probe_cache[absolute_path]
        except KeyError:
            pass
        LOGGER.debug("Probing '%s' to discover compiler family.", absolute_path)
        messages = []
        last_version_flags = None
        stdout = None
        # Settle down pylint... the __instances__ member is created by the metaclass
        # pylint: disable=no-member
        for family in cls.__instances__:
            if not family.family_regex:
                continue
            if family.version_flags != last_version_flags:
                last_version_flags = family.version_flags
                LOGGER.debug("Probing compiler '%s' to discover compiler family", absolute_path)
                cmd = [absolute_path] + family.version_flags
                LOGGER.debug("Creating subprocess: %s", cmd)
                try:
                    stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as err:
                    messages.append(err.output)
                    LOGGER.debug("%s failed with return code %d: %s", cmd, err.returncode, err.output)
                    continue
                else:
                    LOGGER.debug(stdout)
                    LOGGER.debug("%s returned 0", cmd)
            if stdout:
                if re.search(family.family_regex, stdout):
                    LOGGER.debug("'%s' is a %s compiler", absolute_path, family.name)
                    cls._probe_cache[absolute_path] = family
                    return family
                else:
                    LOGGER.debug("'%s' is not a %s compiler", absolute_path, family.name)
        raise ConfigurationError("Cannot determine compiler family: %s" % '\n'.join(messages))


class _CompilerInfo(TrackedInstance):
    """Information about a compiler.
   
    A compiler's basic information includes it's family (e.g. `Intel`) and role (e.g. CXX).
    The compiler might not be installed.  
    
    Attributes:
        family (_CompilerFamily): The family this compiler belongs to.
        command (str): Command without path or arguments, e.g. 'icpc'
        role (_CompilerRole): This compiler's *primary* role in the family.
        short_descr (str): A short description for command line help.
    """

    def __init__(self, family, command, role):
        assert isinstance(family, _CompilerFamily)
        assert isinstance(command, basestring)
        assert isinstance(role, _CompilerRole)
        self.family = family
        self.command = command
        self.role = role
        self.short_descr = "%s %s compiler" % (family.name, role.language)
        
    @classmethod
    def _find(cls, command, family, role):
        # pylint: disable=too-many-return-statements
        if command and family and role:
            return [info for info in family.members.get(role, []) if info.command == command]
        elif command and family:
            return [info for info_list in family.members.itervalues() for info in info_list if info.command == command]
        elif command and role:
            return [info for info in cls.all() if info.role is role and info.command == command]
        elif family and role:
            return family.members.get(role, [])
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
        """Find _CompilerInfo instances that matches the given command and/or family and/or role.
        
        Args:
            command (str): A compiler command without path.
            family (_CompilerFamily): Compiler family to search for.
            role (_CompilerRole): Compiler role to search for.

        Returns:
            list: _CompilerInfo instances matching given compiler information.
        """
        assert command is None or isinstance(command, basestring)
        assert family is None or isinstance(family, _CompilerFamily)
        assert role is None or isinstance(role, _CompilerRole)
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


class InstalledCompilerCreator(type):
    """Cache compiler probe results.
     
    InstalledCompiler invokes a compiler command to discover system-specific compiler characteristics.  
    This can be very expensive, so this metaclass changes the instance creation procedure to only 
    probe the compiler when the compiler command has never been seen before and avoid dupliate
    invocations in a case like::
     
        a = InstalledCompiler('/path/to/icc')
        b = InstalledCompiler('/path/to/icc')    

    Without this metaclass, `a` and `b` would be different instances assigned to the same compiler 
    and `icc` would be probed twice. With this metaclass, ``b is a == True`` and `icc` is only invoked once.
    """
    def __call__(cls, absolute_path, info, **kwargs):
        assert isinstance(absolute_path, basestring) and os.path.isabs(absolute_path)
        assert isinstance(info, _CompilerInfo)
        # Don't allow unchecked values into the instance cache
        if kwargs:
            return super(InstalledCompilerCreator, cls).__call__(absolute_path, info, **kwargs)
        LOGGER.debug('Checking (%s, %s)', absolute_path, info.role.keyword)
        try:
            instance = cls.__instances__[absolute_path, info]
        except KeyError: 
            instance = super(InstalledCompilerCreator, cls).__call__(absolute_path, info, **kwargs)
            cls.__instances__[absolute_path, info] = instance
            LOGGER.debug('Added (%s, %s) to compiler cache', absolute_path, info.role.keyword)
        else:
            LOGGER.debug('Using cached instance')
        return instance


class InstalledCompiler(object):
    """Information about an installed compiler command.
    
    There are relatively few well known compilers, but a potentially infinite
    number of commands that can invoke those compilers.  Additionally, an installed 
    compiler command may be a wrapper around another command.  This class links a
    command (e.g. icc, gcc-4.2, etc.) with a compiler command in the knowledgebase.
    
    Attributes:
        absolute_path (str): Absolute path to the compiler command.
        info (_CompilerInfo): Information about the compiler invoked by the compiler command.
        command (str): Command that invokes the compiler, without path.
        path (str): Absolute path to folder containing the compiler command.
        uid (str): A unique identifier for the installed compiler.
        wrapped (InstalledCompiler): Information about the wrapped compiler, if any.
        include_path (list): Paths to search for include files when compiling with the wrapped compiler.
        library_path (list): Paths to search for libraries when linking with the wrapped compiler.
        compiler_flags (list): Additional flags used when compiling with the wrapped compiler.
        libraries (list): Additional libraries to link when linking with the wrapped compiler.
    """
    
    __metaclass__ = InstalledCompilerCreator
    
    __instances__ = {}

    def __init__(self, absolute_path, info, uid=None, 
                 wrapped=None, include_path=None, library_path=None, compiler_flags=None, libraries=None):
        """Initializes the InstalledCompiler instance.
        
        Any information not provided on the argument list may be probed from the system.
        This can be **VERY** expensive and may involve invoking the compiler, checking PATH, file permissions, 
        or other conditions in the system to determine if a compiler command is present and executable.
        If this compiler command wraps another command, that command is also probed.  The probes recurse
        to the "root" compiler that doesn't wrap any other command.
        
        :any:`uid` uniquely identifies this compiler as installed in the system.  If the compiler's installation
        changes substantially (e.g. significant version upgrades or changes in the compiler wrapper) then the UID
        will change as well.
               
        These probes are necessary because TAU is highly dependent on the compiler used to install TAU.  
        If that compiler changes, or the user tries to "fake out" TAU Commander by renaming compiler
        commands, then the user should be warned that the compiler has changed.  If the change is severe
        then the operation should halt before an invalid operation.
        
        Args:
            absolute_path (str): Absolute path to the compiler command.
            info (_CompilerInfo): Information about the compiler invoked by the compiler command.
            uid (str): A unique identifier for the installed compiler.
            wrapped (InstalledCompiler): Information about the wrapped compiler or None.  If this is None then
                                         all wrapper path arguments (i.e. `include_path`) are ignored.
            include_path (list): Paths to search for include files when compiling with the wrapped compiler.
                                 Ignored if :any:`wrapped` is None.
            library_path (list): Paths to search for libraries when linking with the wrapped compiler.
                                 Ignored if :any:`wrapped` is None.
            compiler_flags (list): Additional flags used when compiling with the wrapped compiler.
                                 Ignored if :any:`wrapped` is None.
            libraries (list): Additional libraries to link when linking with the wrapped compiler.
                                 Ignored if :any:`wrapped` is None.
        """
        self._version_string = None
        self.absolute_path = absolute_path
        self.info = info
        self.command = os.path.basename(absolute_path)
        self.path = os.path.dirname(absolute_path)
        if wrapped:
            assert isinstance(wrapped, InstalledCompiler)
            self.include_path = include_path or []
            self.library_path = library_path or []
            self.compiler_flags = compiler_flags or []
            self.libraries = libraries or []
            self.wrapped = wrapped
        else:
            self.include_path = []
            self.library_path = []
            self.compiler_flags = []
            self.libraries = []
            self.wrapped = self._probe_wrapper()
        if uid:
            self.uid = uid
        else:
            md5 = hashlib.md5()
            md5.update(self.absolute_path)
            md5.update(self.info.family.name)
            md5.update(self.info.role.keyword)
            if self.wrapped:
                md5.update(self.wrapped.uid)
                for attr in 'include_path', 'library_path', 'compiler_flags', 'libraries':
                    for value in getattr(self, attr):
                        md5.update(str(sorted(value)))
            self.uid = md5.hexdigest()
        # Don't need to check the compiler family of compiler wrappers since the compiler
        # the wrapper wraps has already been checked.
        if not self.wrapped and info.family.family_regex:
            if not re.search(info.family.family_regex, self.version_string):
                probed_family = _CompilerFamily.probe(absolute_path)
                raise ConfigurationError("Compiler '%s' is a %s compiler, not a '%s' compiler." %
                                         (absolute_path, probed_family.name, info.family.name))

    def _probe_wrapper(self):
        if not self.info.family.show_wrapper_flags:
            return None
        LOGGER.debug("Probing %s '%s'", self.info.short_descr, self.absolute_path)
        cmd = [self.absolute_path] + self.info.family.show_wrapper_flags
        LOGGER.debug("Creating subprocess: %s", cmd)
        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            # If this command didn't accept show_wrapper_flags then it's not a compiler wrapper to begin with,
            # i.e. another command just happens to be the same as a known compiler command.
            raise ConfigurationError("'%s' isn't actually a %s since it doesn't accept arguments %s." % 
                                     (self.absolute_path, self.info.short_descr, self.info.family.show_wrapper_flags))
        LOGGER.debug(stdout)
        LOGGER.debug("%s returned 0", cmd)
        # Assume the longest line starting with a known compiler command is the wrapped compiler followed by arguments.
        known_commands = set(info.command for info in _CompilerInfo.all())
        wrapped = None
        for line in sorted(stdout.split('\n'), key=len, reverse=True):
            if not line:
                continue
            parts = line.split()
            wrapped_command = parts[0]
            wrapped_args = parts[1:]
            if os.path.basename(wrapped_command) not in known_commands:
                continue
            wrapped_absolute_path = util.which(wrapped_command)
            if not wrapped_absolute_path:
                continue
            if wrapped_absolute_path == self.absolute_path:
                # A wrapper that wraps itself isn't a wrapper, e.g. compilers that ignore invalid arguments
                # when version flags are present.
                return None
            wrapped = self._probe_wrapped(wrapped_absolute_path, wrapped_args)
            if wrapped:
                LOGGER.info("%s '%s' wraps '%s'", self.info.short_descr, self.absolute_path, wrapped.absolute_path)
                break
        else:
            LOGGER.warning("Unable to identify compiler wrapped by wrapper '%s'."
                           " TAU will attempt to continue but may fail later on.", self.absolute_path)
        return wrapped

    def _probe_wrapped(self, wrapped_absolute_path, wrapped_args):
        wrapped_family = _CompilerFamily.probe(wrapped_absolute_path)
        wrapped_command = os.path.basename(wrapped_absolute_path)
        found_info = _CompilerInfo.find(command=wrapped_command, family=wrapped_family)
        if len(found_info) == 1:
            wrapped_info = found_info[0]
            LOGGER.debug("Identified '%s': %s", wrapped_absolute_path, wrapped_info.short_descr)
        elif len(found_info) > 1:
            wrapped_info = found_info[0]
            LOGGER.warning("TAU could not recognize the compiler command '%s',"
                           " but it looks like it might be a %s.", 
                           wrapped_absolute_path, wrapped_info.short_descr)
        else:
            LOGGER.warning("'%s' wraps an unrecognized compiler command '%s'."
                           " TAU will attempt to continue but may fail later on.", 
                           self.absolute_path, wrapped_absolute_path)
            return None
        wrapped = InstalledCompiler(wrapped_absolute_path, wrapped_info)
        try:
            self._parse_wrapped_args(wrapped_args)
        except IndexError:
            LOGGER.warning("Unexpected output from compiler wrapper '%s'."
                           " TAU will attempt to continue but may fail later on.", self.absolute_path)
            return None
        return wrapped

    def _parse_wrapped_args(self, args):
        def parse_flags(idx, flags, acc):
            arg = args[idx]
            for flag in flags:
                if arg == flag:
                    acc.append(args[idx+1])
                    return 2
                elif arg.startswith(flag):
                    acc.append(arg[len(flag):])
                    return 1
            return 0
        idx = 0
        while idx < len(args):
            for flags, acc in [(self.info.family.include_path_flags, self.include_path),
                               (self.info.family.library_path_flags, self.library_path),
                               (self.info.family.link_library_flags, self.libraries)]:
                consumed = parse_flags(idx, flags, acc)
                if consumed:
                    idx += consumed
                    break
            else:
                self.compiler_flags.append(args[idx])
                idx += 1
        LOGGER.debug("Wrapper compiler flags: %s", self.compiler_flags)
        LOGGER.debug("Wrapper include path: %s", self.include_path)
        LOGGER.debug("Wrapper library path: %s", self.library_path)
        LOGGER.debug("Wrapper libraries: %s", self.libraries)
        
    @classmethod
    def probe(cls, command, family=None, role=None):
        """Probe the system to discover information about an installed compiler.
        
        Args:
            command (str): Absolute or relative path to an installed compiler command.
            family (_CompilerFamily): Installed compiler's family if known, None otherwise.
            role (_CompilerRole): Installed compiler's role if known, None otherwise.

        Raises:
            ConfigurationError: Unknown compiler command or not enough information given to perform the probe.

        Returns:
            InstalledCompiler: A new InstalledCompiler instance describing the compiler.
        """
        assert isinstance(command, basestring)
        assert isinstance(family, _CompilerFamily) or family is None
        assert isinstance(role, _CompilerRole) or role is None
        absolute_path = util.which(command)
        if not absolute_path:
            raise ConfigurationError("Compiler '%s' not found on PATH" % command)
        command = os.path.basename(absolute_path)
        # Try to identify the compiler with minimal information
        info_list = _CompilerInfo.find(command, family, role)
        if len(info_list) == 1:
            return InstalledCompiler(absolute_path, info_list[0])
        # If that didn't work then identify the compiler's family and try again
        if not family:
            family = _CompilerFamily.probe(absolute_path)
            info_list = _CompilerInfo.find(command, family, role)
        if len(info_list) == 1:
            return InstalledCompiler(absolute_path, info_list[0])
        elif len(info_list) > 1:
            raise ConfigurationError("%s compiler '%s' is ambiguous: could be any of %s"  % 
                                     (family.name, absolute_path, [info.short_descr for info in info_list]))
        elif len(info_list) == 0:
            raise ConfigurationError("Unknown %s compiler '%s'" % (family.name, absolute_path))
        return InstalledCompiler(absolute_path, info_list[0])

    def unwrap(self):
        """Iterate through layers of compiler wrappers to find the true compiler.
        
        Returns:
            InstalledCompiler: Compiler wrapped by this compiler, ``self`` if this compiler doesn't wrap another.
        """
        comp = self
        while comp.wrapped:
            comp = comp.wrapped
        return comp
    
    @property
    def version_string(self):
        """Get the compiler's self-reported version info.
        
        Usually whatever the compiler prints when the --version flag is provided.
        
        Returns:
            str: The compilers' version string.
        """
        if self._version_string is None:
            cmd = [self.absolute_path] + self.info.family.version_flags
            try:
                self._version_string = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                raise ConfigurationError("Invalid version flags %s for compiler '%s'" % 
                                         (self.info.family.version_flags, self.absolute_path))
        return self._version_string


class InstalledCompilerFamily(object):
    """Information about an installed compiler family.
     
    Compiler families are usually installed at a common prefix but there is no
    guarantee that all members of the family will be installed.  For example,
    it is often the case that C and C++ compilers are installed but no Fortran
    compiler is installed.  This class tracks which members of a compiler family
    are actually installed on the system.
     
    Attributes:
        family (_CompilerFamily): The installed family.
        FIXME: members 
    """

    def __init__(self, family):
        self.family = family
        self.members = {}
        LOGGER.debug("Detecting %s compiler installation", family.name)
        for role, info_list in family.members.iteritems():
            for info in info_list:
                absolute_path = util.which(info.command)
                if absolute_path:
                    LOGGER.debug("%s %s compiler is '%s'", family.name, info.role.language, absolute_path)
                    installed = InstalledCompiler(absolute_path, info)
                    self.members.setdefault(role, []).append(installed)
        if not self.members:
            raise ConfigurationError("%s compilers not found." % self.family.name)

    def get(self, role, default):
        try:
            return self[role]
        except KeyError:
            return default 

    def __getitem__(self, role):
        """Return the preferred installed compiler for a given role.
        
        Since compiler can perform multiple roles we often have many commands
        that could fit a given role, but only one *preferred* command for the
        role.  For example, `icpc` can fill the CC or CXX roles but `icc` is
        preferred over `icpc` for the CC role.
        
        Args:
            role (_CompilerRole): The compiler role to fill.
        
        Returns:
            InstalledCompiler: The installed compiler for the role.
            
        Raises:
            KeyError: This family has no compiler in the given role.
            IndexError: No installed compiler fills the given role.
        """
        try:
            return self.members[role][0]
        except IndexError:
            raise KeyError

    def __iter__(self):
        """Yield one InstalledCompiler for each role filled by any compiler in this installation."""
        for role in self.family.kbase.roles.itervalues():
            try:
                yield self.members[role][0]
            except (KeyError, IndexError):
                pass


class InstalledCompilerSet(KeyedRecord):
    """A collection of installed compilers, one per role if the role can be filled.
    
    To actually build a software package (or user's application) we must have exactly
    one compiler in each required compiler role.
    
    Attributes:
        uid: A unique identifier for this particular combination of compilers.
        members: (_CompilerRole, InstalledCompiler) dictionary containing members of this set
    """
    
    __key__ = 'uid'
    
    def __init__(self, uid, **kwargs):
        self.uid = uid
        self.members = {}
        self._add_members(**kwargs)
            
    def __contains__(self, key):
        return key in self.members

    def __iter__(self):
        return self.members.__iter__()
    
    def __getitem__(self, key):
        return self.members[key]

    def iterkeys(self):
        return self.members.iterkeys()
    
    def itervalues(self):
        return self.members.itervalues()

    def iteritems(self):
        return self.members.iteritems()

    def _add_members(self, **kwargs):
        for key, val in kwargs.iteritems():
            assert isinstance(val, InstalledCompiler)
            role = Knowledgebase.find_role(key)
            self.members[role] = val

    def modify(self, **kwargs):
        """Build a modified copy of this object."""
        # pylint: disable=protected-access 
        new_uid = hashlib.md5()
        new_uid.update(self.uid)
        new_uid.update(str(sorted(kwargs)))
        compilers = {role.keyword: comp for role, comp in self.members.iteritems()}
        modified = InstalledCompilerSet(new_uid.hexdigest(), **compilers)
        modified._add_members(**kwargs)
        return modified
