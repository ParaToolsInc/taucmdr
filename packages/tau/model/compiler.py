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

from tau import logger
from tau.model import Controller


LOGGER = logger.get_logger(__name__)
 
 
class Compiler(Controller):
    """Compiler data controller."""

    def info(self):
        """Probes the system for information on this compiler command.
        
        Returns:
            InstalledCompiler: Information about the installed compiler command.
        """
        from tau.cf.compiler.installed import InstalledCompiler
        comp = InstalledCompiler(self['path'])
        if comp.md5sum() != self['md5']:
            LOGGER.warning("%s '%s' has changed!", comp.info.short_descr, comp.command)
        return comp

    @classmethod
    def register(cls, comp):
        """Records information about a compiler command in the database.
        
        If the given compiler has already been registered then do not update the database.
        
        Args:
            comp (InstalledCompiler): Information about the installed compiler command.
            
        Returns:
            Compiler: Data controller for the installed compiler's data.
        """
        path = comp.absolute_path
        md5sum = comp.md5sum()
        found = cls.one(keys={'path': path})
        if not found:
            found = cls.create(fields={'path': path, 'md5': md5sum})
        else:
            if md5sum != found['md5']:
                LOGGER.warning("%s '%s' has changed!  MD5 sum was %s, but now it's %s", 
                               comp.info.short_descr, comp.command, found['md5'], md5sum)
        return found


Compiler.attributes = {
    'path': {
        'type': 'string',
        'required': True,
        'unique': True,
        'description': "absolute path to the compiler command"
    },
    'md5': {
        'type': 'string',
        'required': True,
        'description': "checksum of the compiler command file"
    }
}

