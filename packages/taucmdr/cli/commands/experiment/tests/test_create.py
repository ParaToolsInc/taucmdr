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

from taucmdr import tests, util
from taucmdr.cf.platforms import HOST_OS, DARWIN
from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.target.create import COMMAND as target_create_cmd
from taucmdr.cli.commands.application.create import COMMAND as application_create_cmd
from taucmdr.cli.commands.project.create import COMMAND as project_create_cmd
from taucmdr.cli.commands.project.edit import COMMAND as project_edit_cmd
from taucmdr.cli.commands.project.select import COMMAND as project_select_cmd

class CreateTest(tests.TestCase):
    
    @tests.skipUnless(util.which('pgcc'), "PGI compilers required for this test")
    def test_pgi(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, target_create_cmd, ['test_targ', '--compilers', 'PGI'])
        self.assertIn("Added target 'test_targ' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, measurement_create_cmd, ['meas_PGI'])
        self.assertIn("Added measurement 'meas_PGI' to project configuration", stdout)
        self.assertFalse(stderr)
        argv = ['exp2', '--target', 'test_targ', '--application', 'app1', '--measurement', 'meas_PGI']
        _, stderr = self.assertCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertFalse(stderr)
        
    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, experiment_create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, experiment_create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)

    def test_invalid_targ_name(self):
        self.reset_project_storage()
        argv = ['exp2', '--target', 'targ_err', '--application', 'app1', '--measurement', 'sample']
        stdout, stderr = self.assertNotCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertNotIn('CRITICAL', stdout)
        self.assertIn('error', stderr)

    def test_invalid_app_name(self):
        self.reset_project_storage()
        argv = ['exp2', '--target', 'targ1', '--application', 'app_err', '--measurement', 'sample']
        stdout, stderr = self.assertNotCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertNotIn('CRITICAL', stdout)
        self.assertIn('error', stderr)

    def test_invalid_meas_name(self):
        self.reset_project_storage()
        argv = ['exp2', '--target', 'targ1', '--application', 'app1', '--measurement', 'meas_err']
        stdout, stderr = self.assertNotCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertNotIn('CRITICAL', stdout)
        self.assertIn('error', stderr)

    def test_ompt(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, application_create_cmd, ['test_app', '--openmp', 'T'])
        self.assertIn("Added application 'test_app' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, measurement_create_cmd, ['meas_ompt', '--openmp', 'ompt'])
        self.assertIn("Added measurement 'meas_ompt' to project configuration", stdout)
        self.assertFalse(stderr)
        argv = ['exp2', '--target', 'targ1', '--application', 'test_app', '--measurement', 'meas_ompt']
        _, stderr = self.assertCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertFalse(stderr)

    @tests.skipIf(HOST_OS is DARWIN, "No 'sample' measurement on Darwin.")
    def test_new_project(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/29"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, project_create_cmd, ['test_proj'])
        self.assertIn("Created a new project named 'test_proj'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, project_edit_cmd, 
                                                       ['test_proj', '--add-measurements', 'profile', 'sample'])
        self.assertIn("Added measurement 'profile' to project configuration", stdout)
        self.assertIn("Added measurement 'sample' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, project_edit_cmd, ['test_proj', '--add-application', 'app1'])
        self.assertIn("Added application 'app1' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, project_edit_cmd, ['test_proj', '--add-target', 'targ1'])
        self.assertIn("Added target 'targ1' to project configuration", stdout)
        self.assertFalse(stderr)
        _, stderr = self.assertCommandReturnValue(0, project_select_cmd, ['test_proj'])
        self.assertFalse(stderr)
        argv = ['exp2', '--target', 'targ1', '--application', 'app1', '--measurement', 'sample']
        stdout, stderr = self.assertCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertIn("Created a new experiment", stdout)
        self.assertFalse(stderr)
