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
from tau import logger, util
from tau.error import ConfigurationError, InternalError
from tau.cf import KeyedRecord, KeyedRecordCreator
from tau.cf.compiler import CompilerInfo, CompilerRole


LOGGER = logger.get_logger(__name__)



class InstalledCompilerCreator(KeyedRecordCreator):    
    def __call__(cls, command):
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
    command (e.g. icc, gcc-4.2, etc.) with a common compiler command.
    
    Attributes:
        absolute_path: Absolute path to the compiler command
        command: Command that invokes the compiler, without path, as a string
        path: Absolute path to folder containing the compiler command
        info: Optional CompilerInfo object describing the compiler invoked by the compiler command, detected if None
    """
    
    __metaclass__ = InstalledCompilerCreator
    
    __key__ = 'absolute_path'

    def __init__(self, absolute_path):
        """Probes the system to find an installed compiler.
        
        May check PATH, file permissions, or other conditions in the system
        to determine if a compiler command is present and executable.
        
        If this compiler command wraps another command, may also attempt to discover
        information about the wrapped compiler as well.
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
            LOGGER.debug("Probing wrapper compiler '%s' to discover wrapped compiler" % self.absolute_path)
            cmd = [self.absolute_path] + self.info.family.show_wrapper_flags
            LOGGER.debug("Creating subprocess: %s" % cmd)
            try:
                stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                raise RuntimeError("%s failed with return code %d: %s" % (cmd, err.returncode, err.output))
            else:
                LOGGER.debug(stdout)
                LOGGER.debug("%s returned 0" % cmd)
            args = stdout.split()
            self.wrapped = WrappedCompiler(args[0])
            try:
                self.wrapped.parse_args(args[1:], self.info.family)
            except IndexError:
                raise RuntimeError("Unexpected output from '%s':\n%s" % (' '.join(cmd), stdout))
        else:
            self.wrapped = None


    def md5sum(self):
        """
        Calculate the MD5 checksum of the installed compiler command executable.
        
        Returns:
            The MD5 sum as a string of hexidecimal digits.
        """
        if not self._md5sum:
            LOGGER.debug("Calculating MD5 of '%s'" % self.absolute_path)
            md5sum = hashlib.md5()
            with open(self.absolute_path, 'r') as compiler_file:
                md5sum.update(compiler_file.read())
            self._md5sum = md5sum.hexdigest()
        return self._md5sum



class WrappedCompiler(InstalledCompiler):
    """Information about the compiler wrapped by another compiler.
    
    Attributes:
        include_path: List of paths to search for include files when compiling with the wrapped compiler.
        library_path: List of paths to search for libraries when linking with the wrapped compiler.
        compiler_flags: List of additional flags used when compiling with the wrapped compiler.
        libraries: List of additional libraries to link when linking with the wrapped compiler.
    """
    def __init__(self, absolute_path):
        super(WrappedCompiler,self).__init__(absolute_path)
        self.include_path = []
        self.library_path = []
        self.compiler_flags = []
        self.libraries = []
        
    def parse_args(self, args, wrapper_family):
        """Parse arguments passed to the wrapped compiler by the compiler wrapper."""
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
        LOGGER.debug("Wrapped compiler flags: %s" % self.compiler_flags)
        LOGGER.debug("Wrapped include path: %s" % self.include_path)
        LOGGER.debug("Wrapped library path: %s" % self.library_path)
        LOGGER.debug("Wrapped libraries: %s" % self.libraries)



class InstalledCompilerSet(KeyedRecord):
    """A collection of installed compilers, one per role if the role can be filled.
    
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

    def __getitem__(self, role):
        return self.members[role]



class InstalledCompilerFamily(KeyedRecord):
    """Encapsulates data on a compiler installation.
    
    Attributes:
        family: CompilerFamily for this installation.
        commands: (command, InstalledCompiler) dictionary listing all installed compiler commands. 
    """
    
    __key__ = 'family'
    
    def __init__(self, family):
        self.family = family
        self.commands = {}
        LOGGER.debug("Detecting %s compiler installation" % family.name)
        for info in family:
            try:
                comp = InstalledCompiler(info.command)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                self.commands[comp.info.command] = comp
                LOGGER.debug("%s %s compiler is %s" % (family.name, comp.info.role.language, comp.absolute_path))

    def __iter__(self):
        """
        Yield one InstalledCompiler for each role filled by any compiler in this installation.
        """
        for role in CompilerRole.all():
            try:
                yield self.preferred(role)
            except KeyError:
                pass
    
    def preferred(self, role):
        """Return the preferred installed compiler for a given role.
        
        Returns:
            InstalledCompiler object.
            
        Raises:
            KeyError: No installed compiler can fill the role.
        """
        for info in self.family.members(role):
            try:
                return self.commands[info.command]
            except KeyError:
                continue
        raise KeyError
