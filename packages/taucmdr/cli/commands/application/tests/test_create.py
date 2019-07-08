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
from taucmdr.cli.commands.application.create import COMMAND as create_cmd
from taucmdr.model.application import Application
from taucmdr.cf.storage.levels import PROJECT_STORAGE

class CreateTest(tests.TestCase):
    """Tests for :any:`application.create`."""

    def test_create(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, ['test01'])
        self.assertIn('Added application \'test01\' to project configuration', stdout)
        self.assertFalse(stderr)
        
    def test_python(self):
        self.reset_project_storage()
        name = 'python_app'
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, [name,'--python'])
        app = Application.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(app, Application)
        self.assertEqual(app['python'], True)
        self.assertFalse(stderr)

    def test_duplicatename(self):
        self.reset_project_storage()
        _, stderr = self.assertNotCommandReturnValue(0, create_cmd, ['app1'])
        self.assertIn('application create <application_name> [arguments]', stderr)
        self.assertIn('application create: error: A application with name', stderr)
        self.assertIn('already exists', stderr)
        
    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
