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

from __future__ import absolute_import
import os
from taucmdr import logger
from taucmdr.error import InternalError, ConfigurationError
from taucmdr.mvc.model import Model
from taucmdr.mvc.controller import Controller
from taucmdr.cf.compiler import Knowledgebase, InstalledCompiler

LOGGER = logger.get_logger(__name__)


def attributes():
    return {
        'uid': {
            'type': 'string',
            'required': True,
            'description': "compiler unique identifier"
        },
        'path': {
            'type': 'string',
            'required': True,
            'description': "absolute path to the compiler command"
        },
        'family': {
            'type': 'string',
            'required': True,
            'description': "compiler's family name"
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

    def _compiler_info(self):
        command = os.path.basename(self['path'])
        role = Knowledgebase.find_role(self['role'])
        family = role.kbase.families[self['family']]
        info_list = Knowledgebase.find_compiler(command, family, role)
        if len(info_list) != 1:
            raise InternalError("Zero or more than one known compilers match '%s'" % self)
        return info_list[0]

    def _verify_core_attrs(self, comp, msg_parts):
        fatal = False
        if comp.absolute_path != self['path']:
            msg_parts.append("Compiler moved from '%s' to '%s'." % (self['path'], comp.absolute_path))
        if comp.info.family.name != self['family']:
            fatal = True
            msg_parts.append("It was a %s compiler but now it's a %s compiler." %
                             (self['family'], comp.info.family.name))
        if comp.info.role.keyword != self['role']:
            msg_parts.append("It was a %s compiler but now it's a %s compiler." %
                             (self['role'], comp.info.role.keyword))
        return fatal

    def verify(self):
        """Checks that the system state matches the recorded compiler information.

        May execute the compiler or other commands, check filesystem paths, and check environment variables
        to determine if this compiler record is still valid.  This operation may be expensive.

        Returns:
            InstalledCompiler: Information on the compiler installation matching this record.

        Raises:
            ConfigurationError: This compiler record is no longer valid.
        """
        comp = InstalledCompiler(self['path'], self._compiler_info())
        if comp.uid == self['uid']:
            return comp
        msg_parts = ["%s '%s' has changed:" % (comp.info.short_descr, comp.absolute_path)]
        fatal = self._verify_core_attrs(comp, msg_parts)
        if not fatal:
            self_wrapped = self.get('wrapped', False)
            if comp.wrapped and not self_wrapped:
                fatal = True
                msg_parts.append("It has changed to a compiler wrapper.")
            elif not comp.wrapped and self_wrapped:
                fatal = True
                msg_parts.append("It has changed from a compiler wrapper to a regular compiler.")
            elif comp.wrapped and self_wrapped:
                new_wrapped = comp.wrapped.unwrap()
                old_wrapped = self.populate('wrapped')
                while 'wrapped' in old_wrapped:
                    old_wrapped = self.populate('wrapped')
                # old_wrapped is a Compiler instance so this isn't really a protected access violation
                # pylint: disable=protected-access
                fatal = fatal or old_wrapped._verify_core_attrs(new_wrapped, msg_parts)
                if not fatal:
                    if sorted(comp.include_path) != sorted(self['include_path']):
                        msg_parts.append("Include path has changed.")
                    if sorted(comp.library_path) != sorted(self['library_path']):
                        msg_parts.append('Library path has changed.')
                    if sorted(comp.compiler_flags) != sorted(self['compiler_flags']):
                        msg_parts.append('Compiler flags have changed.')
                    if sorted(comp.libraries) != sorted(self['libraries']):
                        msg_parts.append('Linked libraries have changed.')
        msg = "\n  ".join(msg_parts)
        if fatal:
            raise ConfigurationError(msg,
                                     "Check loaded environment modules",
                                     "Check environment variables, especially PATH",
                                     "Contact your system administrator")
        else:
            LOGGER.warning(msg + ("\n\nCheck loaded environment modules and environment variables.\n"
                                  "Attempting to continue.  Compilation may fail later on."))
        return comp

    def installation(self):
        """Gets information about this compiler installation.

        Returns:
            InstalledCompiler: Information about the installed compiler command.
        """
        info = self._compiler_info()
        try:
            wrapped = self.populate('wrapped')
        except KeyError:
            comp = InstalledCompiler(self['path'], info, uid=self['uid'])
        else:
            comp = InstalledCompiler(self['path'], info, uid=self['uid'],
                                     wrapped=wrapped.installation(),
                                     include_path=self.get('include_path'),
                                     library_path=self.get('library_path'),
                                     compiler_flags=self.get('compiler_flags'),
                                     libraries=self.get('libraries'))
        return comp
