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
from tau.error import ConfigurationError, InternalError
from tau.cf import KeyedRecord, KeyedRecordCreator
from tau.cf.compiler import CompilerInfo, CompilerRole


LOGGER = logger.get_logger(__name__)


class InstalledCompilerCreator(KeyedRecordCreator):
    """Metaclass to create a new :any:`InstalledCompiler` instance.
    
    This metaclass greatly improves TAU Commander performance.
    
    InstalledCompiler instances are constructed with an absolute path
    to an installed compiler command.  On initialization, the instance
    invokes the compiler command to discover system-specific compiler
    characteristics.  This can be very expensive, so we change the
    instance creation proceedure to only probe the compiler when the 
    compiler command has never been seen before.  This avoids dupliate
    invocations in a case like::
    
        # `which icc` = '/path/to/icc'
        a = InstalledCompiler('/path/to/icc')
        b = InstalledCompiler('icc')    
    
    Without this metaclass, `a` and `b` would be different instances
    assigned to the same compiler and `icc` would be probed twice. With
    this metaclass, ``b is a == True`` and `icc` is only invoked once.
    """
    def __call__(cls,  *args, **kwargs):
        try:
            command = kwargs['command']
        except KeyError:
            command = args[0]
        assert isinstance(command, basestring)
        if os.path.isabs(command):
            try:
                return cls.__instances__[command]
            except KeyError:
                pass
        absolute_path = util.which(command)
        if not absolute_path:
            raise ConfigurationError("'%s' missing or not executable." % command,
                                     "Check spelling, loaded modules, PATH environment variable, and file permissions")
        return KeyedRecordCreator.__call__(cls, absolute_path)



class InstalledCompiler(KeyedRecord):
    """Information about an installed compiler command.
    
    There are relatively few well known compilers, but a potentially infinite
    number of commands that can invoke those compilers.  Additionally, an installed 
    compiler command may be a wrapper around another command.  This class links a
    command (e.g. icc, gcc-4.2, etc.) with a compiler command in the knowledgebase.
    
    Attributes:
        absolute_path (str): Absolute path to the compiler command.
        command (str): Command that invokes the compiler, without path.
        path (str): Absolute path to folder containing the compiler command.
        info (CompilerInfo): Information about the compiler invoked by the compiler command.
    """
    
    __metaclass__ = InstalledCompilerCreator
    
    __key__ = 'absolute_path'

    def __init__(self, absolute_path, arch_args=[]):
        """Probes the system to find an installed compiler.
        
        May check PATH, file permissions, or other conditions in the system
        to determine if a compiler command is present and executable.
        
        If this compiler command wraps another command, may also attempt to discover
        information about the wrapped compiler as well.
        
        Args:
            absolute_path (str): Absolute path to the compiler command.
        """
        self._md5sum = None
        self.absolute_path = absolute_path
        self.path = os.path.dirname(absolute_path)
        self.command = os.path.basename(absolute_path)
        try:
            self.info = CompilerInfo.find(self.command)
        except KeyError:
            raise RuntimeError("Unknown compiler command '%s'" % self.absolute_path)
        if self.info.family.show_wrapper_flags:
            LOGGER.debug("Probing wrapper compiler '%s' to discover wrapped compiler", self.absolute_path)
            cmd = [self.absolute_path] + self.info.family.show_wrapper_flags + arch_args
            LOGGER.debug("Creating subprocess: %s", cmd)
            try:
                stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                raise RuntimeError("%s failed with return code %d: %s" % (cmd, err.returncode, err.output))
            else:
                LOGGER.debug(stdout)
                LOGGER.debug("%s returned 0", cmd)
            args = stdout.split()
            self.wrapped = WrappedCompiler(args[0])
            try:
                self.wrapped.parse_args(args[1:], self.info.family)
            except IndexError:
                raise RuntimeError("Unexpected output from '%s':\n%s" % (' '.join(cmd), stdout))
        else:
            self.wrapped = None


    def md5sum(self):
        """Calculate the MD5 checksum of the installed compiler command executable.
        
        TAU is highly dependent on the compiler used to install TAU.  If that compiler
        ever changes, or the user tries to "fake out" TAU Commander by renaming compiler
        commands, then the user should be warned that the compiler has changed. 
        
        For now, we use the MD5 checksum of the compiler executable to identify the compiler.
        This may need to change since compiler wrappers can throw this off.
        
        Returns:
            str: The MD5 checksum in hex.
        """
        if not self._md5sum:
            LOGGER.debug("Calculating MD5 of '%s'", self.absolute_path)
            md5sum = hashlib.md5()
            with open(self.absolute_path, 'r') as compiler_file:
                md5sum.update(compiler_file.read())
            self._md5sum = md5sum.hexdigest()
        return self._md5sum



