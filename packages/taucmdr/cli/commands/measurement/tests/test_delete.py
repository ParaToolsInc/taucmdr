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

Functions used for unit tests of delete.py.
"""


from __future__ import absolute_import
from taucmdr import tests
from taucmdr.cli.commands.measurement import delete, create
from taucmdr.cli.commands import select

class DeleteTest(tests.TestCase):
    """Tests for :any:`measurement.delete`."""

    def test_delete(self):
        self.reset_project_storage()
        argv = ['test_meas01']
        self.assertCommandReturnValue(0, create.COMMAND, argv)
        stdout, stderr = self.assertCommandReturnValue(0, delete.COMMAND, argv)
        self.assertIn("Deleted measurement 'test_meas01'", stdout)
        self.assertFalse(stderr)

    def test_wrongname(self):
        self.reset_project_storage()
        _, stderr = self.assertNotCommandReturnValue(0, delete.COMMAND, ['invalid_name'])
        self.assertIn('measurement delete <measurement_name> [arguments]', stderr)
        self.assertIn('measurement delete: error: No project-level measurement with name', stderr)

    def test_issue187(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/187"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create.COMMAND,
                                                       ['profile2', '--profile', 'tau', '--trace', 'none',
                                                        '--source-inst', 'automatic', '--sample', 'false'])
        self.assertIn("Added measurement 'profile2' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select.COMMAND, ['profile2'])
        self.assertIn("Created a new experiment 'targ1-app1-profile2'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, delete.COMMAND, ['profile2'])
        self.assertIn("Deleted measurement 'profile2'", stdout)
        self.assertFalse(stderr)
