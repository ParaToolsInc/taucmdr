#
# Copyright (c) 2016-2026, ParaTools, Inc.
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
"""Unit tests for :any:`taucmdr.model.compiler`."""

from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.compiler import Compiler


class CompilerTest(tests.TestCase):
    """Tests for :any:`taucmdr.model.compiler.Compiler`."""

    def test_unknown_family(self):
        """A compiler record from a family this version doesn't know gives a clear error."""
        self.reset_project_storage(['--bare'])
        comp = Compiler.controller(PROJECT_STORAGE).create({'uid': 'stale-record',
                                                            'path': '/opt/old/bin/oldcc',
                                                            'family': 'NoSuchFamily',
                                                            'role': CC.keyword})
        with self.assertRaisesRegex(ConfigurationError, 'NoSuchFamily'):
            comp.installation()
