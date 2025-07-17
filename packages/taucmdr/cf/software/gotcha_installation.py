#
# Copyright (c) 2025, ParaTools, Inc.
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
"""GOTCHA software installation management.

GOTCHA is required for Score-P 9.0 and later.
"""

from taucmdr import logger
from taucmdr.cf.software.installation import CMakeInstallation
from taucmdr.cf.compiler.host import CC, CXX



LOGGER = logger.get_logger(__name__)

REPOS = {None: [
    'https://fs.paratools.com/tau-mirror/GOTCHA-1.0.8.tar.gz'
]}

LIBRARIES = {None: ['libgotcha.so']}

HEADERS = {None: ['gotcha/gotcha.h']}


class GotchaInstallation(CMakeInstallation):
    """Encapsulates a GOTCHA installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        super().__init__('gotcha', 'gotcha', sources, target_arch, target_os,
                                               compilers, REPOS, None, LIBRARIES, HEADERS)

    def cmake(self, flags):
        flags.extend(['-DCMAKE_C_COMPILER=' + self.compilers[CC].unwrap().absolute_path,
                      '-DCMAKE_CXX_COMPILER=' + self.compilers[CXX].unwrap().absolute_path,
                      '-DCMAKE_BUILD_TYPE=Release'])
        return super().cmake(flags)

    def make(self, flags):
        return super().make(flags)
