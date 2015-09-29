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
"""Target data model controller."""


from tau.error import InternalError, ConfigurationError
from tau.core.mvc import Controller, with_key_attribute
from tau.cf.compiler import CompilerRole
from tau.cf.compiler.installed import InstalledCompilerSet


class Target(Controller, with_key_attribute('name')):
    """Target data controller."""

    def on_create(self):
        super(Target, self).on_create()
        if not self['tau_source']:
            raise ConfigurationError("A TAU installation or source code must be provided.")

    def compilers(self):
        """Get information about the compilers used by this target configuration.
         
        Returns:
            InstalledCompilerSet: Collection of installed compilers used by this target.
        """
        eids = []
        compilers = {}
        for role in CompilerRole.all():
            try:
                compiler_command = self.populate(role.keyword)
            except KeyError:
                continue
            compilers[role.keyword] = compiler_command.info()
            eids.append(compiler_command.eid)
        missing = [role.keyword for role in CompilerRole.tau_required() if role.keyword not in compilers]
        if missing:
            raise InternalError("Target '%s' is missing required compilers: %s" % (self['name'], missing))
        return InstalledCompilerSet('_'.join([str(x) for x in eids]), **compilers)

