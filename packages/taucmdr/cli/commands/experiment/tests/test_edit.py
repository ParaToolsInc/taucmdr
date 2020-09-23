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

Functions used for unit tests of edit.py.
"""


from __future__ import absolute_import
from taucmdr import tests
from taucmdr.cli.commands.experiment.edit import COMMAND as EXPERIMENT_EDIT_COMMAND
from taucmdr.cli.commands.experiment.create import COMMAND as EXPERIMENT_CREATE_COMMAND
from taucmdr.cli.commands.application.copy import COMMAND as APPLICATION_COPY_COMMAND
from taucmdr.cli.commands.select import COMMAND as SELECT_COMMAND


class EditTest(tests.TestCase):
    """Tests for :any:`experiment.edit`."""

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND, [])
        self.assertIn('the following arguments are required', stderr)
        self.assertFalse(stdout)

    def test_invalid_experiment_name(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND,
                                                          ['targ1-app2-profile', '--measurement', 'trace'])
        self.assertIn("No project-level experiment with name='targ1-app2-profile'.", stderr)
        self.assertFalse(stdout)

    def test_invalid_target(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND,
                                                          ['targ1-app1-profile', '--target', 'no_such_targ'])
        self.assertIn("Invalid target: no_such_targ", stderr)
        self.assertFalse(stdout)

    def test_invalid_application(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND,
                                                          ['targ1-app2-profile', '--application', 'no_such_app'])
        self.assertIn("Invalid application: no_such_app", stderr)
        self.assertFalse(stdout)

    def test_invalid_measurement(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND,
                                                          ['targ1-app2-profile', '--measurement', 'no_such_meas'])
        self.assertIn("Invalid measurement: no_such_meas", stderr)
        self.assertFalse(stdout)

    def test_create_and_edit(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/198"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, APPLICATION_COPY_COMMAND, ['app1', 'app2', '--openmp'])
        self.assertIn("Added application 'app2' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, EXPERIMENT_CREATE_COMMAND,
                                                       ['exp1', '--target', 'targ1',
                                                        '--application', 'app1',
                                                        '--measurement', 'profile'])
        self.assertIn("Created a new experiment 'exp1'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND, ['exp1', '--application', 'app2'])

    def test_select_and_edit(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/198"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, APPLICATION_COPY_COMMAND, ['app1', 'app2', '--openmp'])
        self.assertIn("Added application 'app2' to project configuration", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, SELECT_COMMAND, ['app1', 'profile'])
        self.assertIn("elected experiment 'targ1-app1-profile'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, EXPERIMENT_EDIT_COMMAND,
                                                       ['targ1-app1-profile', '--application', 'app2'])
