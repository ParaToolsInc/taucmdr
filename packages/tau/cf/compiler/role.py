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


class CompilerRole(object):
    """Information about a compiler's role.
    
    Attributes:
        keyword: String identifying how the compiler is used in the build process, e.g. 'CXX'
        language: Language corresponding to the compiler role, e.g. 'C++'
        required: True if this role must be filled to compile TAU, False otherwise
    """
    def __init__(self, keyword, language, required):
        self.keyword = keyword
        self.language = language
        self.required = required

    def __eq__(self, other):
        return isinstance(other, CompilerRole) and (other.keyword == self.keyword)


CC_ROLE = CompilerRole('CC', 'C', True)
CXX_ROLE = CompilerRole('CXX', 'C++', True)
FC_ROLE = CompilerRole('FC', 'Fortran', True)
F77_ROLE = CompilerRole('F77', 'FORTRAN77', False)
F90_ROLE = CompilerRole('F90', 'Fortran90', False)
UPC_ROLE = CompilerRole('UPC', 'Universal Parallel C', False)

ALL_ROLES = [CC_ROLE, CXX_ROLE, FC_ROLE, F77_ROLE, F90_ROLE, UPC_ROLE]
REQUIRED_ROLES = [_ for _ in ALL_ROLES if _.required]
KNOWN_ROLES = dict([(_.keyword, _) for _ in ALL_ROLES])
