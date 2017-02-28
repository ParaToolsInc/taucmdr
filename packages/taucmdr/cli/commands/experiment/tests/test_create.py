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

import unittest
from taucmdr import tests, util
from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.target.create import COMMAND as target_create_cmd

class CreateTest(tests.TestCase):
    
    @unittest.skipUnless(util.which('pgcc'), "PGI compilers required for this test")
    def test_pgi(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, target_create_cmd, ['test_targ', '--compilers', 'PGI'])
        self.assertIn('Added target \'test_targ\' to project configuration', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, measurement_create_cmd, ['meas_PGI'])
        self.assertIn('Added measurement \'meas_PGI\' to project configuration', stdout)
        self.assertFalse(stderr)
        argv = ['test_targ', 'meas_PGI']
        _, stderr = self.assertCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertFalse(stderr)
        
    def test_h_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, experiment_create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage(project_name='proj1')
        stdout, _ = self.assertCommandReturnValue(0, experiment_create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)
