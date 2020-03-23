# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, ParaTools, Inc.
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
"""Test functions.

Functions used for unit tests of show.py.
"""


from __future__ import absolute_import
from taucmdr import tests
from taucmdr.cf.platforms import HOST_ARCH
from taucmdr.cli.commands.trial import show, create
from taucmdr.cf.compiler.host import CC

class ShowTest(tests.TestCase):

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_show(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, create.COMMAND, ['./a.out'])
        argv = ['0', '--profile-tool', 'pprof']
        self.assertCommandReturnValue(None, show.COMMAND, argv)

    def test_multiple_trials(self):
        """Issue #240"""
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, create.COMMAND, ['./a.out'])
        self.assertCommandReturnValue(0, create.COMMAND, ['./a.out'])
        self.assertCommandReturnValue(0, create.COMMAND, ['./a.out'])
        argv = ['0', '2', '--profile-tool', 'pprof']
        stdout, stderr = self.assertCommandReturnValue(None, show.COMMAND, argv)
        self.assertFalse(stderr)
        self.assertIn('Current trial/metric directory: 0', stdout)
        self.assertIn('Current trial/metric directory: 2', stdout)
        self.assertNotIn('Current trial/metric directory: 1', stdout)
