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

from tau.error import InternalError
from role import REQUIRED_ROLES, KNOWN_ROLES


class CompilerSet(object):
    """A collection of Compiler objects, one per required role.
    
    Attributes:
        uid: Unique identifier (hopefully) for this combination of compilers.
        CC: Compiler in the 'CC' role
        CXX: Compiler in the 'CXX' role
        etc.
    """
    # pylint: disable=too-few-public-methods
    
    def __init__(self, uid, **kwargs):
        self.uid = uid
        missing_roles = set([role.keyword for role in REQUIRED_ROLES])
        for key, comp in kwargs.iteritems():
            if key not in KNOWN_ROLES:
                raise InternalError("Invalid role: %s" % role)
            setattr(self, key, comp)
            missing_roles.remove(key)
        for role in missing_roles:
            raise InternalError("Required role %s not defined" % role)
        
    def iter(self):
        for keyword in KNOWN_ROLES:
            try:
                yield getattr(self, keyword)
            except AttributeError:
                continue

    def __iter__(self):
        return self.iter()

    def __contains__(self, role):
        try:
            keyword = role.keyword
        except AttributeError as err:
            raise InternalError("%s is not a CompilerRole: %s" % (role, err))
        else:
            return hasattr(self, keyword)