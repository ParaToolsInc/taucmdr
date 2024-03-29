#
# Copyright (c) 2020, ParaTools, Inc.
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
"""libdwarf software installation management.

The Dwarf library provides an interface to resolve samples by converting program
    counter addresses to function names for applications with a large number of symbols.
"""

import os
from taucmdr.cf.software.installation import AutotoolsInstallation

REPOS = {None: ['http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/libdwarf-20200825.tar.gz',
                'https://www.prevanders.net/libdwarf-20200825.tar.gz']}

LIBRARIES = {None: ['libdwarf.la', 'libdwarf.a']}

HEADERS = {None: ['dwarf.h', 'libdwarf.h']}


class LibdwarfInstallation(AutotoolsInstallation):
    """Encapsulates a libdwarf installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        super().__init__('libdwarf', 'libdwarf', sources,
                                                   target_arch, target_os, compilers, REPOS, None, LIBRARIES, HEADERS)

        self.add_dependency('libelf', sources)

    def configure(self, flags):
        flags.extend(['--with-pic'])

        libelf = self.dependencies.get('libelf')
        os.environ['LDFLAGS'] = '-L%s' % libelf.lib_path
        os.environ['CPPFLAGS'] = '-I%s' % libelf.include_path

        return super().configure(flags)
