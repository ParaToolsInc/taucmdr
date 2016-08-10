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

Functions used for unit tests of select.py.
"""


import unittest
from tau import tests, util
from tau.cli.commands import select
from tau.cli.commands.measurement import create
from tau.cli.commands.target import create as create_target

class SelectTest(tests.TestCase):
    
    def test_select(self):
        self.reset_project_storage(app_name='testing_app')
        argv = ['testing_app', 'profile']
        self.assertCommandReturnValue(0, select.COMMAND, argv)

    @unittest.skipUnless(util.which('pgcc'), "PGI compilers required for this test")
    def test_pgi(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create_target.COMMAND, ['test_targ', '--compilers', 'PGI'])
        _, _, stderr = self.exec_command(create.COMMAND, ['meas_PGI'])
        argv = ['proj1', 'test_targ', 'meas_PGI']
        self.assertCommandReturnValue(0, select.COMMAND, argv)
        self.assertIn('Added measurement \'meas_PGI\' to project configuration', stdout)
        self.assertFalse(stderr)
