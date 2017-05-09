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

Functions used for unit tests of create.py.
"""

from taucmdr import tests
from taucmdr.cf.platforms import HOST_ARCH
from taucmdr.cf.compiler.host import CC
from taucmdr.cli.commands.trial.create import COMMAND as create_cmd

class CreateTest(tests.TestCase):
    """Tests for :any:`trial.create`."""

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_create(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, ['./a.out'])
        self.assertIn('BEGIN', stdout)
        self.assertIn('END Experiment', stdout)
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertFalse(stderr)
        
    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_create_with_description(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        args = ['--description', 'Created by test_create_with_description', '--', './a.out']
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, args)
        self.assertIn('BEGIN', stdout)
        self.assertIn('END Experiment', stdout)
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertFalse(stderr)
        
    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
