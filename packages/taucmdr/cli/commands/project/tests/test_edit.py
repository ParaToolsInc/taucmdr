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
from __future__ import print_function

"""Test functions.

Functions used for unit tests of edit.py.
"""


from taucmdr import tests
from taucmdr.cli.commands.project import edit
from taucmdr.model.project import Project

class EditTest(tests.TestCase):
    """Tests for :any:`project.edit`."""

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, [])
        self.assertIn('too few arguments', stderr)
        self.assertFalse(stdout)

    def test_rename(self):
        self.reset_project_storage()
        argv = ['proj1', '--new-name', 'proj2']
        self.assertCommandReturnValue(0, edit.COMMAND, argv)
        proj_ctrl = Project.controller()
        self.assertIsNone(proj_ctrl.one({'name': 'proj1'}))
        self.assertIsNotNone(proj_ctrl.one({'name': 'proj2'}))
        self.assertCommandReturnValue(0, edit.COMMAND, ['proj2', '--new-name', 'proj1'])
    
    def test_wrongname(self):
        self.reset_project_storage()
        argv = ['proj2', '--new-name', 'proj3']
        _, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('project edit <project_name> [arguments]', stderr)
        self.assertIn('project edit: error', stderr)
        self.assertIn('is not a project name.', stderr)
        
    def test_wrongarg(self):
        self.reset_project_storage()
        argv = ['app1', '--arg', 'arg1']
        _, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('project edit <project_name> [arguments]', stderr)
        self.assertIn('project edit: error: unrecognized arguments: --arg arg1', stderr)
