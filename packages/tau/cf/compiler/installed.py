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
from tau import logger, util
from tau.error import ConfigurationError, InternalError
from tau.cf import KeyedRecord
from tau.cf.compiler import CompilerInfo, CompilerRole


LOGGER = logger.getLogger(__name__)


class InstalledCompiler(KeyedRecord):
    """Information about an installed compiler command.
    
    There are relatively few well known compilers, but a potentially infinite
    number of commands that can invoke those compilers.  This class links a
    command (e.g. icc, gcc-4.2, etc.) with a common compiler command.
    
    Attributes:
        absolute_path: Absolute path to the compiler command
        command: Command that invokes the compiler, without path, as a string
        path: Absolute path to folder containing the compiler command
        info: Optional CompilerInfo object describing the compiler invoked by the compiler command, detected if None
    """
    
    KEY = 'absolute_path'
    
    def __new__(cls, key):
        """Probes the system to find an installed compiler.
        
        May check PATH, file permissions, or other conditions in the system
        to determine if a compiler command is present and executable.
        
        Args:
            key: Command string or CompilerInfo to match.
        
        Raises:
            ConfigurationError: compiler is not installed.
        """
        command = key if isinstance(key, basestring) else key.command
        if os.path.isabs(command):
            try:
                return cls._INSTANCES[command]
            except (KeyError, AttributeError):
                pass
        absolute_path = util.which(command)
        if not absolute_path:
            raise ConfigurationError("'%s' missing or not executable." % command,
                                     "Check spelling, loaded modules, PATH environment variable, and file permissions")
        try:
            return cls._INSTANCES[absolute_path]
        except (KeyError, AttributeError):
            try:
                info = CompilerInfo.find(command)
            except KeyError:
                raise ConfigurationError("Cannot recognize compiler command '%s'" % command)
            instance = KeyedRecord.__new__(cls, absolute_path)
            instance._md5sum = None
            instance.absolute_path = absolute_path
            instance.command = os.path.basename(absolute_path)
            instance.path = os.path.dirname(absolute_path)
            instance.info = info
            return instance
    
    @classmethod
    def find(cls, key):
        """Probes the system to find an installed compiler.
        
        May check PATH, file permissions, or other conditions in the system
        to determine if a compiler command is present and executable.
        
        Args:
            key: Command string or CompilerInfo to match.
        
        Raises:
            ConfigurationError: compiler is not installed.
        """
        command = key if isinstance(key, basestring) else key.command
        if os.path.isabs(command):
            try:
                return cls._INSTANCES[command]
            except (KeyError, AttributeError):
                pass
        abspath = util.which(command)
        if not abspath:
            raise ConfigurationError("'%s' missing or not executable." % command,
                                     "Check spelling, loaded modules, PATH environment variable, and file permissions")
        try:
            return cls._INSTANCES[abspath]
        except (KeyError, AttributeError):
            try:
                info = CompilerInfo.find(command)
            except KeyError:
                raise ConfigurationError("Cannot recognize compiler command '%s'" % command)
            return cls(abspath, info)
        
    def md5sum(self):
        if not self._md5sum:
            LOGGER.debug("Calculating MD5 of '%s'" % self.absolute_path)
            md5sum = hashlib.md5()
            with open(self.absolute_path, 'r') as compiler_file:
                md5sum.update(compiler_file.read())
            self._md5sum = md5sum.hexdigest()
        return self._md5sum



class InstalledCompilerSet(KeyedRecord):
    """A collection of installed compilers, one per role if the role can be filled.
    
    Attributes:
        uid: A unique identifier for this particular combination of compilers.
    """
    
    KEY = 'uid'
    
    def __init__(self, uid, **kwargs):
        self.uid = uid
        self.members = {}
        all_roles = CompilerRole.keys()
        for key, val in kwargs.iteritems():
            if key not in all_roles:
                raise InternalError("Invalid role: %s" % key)
            self.members[key] = val

    def __getitem__(self, role):
        return self.members[role.keyword]
        
        

class CompilerInstallation(KeyedRecord):
    """
    Encapsulates data on a compiler installation.
    
    Attributes:
        family: CompilerFamily for this installation.
        commands: (command, InstalledCompiler) dictionary listing all installed compiler commands. 
    """
    
    KEY = 'family'
    
    def __new__(cls, family):
        try:
            return cls._INSTANCES[family]
        except (KeyError, AttributeError):
            pass
        instance = KeyedRecord.__new__(cls, family)
        instance.family = family
        instance.commands = {}
        LOGGER.debug("Detecting %s compiler installation" % family.name)
        for info in family:
            try:
                comp = InstalledCompiler(info)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                instance.commands[comp.info.command] = comp
                LOGGER.debug("%s %s compiler is %s" % (family.name, comp.info.role.language, comp.absolute_path))
        return instance

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
        for info in self.family.members_by_role(role):
            try:
                return self.commands[info.command]
            except KeyError:
                continue
        raise KeyError
        
