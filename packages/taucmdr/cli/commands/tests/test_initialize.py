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

Functions used for unit tests of initialize.py.
"""

from __future__ import absolute_import
import os
from taucmdr import tests
from taucmdr.cli.commands.initialize import COMMAND as initialize_cmd


class InitializeTest(tests.TestCase):
    """Unit tests for `taucmdr initialize`"""

    def test_bare(self):
        self.destroy_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, initialize_cmd, ['--bare'])
        self.assertIn('Created a new project named', stdout)
        self.assertIn('Project Configuration', stdout)
        self.assertIn('No targets', stdout)
        self.assertIn('No applications', stdout)
        self.assertIn('No measurements', stdout)
        self.assertIn('No experiments', stdout)
        self.assertFalse(stderr)

    def test_initialize(self):
        self.destroy_project_storage()
        self.assertCommandReturnValue(0, initialize_cmd, [])

    def test_init_below_project(self):
        self.reset_project_storage()
        subdir = "foo"
        os.mkdir(subdir)
        os.chdir(subdir)
        self.assertNotCommandReturnValue(0, initialize_cmd, [])

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, initialize_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, initialize_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
