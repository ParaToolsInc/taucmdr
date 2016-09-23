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
#pylint: disable=missing-docstring

import os
import unittest
from tau import tests, util
from tau.cf.compiler.host import CC, CXX, FC
from tau.cli.commands.target.create import COMMAND as create_cmd

class CreateTest(tests.TestCase):
    """Tests for :any:`target.create`."""

    def test_create(self):
        self.reset_project_storage(project_name='proj1')
        argv = ['targ02']
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, argv)
        self.assertIn('Added target \'targ02\' to project configuration \'proj1\'', stdout)
        self.assertFalse(stderr)

    def test_no_args(self):
        self.reset_project_storage(project_name='proj1')
        _, _, stderr = self.exec_command(create_cmd, [])
        self.assertIn('error: too few arguments', stderr)

    def test_h_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['-h'])
        self.assertIn('Create target configurations.', stdout)
        self.assertIn('show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['--help'])
        self.assertIn('Create target configurations.', stdout)
        self.assertIn('show this help message and exit', stdout)

    def test_duplicatename(self):
        self.reset_project_storage(project_name='proj1')
        _, _, stderr = self.exec_command(create_cmd, ['targ1'])
        self.assertIn('target create <target_name> [arguments]', stderr)
        self.assertIn('target create: error: A target with name', stderr)
        self.assertIn('already exists', stderr)

    @unittest.skipUnless(util.which('icc'), "Intel compilers required for this test")
    def test_host_family_intel(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, ['test_targ', '--compilers', 'Intel'])
        self.assertIn("Added target", stdout)
        self.assertIn("test_targ", stdout)
        self.assertFalse(stderr)

        from tau.cf.storage.levels import PROJECT_STORAGE
        from tau.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        test_targ = ctrl.one({'name': 'test_targ'})
        for role, expected in (CC, 'icc'), (CXX, 'icpc'), (FC, 'ifort'):
            path = test_targ.populate(role.keyword)['path']
            self.assertEqual(os.path.basename(path), expected, 
                             "Target[%s] is '%s', not '%s'" % (role, path, expected))


    @unittest.skipUnless(util.which('pgcc'), "PGI compilers required for this test")
    def test_host_family_pgi(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, ['test_targ', '--compilers', 'PGI'])
        self.assertIn("Added target", stdout)
        self.assertIn("test_targ", stdout)
        self.assertFalse(stderr)

        from tau.cf.storage.levels import PROJECT_STORAGE
        from tau.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        test_targ = ctrl.one({'name': 'test_targ'})
        path = test_targ.populate(CC.keyword)['path']
        self.assertEqual('pgcc', os.path.basename(path), "Target[CC] is '%s', not 'pgcc'" % path)

