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
"""Installed compiler detection.

TAU Commander's compiler knowledgebase lists all compilers known to TAU Commander
but only some of those will actually be available on any given system.  This
module detects installed compilers and can invoke the installed compiler to 
discover features that change from system to system.
"""

import os
import hashlib
import subprocess
from tau import logger, util
from tau.error import InternalError, ConfigurationError
from tau.cf import KeyedRecord
from tau.cf.compiler import CompilerRole, CompilerFamily, CompilerInfo

LOGGER = logger.get_logger(__name__)


class InstalledCompilerCreator(type):
    """Metaclass to create a new :any:`InstalledCompiler` instance.
     
    This metaclass greatly improves TAU Commander performance.
     
    InstalledCompiler instances are constructed with an absolute path
    to an installed compiler command.  On initialization, the instance
    invokes the compiler command to discover system-specific compiler
    characteristics.  This can be very expensive, so we change the
    instance creation procedure to only probe the compiler when the 
    compiler command has never been seen before.  This avoids dupliate
    invocations in a case like::
     
        a = InstalledCompiler('/path/to/icc')
        b = InstalledCompiler('/path/to/icc')    

    Without this metaclass, `a` and `b` would be different instances
    assigned to the same compiler and `icc` would be probed twice. With
    this metaclass, ``b is a == True`` and `icc` is only invoked once.
    """
    def __call__(cls, absolute_path, info, **kwargs):
        assert isinstance(absolute_path, basestring) and os.path.isabs(absolute_path)
        assert isinstance(info, CompilerInfo)
        try:
            instance = cls.__instances__[absolute_path, info]
        except KeyError: 
            LOGGER.debug("No cached compiler installation info for '%s'", absolute_path)
            instance = super(InstalledCompilerCreator, cls).__call__(absolute_path, info, **kwargs)
            cls.__instances__[absolute_path, info] = instance
        else:
            LOGGER.debug("Using cached compiler installation info for '%s'", absolute_path)
        return instance


class InstalledCompiler(object):
    """Information about an installed compiler command.
    
    There are relatively few well known compilers, but a potentially infinite
    number of commands that can invoke those compilers.  Additionally, an installed 
    compiler command may be a wrapper around another command.  This class links a
    command (e.g. icc, gcc-4.2, etc.) with a compiler command in the knowledgebase.
    
    Attributes:
        absolute_path (str): Absolute path to the compiler command.
        info (CompilerInfo): Information about the compiler invoked by the compiler command.
        command (str): Command that invokes the compiler, without path.
        path (str): Absolute path to folder containing the compiler command.
        uid (str): A unique identifier for the installed compiler.
        wrapped (InstalledCompiler): Information about the wrapped compiler, if any.
        include_path (list): Paths to search for include files when compiling with the wrapped compiler.
        library_path (list): Paths to search for libraries when linking with the wrapped compiler.
        compiler_flags (list): Additional flags used when compiling with the wrapped compiler.
        libraries (list): Additional libraries to link when linking with the wrapped compiler.
    """
    
    # FIXME: Caching breaks compiler wrapper probing on cori
    # FIXME: `tau init` with PrgEnv-intel
    # FIXME: `module swap PrgEnv-intel PrgEnv-gnu`
    # FIXME: tau cc foo.c # No warnings, Intel TAU config applied to GNU compiler
    # __metaclass__ = InstalledCompilerCreator
    
    __instances__ = {}

    def __init__(self, absolute_path, info, 
                 uid=None, wrapped=None, include_path=None, library_path=None, compiler_flags=None, libraries=None):
        """Initializes the InstalledCompiler instance.
        
        Any information not provided on the argument list may be probed from the system.
        This can be **VERY** expensive and may involve invoking the compiler, checking PATH, file permissions, 
        or other conditions in the system to determine if a compiler command is present and executable.
        If this compiler command wraps another command, that command may also be probed.  The probes recurse
        to the "root" compiler that doesn't wrap any other command.  In fact, the probe is so expensive we
        emit an INFO-level message whenever it happens.
        
        :any:`uid` uniquely identifies this compiler as installed in the system.  If the compiler's installation
        changes substantially (e.g. significant version upgrades or changes in the compiler wrapper) then the UID
        will change as well.
        
        TAU is highly dependent on the compiler used to install TAU.  If that compiler
        changes, or the user tries to "fake out" TAU Commander by renaming compiler
        commands, then the user should be warned that the compiler has changed.
        
        Args:
            absolute_path (str): Absolute path to the compiler command.
            info (CompilerInfo): Information about the compiler invoked by the compiler command.
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
            self.uid = self._calculate_uid()

    def _calculate_uid(self):
        LOGGER.debug("Calculating UID of '%s'", self.absolute_path)
        uid = hashlib.md5()
        uid.update(self.absolute_path)
        uid.update(self.info.family.name)
        uid.update(self.info.role.keyword)
        if self.wrapped:
            uid.update(self.wrapped.uid)
            for attr in 'include_path', 'library_path', 'compiler_flags', 'libraries':
                for value in getattr(self, attr):
                    uid.update(value)
        return uid.hexdigest()

    def _probe_wrapper(self):
        if not self.info.family.show_wrapper_flags:
            LOGGER.debug("Not probing wrapper: family '%s' does not provide flags to show wrapper flags", 
                         self.info.family.name)
            return None
        LOGGER.info("Probing %s '%s' to discover wrapped compiler", self.info.short_descr, self.absolute_path)
        cmd = [self.absolute_path] + self.info.family.show_wrapper_flags
        LOGGER.debug("Creating subprocess: %s", cmd)
        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            LOGGER.warning("Unable to identify compiler wrapped by wrapper '%s'."
                           " TAU will attempt to continue but may fail later on.", self.absolute_path)
            return None
        LOGGER.debug(stdout)
        LOGGER.debug("%s returned 0", cmd)
        # Assume the longest line starting with an executable is the wrapped compiler followed by arguments.
        wrapped = None
        for line in sorted(stdout.split('\n'), key=len, reverse=True):
            if not line:
                continue
            parts = line.split()
            wrapped_command = parts[0]
            wrapped_args = parts[1:]
            wrapped_absolute_path = util.which(wrapped_command)
            if not wrapped_absolute_path:
                continue
            LOGGER.info("  '%s' wraps '%s'", self.absolute_path, wrapped_absolute_path)
            wrapped = self._probe_wrapped(wrapped_absolute_path, wrapped_args)
            if wrapped:
                break
        else:
            LOGGER.warning("Unable to identify compiler wrapped by wrapper '%s'."
                           " TAU will attempt to continue but may fail later on.", self.absolute_path)
        return wrapped

    def _probe_wrapped(self, wrapped_absolute_path, wrapped_args):
        wrapped_family = CompilerFamily.probe(wrapped_absolute_path)
        wrapped_command = os.path.basename(wrapped_absolute_path)
        found_info = CompilerInfo.find(command=wrapped_command, family=wrapped_family)
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
            self._parse_args(wrapped_args)
        except IndexError:
            LOGGER.warning("Unexpected output from compiler wrapper '%s'."
                           " TAU will attempt to continue but may fail later on.", self.absolute_path)
            return None
        return wrapped

    def _parse_args(self, args):
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
            family (CompilerFamily): Installed compiler's family if known, None otherwise.
            role (CompilerRole): Installed compiler's role if known, None otherwise.

        Raises:
            ConfigurationError: Unknown compiler command or not enough information given to perform the probe.

        Returns:
            InstalledCompiler: A new InstalledCompiler instance describing the compiler.
        """
        absolute_path = util.which(command)
        if not absolute_path:
            raise ConfigurationError("Compiler '%s' not found on PATH" % command)
        command = os.path.basename(absolute_path)
        if not family:
            family = CompilerFamily.probe(absolute_path)
        info_list = CompilerInfo.find(command, family, role)
        if len(info_list) > 1:
            raise ConfigurationError("%s compiler '%s' is ambiguous: could be any of %s"  % 
                                     (family.name, absolute_path, [info.short_descr for info in info_list]))
        elif len(info_list) == 0:
            raise ConfigurationError("Unknown %s compiler '%s'" % (family.name, absolute_path))
        return InstalledCompiler(absolute_path, info_list[0])
    
    def get_wrapped(self):
        """Iterate through layers of compiler wrappers to find the true compiler.
        
        Returns:
            InstalledCompiler: Compiler wrapped by this compiler, ``self`` if this compiler doesn't wrap another.
        """
        comp = self
        while comp.wrapped:
            comp = comp.wrapped
        return comp


