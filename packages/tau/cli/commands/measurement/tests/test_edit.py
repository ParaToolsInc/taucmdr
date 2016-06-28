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


from tau import tests
from tau.cli.commands.measurement import edit

class EditTest(tests.TestCase):
    """Tests for :any:`measurement.edit`."""

    def test_edit(self):
        tests.reset_project_storage(project_name='proj1')
        argv = ['sample', '--new-name', 'sample01']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('Updated measurement \'sample\'', stdout)
        self.assertFalse(stderr)
        argv = ['sample01', '--new-name', 'sample1']
        self.exec_command(edit.COMMAND, argv)
        
    def test_wrongname(self):
        tests.reset_project_storage(project_name='proj1')
        argv = ['meas1', '--new-name', 'meas2']
        _, _, stderr = self.exec_command(edit.COMMAND, argv)
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: No project-level measurement with name', stderr)
        
    def test_wrongarg(self):
        tests.reset_project_storage(project_name='proj1')
        argv = ['sample', '--use-mpi', 'T']
        _, _, stderr = self.exec_command(edit.COMMAND, argv)
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: unrecognized arguments', stderr)
