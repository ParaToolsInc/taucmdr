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

from tau import logger
from tau.controller import Controller


LOGGER = logger.getLogger(__name__)
 
class Compiler(Controller):

    """
    Compiler data model controller
    """

    attributes = {
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

    def info(self):
        """Probes the system for information on this compiler command.
        
        Returns:
            CompilerInfo for this compiler command.
        """
        from tau.cf.compiler.installed import InstalledCompiler
        comp = InstalledCompiler(self['path'])
        if comp.md5sum() != self['md5']:
            LOGGER.warning("%s '%s' has changed!" % (comp.info.short_descr, comp.command))
            # TODO: What do we do when compilers change?
        return comp

    @classmethod
    def register(cls, comp):
        path = comp.absolute_path
        md5sum = comp.md5sum()
        found = cls.one(keys={'path': path})
        if not found:
            found = cls.create(fields={'path': path, 'md5': md5sum})
        else:
            if md5sum != found['md5']:
                LOGGER.warning("%s '%s' has changed!  MD5 sum was %s, but now it's %s" % 
                               (comp.info.short_descr, comp.command, found['md5'], md5sum))
                # TODO: What should we do when the compilers change?
        return found