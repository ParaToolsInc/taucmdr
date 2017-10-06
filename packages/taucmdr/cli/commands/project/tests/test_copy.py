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
from taucmdr.cli.commands.project.copy import COMMAND as PROJECT_COPY_COMMAND

class CopyTest(tests.TestCase):
    """Tests for :any:`project.copy`."""

    def test_copy(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, PROJECT_COPY_COMMAND, 
                                                       ['proj1', 'proj2', 
                                                        '--application', 'app1', 
                                                        '--measurements profile',
                                                        ' --targets east03'])
        self.assertIn('Created a new project named \'proj2\'', stdout)
        self.assertFalse(stderr)

    def test_duplicatename(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, PROJECT_COPY_COMMAND, ['proj1', 'proj2'])
        self.assertIn('Created a new project named \'proj2\'', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertNotCommandReturnValue(0, PROJECT_COPY_COMMAND, ['proj1', 'proj2'])
        self.assertIn("project copy: error: A project named 'proj2' already exists", stderr)
        self.assertFalse(stdout)

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, PROJECT_COPY_COMMAND, ['-h'])
        self.assertIn('Show this help message and exit', stdout)
        self.assertFalse(stderr)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, PROJECT_COPY_COMMAND, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
        self.assertFalse(stderr)