class WrappedCompiler(InstalledCompiler):
    """Information about the compiler wrapped by another compiler.
    
    It's very common to wrap one compiler command with another.  For example, MPI compilers are usually
    just wrappers around system compilers than pass additional arguments to the wrapped compiler.
    We use this class to detect those additional arguments and to set up new compiler wrappers
    of our own.
    
    Attributes:
        include_path (list): Paths to search for include files when compiling with the wrapped compiler.
        library_path (list): Paths to search for libraries when linking with the wrapped compiler.
        compiler_flags (list): Additional flags used when compiling with the wrapped compiler.
        libraries (list): Additional libraries to link when linking with the wrapped compiler.
    """
    def __init__(self, absolute_path):
        super(WrappedCompiler,self).__init__(absolute_path)
        self.include_path = []
        self.library_path = []
        self.compiler_flags = []
        self.libraries = []
        
    def parse_args(self, args, wrapper_family):
        """Parse arguments passed to the wrapped compiler by the compiler wrapper.
        
        Args:
            args (list): Command line arguments added to the wrapped compiler.
            wrapper_family (CompilerFamily): The compiler wrapper's family.
        """
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
            for flags, acc in [(wrapper_family.include_path_flags, self.include_path),
                               (wrapper_family.library_path_flags, self.library_path),
                               (wrapper_family.link_library_flags, self.libraries)]:
                consumed = parse_flags(idx, flags, acc)
                if consumed:
                    idx += consumed
                    break
            else:
                self.compiler_flags.append(args[idx])
                idx += 1
        LOGGER.debug("Wrapped compiler flags: %s", self.compiler_flags)
        LOGGER.debug("Wrapped include path: %s", self.include_path)
        LOGGER.debug("Wrapped library path: %s", self.library_path)
        LOGGER.debug("Wrapped libraries: %s", self.libraries)


class InstalledCompilerFamily(KeyedRecord):
    """Information about an installed compiler family.
    
    Compiler families are usually installed at a common prefix but there is no
    guarantee that all members of the family will be installed.  For example,
    it is often the case that C and C++ compilers are installed but no Fortran
    compiler is installed.  This class tracks which members of a compiler family
    are actually installed on the system.
    
    Attributes:
        family (CompilerFamily): The installed family.
        commands (dict): InstalledCompiler instances indexed by command string. 
    """
    
    __key__ = 'family'
    
    def __init__(self, family):
        self.family = family
        self.commands = {}
        LOGGER.debug("Detecting %s compiler installation", family.name)
        for info in family:
            try:
                comp = InstalledCompiler(info.command)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                self.commands[comp.info.command] = comp
                LOGGER.debug("%s %s compiler is %s", family.name, comp.info.role.language, comp.absolute_path)

    def __iter__(self):
        """Yield one InstalledCompiler for each role filled by any compiler in this installation."""
        for role in CompilerRole.all():
            try:
                yield self.preferred(role)
            except KeyError:
                pass
    
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
            KeyError: No installed compiler can fill the role.
        """
        for info in self.family.members(role):
            try:
                return self.commands[info.command]
            except KeyError:
                continue
        raise KeyError


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
            if key not in all_roles:
                raise InternalError("Invalid role: %s" % key)
            role = CompilerRole.find(key)
            self.members[role] = val

    def __iter__(self):
        return self.members.iteritems()
    
    def __getitem__(self, role):
        return self.members[role]



