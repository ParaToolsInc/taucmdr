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
"""Compiler data model.

TAU only works reliablly when the same compiler is used to build both the application
source code and TAU itself.  If the system compiler changes TAU can break entirely.
This data tracks the system compilers so we can warn the user if they have changed.
"""

import os
from tau import logger
from tau.error import InternalError
from tau.mvc.model import Model
from tau.mvc.controller import Controller
from tau.cf.compiler import CompilerFamily, CompilerRole, CompilerInfo
from tau.cf.compiler.mpi import MpiCompilerFamily
from tau.cf.compiler.installed import InstalledCompiler

LOGGER = logger.get_logger(__name__)


def attributes():
    return {
        'uid': {
            'type': 'string',
            'required': True,
            'description': "unique identifier of the compiler command"
        },
        'path': {
            'type': 'string',
            'required': True,
            'description': "absolute path to the compiler command"
        },
        'family': {
            'type': 'string',
            'required': True,
            'description': "compiler's family"
        },
        'role': {
            'type': 'string',
            'required': True,
            'description': "role this command plays in the compiler family, e.g. CXX or MPI_CC"
        },
        'wrapped': {
            'model': Compiler,
            'required': False,
            'description': "compiler wrapped by this compiler"
        },
        'include_path': {
            'type': 'array',
            'required': False,
            'description': "extra paths to search for include files when compiling with this compiler"
        },
        'library_path': {
            'type': 'array',
            'required': False,
            'description': "extra paths to search for libraries when compiling with this compiler"
        },
        'compiler_flags': {
            'type': 'array',
            'required': False,
            'description': "extra flags to use when compiling with this compiler"
        },
        'libraries': {
            'type': 'array',
            'required': False,
            'description': "extra libraries to link when compiling with this compiler"
        }
    }


class CompilerController(Controller):
    """Compiler data controller."""
    
    def register(self, comp):
        """Records information about an installed compiler command in the database.
        
        If the compiler has already been registered then do not update the database.
        
        Args:
            comp (InstalledCompiler): Information about an installed compiler.
            
        Returns:
            Compiler: Data controller for the installed compiler's data.
        """
        found = self.one({'uid': comp.uid})
        if not found:
            LOGGER.debug("Registering compiler '%s' (%s)", comp.absolute_path, comp.info.short_descr)
            data = {'path': comp.absolute_path, 
                    'family': comp.info.family.name, 
                    'role': comp.info.role.keyword}
            for attr in 'include_path', 'library_path', 'compiler_flags', 'libraries':
                value = getattr(comp, attr)
                if value:
                    data[attr] = value 
            if comp.wrapped:
                data['wrapped'] = self.register(comp.wrapped).eid
            found = self.one(data)
            if not found:
                data['uid'] = comp.uid
                found = self.create(data)
            elif found['uid'] != comp.uid:
                LOGGER.warning("%s '%s' has changed!"
                               " The unique ID was %s when the TAU project was created, but now it's %s."
                               " TAU will attempt to continue but may fail later on.", 
                               comp.info.short_descr, comp.absolute_path, found['uid'], comp.uid)
        return found


class Compiler(Model):
    """Compiler data model."""
    
    __attributes__ = attributes

    __controller__ = CompilerController
    
    def installation_info(self, probe=False):
        """Gets information about this compiler installation.
        
        Args:
            probe (bool): If True then probe the system to confirm that the installed compiler matches the
                          data recorded in the database.  If False then use the recorded data without verification.
        
        Returns:
            InstalledCompiler: Information about the installed compiler command.
        """
        command = os.path.basename(self['path'])
        role = CompilerRole.find(self['role'])
        if role.keyword.startswith('MPI_'):
            family = MpiCompilerFamily.find(self['family'])
        else:
            family = CompilerFamily.find(self['family'])
        info_list = CompilerInfo.find(command, family, role)
        if len(info_list) != 1:
            raise InternalError("Zero or more than one CompilerInfo objects match '%s'" % self)
        if probe:
            comp = InstalledCompiler(self['path'], info_list[0])
            if comp.uid != self['uid']:
                LOGGER.warning("%s '%s' has changed!"
                               " The unique ID was %s when the TAU project was created, but now it's %s."
                               " TAU will attempt to continue but may fail later on.", 
                               comp.info.short_descr, comp.absolute_path, self['uid'], comp.uid)
        else:
            LOGGER.debug("NOT verifying compiler information for '%s'", self['path'])
            try:
                wrapped = self.populate('wrapped')
            except KeyError:
                comp = InstalledCompiler(self['path'], info_list[0], uid=self['uid'])
            else:
                comp = InstalledCompiler(self['path'], info_list[0], 
                                         wrapped=wrapped.installation_info(probe), 
                                         include_path=self['include_path'], 
                                         library_path=self['library_path'], 
                                         compiler_flags=self['compiler_flags'], 
                                         libraries=self['libraries'],
                                         uid=self['uid'])
        return comp