class InstalledCompilerFamily(object):
    """Information about an installed compiler family.
     
    Compiler families are usually installed at a common prefix but there is no
    guarantee that all members of the family will be installed.  For example,
    it is often the case that C and C++ compilers are installed but no Fortran
    compiler is installed.  This class tracks which members of a compiler family
    are actually installed on the system.
     
    Attributes:
        family (CompilerFamily): The installed family.
        FIXME: members 
    """

    def __init__(self, family):
        self.family = family
        self.members = {}
        LOGGER.debug("Detecting %s compiler installation", family.name)
        for role, info_list in family.members.iteritems():
            for info in info_list:
                absolute_path = util.which(info.command)
                if not absolute_path:
                    LOGGER.debug("%s %s compiler '%s' not found in PATH", 
                                 family.name, info.role.language, info.command)
                else:
                    LOGGER.debug("%s %s compiler is '%s'", family.name, info.role.language, absolute_path)
                    try:
                        installed = InstalledCompiler(absolute_path, info)
                    except ConfigurationError as err:
                        LOGGER.debug(err)
                        continue
                    self.members.setdefault(role, []).append(installed)
        if not self.members:
            raise ConfigurationError("%s compilers not found." % self.family.name)

    def preferred(self, role):
        """Return the preferred installed compiler for a given role.
        
        Since compiler can perform multiple roles we often have many commands
        that could fit a given role, but only one *preferred* command for the
        role.  For example, `icpc` can fill the CC or CXX roles but `icc` is
        preferred over `icpc` for the CC role.
        
        Args:
            role (CompilerRole): The compiler role to fill.
        
        Returns:
            InstalledCompiler: The installed compiler for the role.
            
        Raises:
            KeyError: This family has no compiler in the given role.
            IndexError: No installed compiler fills the given role.
        """
        return self.members[role][0]

    def __iter__(self):
        """Yield one InstalledCompiler for each role filled by any compiler in this installation."""
        for role in CompilerRole.all():
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
        members: (CompilerRole, InstalledCompiler) dictionary containing members of this set
    """
    
    __key__ = 'uid'
    
    def __init__(self, uid, **kwargs):
        self.uid = uid
        self.members = {}
        all_roles = CompilerRole.keys()
        for key, val in kwargs.iteritems():
            assert isinstance(val, InstalledCompiler)
            if key not in all_roles:
                raise InternalError("Invalid role: %s" % key)
            role = CompilerRole.find(key)
            self.members[role] = val

    def __iter__(self):
        return self.members.iteritems()
    
    def __getitem__(self, role):
        return self.members[role]
