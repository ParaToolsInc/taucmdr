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


from taucmdr import tests
from taucmdr.cli.commands.measurement.create import COMMAND as CREATE_COMMAND
from taucmdr.cli.commands.measurement.edit import COMMAND as EDIT_COMMAND

class EditTest(tests.TestCase):
    """Tests for :any:`measurement.edit`."""

    def test_edit(self):
        self.reset_project_storage(project_name='proj1')
        old_name = 'meas01'
        new_name = 'meas02'
        self.assertCommandReturnValue(0, CREATE_COMMAND, [old_name])
        stdout, stderr = self.assertCommandReturnValue(0, EDIT_COMMAND, [old_name, '--new-name', new_name])
        self.assertIn("Updated measurement '%s'" % old_name, stdout)
        self.assertFalse(stderr)       

    def test_wrongname(self):
        self.reset_project_storage(project_name='proj1')
        argv = ['meas1', '--new-name', 'meas2']
        _, _, stderr = self.exec_command(EDIT_COMMAND, argv)
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: No project-level measurement with name', stderr)
        
    def test_wrongarg(self):
        self.reset_project_storage(project_name='proj1')
        name = 'meas01'
        self.assertCommandReturnValue(0, CREATE_COMMAND, [name])
        _, _, stderr = self.exec_command(EDIT_COMMAND, ['meas01', '--track-mpi', 'T'])
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: unrecognized arguments', stderr)
