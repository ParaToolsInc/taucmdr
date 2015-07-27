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

import os
from tau import logger
from tau.error import ConfigurationError
from tau.controller import Controller
from tau.cf.compiler import CompilerInfo

LOGGER = logger.getLogger(__name__)


class Compiler(Controller):

    """
    Compiler data model controller
    """

    attributes = {
        'command': {
            'type': 'string',
            'required': True,
            'description': "The compiler command without path"
        },
        'path': {
            'type': 'string',
            'required': True,
            'description': "Absolute path to the compiler command"
        },
        'md5': {
            'type': 'string',
            'required': True,
            'description': "Checksum of the compiler command file"
        },
        'version': {
            'type': 'string',
            'required': True,
            'description': "Version string as reported by compiler command"
        },
        'role': {
            'type': 'string',
            'required': True,
            'description': "Role identifier"
        },
        'family': {
            'type': 'string',
            'required': True,
            'description': "Family name"
        },
        'language': {
            'type': 'string',
            'required': True,
            'description': "Primary language this compiler understands"
        },
        'tau_wrapper': {
            'type': 'string',
            'required': True,
            'description': "Corresponding TAU compiler wrapper script"
        }
    }

    def __str__(self):
        return self['command']

    def absolute_path(self):
        return os.path.join(self['path'], self['command'])
    
    def info(self):
        return CompilerInfo(self['command'], self['role'], 
                            self['family'], 
                            self['language'], self['path'], self['md5'],
                            self['version'])


    @classmethod
    def identify(cls, compiler_cmd):
        """Identifies a compiler command.
        
        Checks the database of known compilers against the command found.
        If there is no existing record for the compiler, update the database.
        Otherwise, reuse the existing record.
               
        Args:
            compiler_cmd: The compiler command to identify, e.g. 'gcc'
            
        Returns:
            A Compiler instance. 
            
        Raises:
            ConfigurationError: compiler_cmd was invalid.
        """
        info = CompilerInfo.identify(compiler_cmd)
        fields = {'command': info.command,
                  'path': info.path,
                  'md5': info.md5sum,
                  'version': info.version,
                  'role': info.role,
                  'family': info.family,
                  'language': info.language,
                  'tau_wrapper': info.tau_wrapper}
        found = cls.one(keys=fields)
        if found:
            LOGGER.debug("Found compiler record: %s" % found)
        else:
            LOGGER.debug("No compiler record found. Creating new record: %s" % fields)
            found = cls.create(fields)
        return found

    @classmethod
    def getSiblings(cls, compiler):
        """
        TODO: Docs
        """
        LOGGER.debug("Getting compilers for '%s'" % compiler)

        compilers = {compiler['role']: compiler}
        for known in KNOWN_COMPILERS.itervalues():
            LOGGER.debug("Checking %s" % known)
            if (known.family == compiler['family']) and (known.role != compiler['role']):
                try:
                    other = cls.identify(known.command)
                except ConfigurationError, e:
                    LOGGER.debug(e)
                    continue
                if os.path.dirname(other['path']) == os.path.dirname(compiler['path']):
                    LOGGER.debug("Found %s compiler '%s' matching '%s'" % (
                        other['role'], other['command'], compiler['command']))
                    compilers[other['role']] = other

        try:
            cc = compilers['CC']
        except KeyError:
            raise ConfigurationError(
                "Cannot find C compiler for %s" % compiler)
        try:
            cxx = compilers['CXX']
        except KeyError:
            raise ConfigurationError(
                "Cannot find C++ compiler for %s" % compiler)
        try:
            fc = compilers['FC']
        except KeyError:
            raise ConfigurationError(
                "Cannot find Fortran compiler for %s" % compiler)

        return cc, cxx, fc
