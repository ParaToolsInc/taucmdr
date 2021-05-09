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
"""OMPT software installation management.

OMPT is used for performance analysis of OpenMP codes.
"""

from taucmdr import logger
from taucmdr.cf.software.installation import CMakeInstallation
from taucmdr.cf.compiler.host import CC, CXX



LOGGER = logger.get_logger(__name__)

REPOS = {None: [
    'http://tau.uoregon.edu/LLVM-openmp-8.0.tar.gz',
    'http://fs.paratools.com/tau-mirror/LLVM-openmp-8.0.tar.gz'
]}

LIBRARIES = {None: ['libomp.so']}

HEADERS = {None: ['omp.h', 'ompt.h']}


class OmptInstallation(CMakeInstallation):
    """Encapsulates an OMPT installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        if sources['ompt'] == 'download-tr6':
            sources['ompt'] = [
                'http://tau.uoregon.edu/LLVM-openmp-ompt-tr6.tar.gz',
                'http://fs.paratools.com/tau-mirror/LLVM-openmp-ompt-tr6.tar.gz'
            ]
        elif sources['ompt'] == 'download-tr4':
            sources['ompt'] = [
                'http://tau.uoregon.edu/LLVM-openmp-0.2.tar.gz',
                'https://fs.paratools.com/tau-mirror/LLVM-openmp-0.2.tar.gz'
            ]
        super().__init__('ompt', 'ompt', sources, target_arch, target_os,
                                               compilers, REPOS, None, LIBRARIES, HEADERS)

    def cmake(self, flags):
        flags.extend(['-DCMAKE_C_COMPILER=' + self.compilers[CC].unwrap().absolute_path,
                      '-DCMAKE_CXX_COMPILER=' + self.compilers[CXX].unwrap().absolute_path,
                      '-DCMAKE_C_FLAGS=-fPIC',
                      '-DCMAKE_CXX_FLAGS=-fPIC',
                      '-DCMAKE_BUILD_TYPE=Release',
                      '-DCMAKE_DISABLE_FIND_PACKAGE_CUDA:BOOL=TRUE'])
        return super().cmake(flags)

    def make(self, flags):
        super().make(flags + ['libomp-needed-headers'])
        return super().make(flags)
