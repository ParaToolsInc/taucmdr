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
"""SQLite3 software installation management.

SQLite3 is a single-file relational database. It can be optionally used by TAU
to store profile data in such a database.
"""

from taucmdr.cf.software.installation import AutotoolsInstallation


REPOS = {None: 'http://www.cs.uoregon.edu/research/paracomp/tau/tauprofile/dist/sos/sqlite-autoconf-3210000.tar.gz'}

LIBRARIES = {None: ['libsqlite3.a', 'libsqlite3.la', 'libsqlite3.so']}

HEADERS = {None: ['sqlite3.h', 'sqlite3ext.h']}

COMMANDS = {None: ['sqlite3']}


class Sqlite3Installation(AutotoolsInstallation):
    """Encapsulates a SQLite3 installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        super().__init__('sqlite3', 'SQLite3', sources,
                         target_arch, target_os, compilers, REPOS, COMMANDS, LIBRARIES, HEADERS)
