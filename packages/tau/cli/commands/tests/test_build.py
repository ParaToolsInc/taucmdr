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

Functions used for unit tests of build.py.
"""


import shutil
from tau import tests, TAU_HOME
from tau.cli.commands.build import COMMAND as build_command
from tau.cf.compiler.host import CC

class BuildTest(tests.TestCase):

    def test_build(self):
        self.reset_project_storage()
        shutil.copyfile(TAU_HOME+'/.testfiles/hello.c', tests.get_test_workdir()+'/hello.c')
        cc_cmd = self.get_compiler(CC)
        argv = [cc_cmd, 'hello.c']
        self.assertCommandReturnValue(0, build_command, argv)

    def test_abspath_compat(self):
        self.reset_project_storage()
        cc_cmd = self.get_compiler(CC)
        self.assertTrue(build_command.is_compatible(cc_cmd))

    def test_h_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, build_command, ['-h'])
        self.assertIn('Create target configurations.', stdout)
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, build_command, ['--help'])
        self.assertIn('Create target configurations.', stdout)
        self.assertIn('Show this help message and exit', stdout)
