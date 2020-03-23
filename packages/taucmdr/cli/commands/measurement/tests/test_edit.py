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
from taucmdr.error import IncompatibleRecordError
from taucmdr.model.project import Project
from taucmdr.model.measurement import Measurement
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.measurement.create import COMMAND as CREATE_COMMAND
from taucmdr.cli.commands.measurement.edit import COMMAND as EDIT_COMMAND

class EditTest(tests.TestCase):
    """Tests for :any:`measurement.edit`."""

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, EDIT_COMMAND, [])
        self.assertIn('too few arguments', stderr)
        self.assertFalse(stdout)

    def test_edit(self):
        self.reset_project_storage()
        old_name = 'meas01'
        new_name = 'meas02'
        self.assertCommandReturnValue(0, CREATE_COMMAND, [old_name])
        stdout, stderr = self.assertCommandReturnValue(0, EDIT_COMMAND, [old_name, '--new-name', new_name])
        self.assertIn("Updated measurement '%s'" % old_name, stdout)
        self.assertFalse(stderr)

    def test_wrongname(self):
        self.reset_project_storage()
        argv = ['meas1', '--new-name', 'meas2']
        _, stderr = self.assertNotCommandReturnValue(0, EDIT_COMMAND, argv)
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: No project-level measurement with name', stderr)

    def test_wrongarg(self):
        self.reset_project_storage()
        name = 'meas01'
        self.assertCommandReturnValue(0, CREATE_COMMAND, [name])
        _, stderr = self.assertNotCommandReturnValue(0, EDIT_COMMAND, ['meas01', '--track-mpi', 'T'])
        self.assertIn('measurement edit <measurement_name> [arguments]', stderr)
        self.assertIn('measurement edit: error: unrecognized arguments', stderr)

    def test_trace_edit(self):
        self.reset_project_storage()
        name = 'test_trace_edit'
        create_args = [name, '--profile', 'tau', '--trace', 'none', '--callpath', '10']
        stdout, stderr = self.assertCommandReturnValue(0, CREATE_COMMAND, create_args)
        self.assertFalse(stderr)
        self.assertIn("Added measurement '%s' to project" % name, stdout)
        self.assertNotIn("WARNING", stdout)
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas['callpath'], 10)
        self.assertEqual(meas['profile'], 'tau')
        self.assertEqual(meas['trace'], 'none')
        stdout, stderr = self.assertCommandReturnValue(0, EDIT_COMMAND, [name, '--trace', 'slog2'])
        self.assertFalse(stderr)
        self.assertIn("WARNING", stdout)
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas['callpath'], 10)
        self.assertEqual(meas['profile'], 'tau')
        self.assertEqual(meas['trace'], 'slog2')

    def test_trace_callpath_edit(self):
        self.reset_project_storage()
        name = 'test_trace_callpath_edit'
        stdout, stderr = self.assertCommandReturnValue(0, CREATE_COMMAND, [name, '--trace'])
        self.assertFalse(stderr)
        self.assertIn("Added measurement '%s' to project" % name, stdout)
        self.assertNotIn("WARNING", stdout)
        stdout, stderr = self.assertCommandReturnValue(0, EDIT_COMMAND, [name, '--callpath', '100'])
        self.assertFalse(stderr)
        self.assertIn("WARNING", stdout)

    def test_set_tau_force_options(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('force-tau-options' in expr.populate('measurement'))
        tau_options = "-optVerbose -optNoCompInst"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--force-tau-options=%s' % tau_options])
        # Check that 'force-tau-options' is now a list containing the expected options in the project record
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        self.assertListEqual(meas['force_tau_options'], [tau_options])

    def test_set_tau_force_options_none(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('force-tau-options' in expr.populate('measurement'))
        tau_options = "none"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--force-tau-options=%s' % tau_options])
        # Check that 'force-tau-options' is now a list containing the expected options in the project record
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        self.assertNotIn('force_tau_options', meas)

    def test_set_tau_extra_options(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('extra-tau-options' in expr.populate('measurement'))
        tau_options = "-optKeepFiles"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--extra-tau-options=%s' % tau_options])
        # Check that 'extra-tau-options' is now a list containing the expected options in the project record
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        self.assertListEqual(meas['extra_tau_options'], [tau_options])

    def test_set_tau_extra_options_none(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('extra-tau-options' in expr.populate('measurement'))
        tau_options = "none"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--extra-tau-options=%s' % tau_options])
        # Check that 'extra-tau-options' is now a list containing the expected options in the project record
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        self.assertNotIn('extra_tau_options', meas)

    def test_set_tau_forced_extra_options(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('extra-tau-options' in expr.populate('measurement'))
        self.assertFalse('forced-tau-options' in expr.populate('measurement'))
        tau_options = "-optKeepFiles"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--extra-tau-options=%s' % tau_options])
        with self.assertRaises(IncompatibleRecordError):
            self.assertNotCommandReturnValue(0, EDIT_COMMAND, ['profile', '--force-tau-options=%s' % tau_options])
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        #self.assertListEqual(meas['extra_tau_options'], [tau_options])

    def test_set_tau_forced_extra_options_none(self):
        self.reset_project_storage()
        expr = Project.selected().experiment()
        self.assertFalse('extra-tau-options' in expr.populate('measurement'))
        self.assertFalse('forced-tau-options' in expr.populate('measurement'))
        tau_options = "none"
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--extra-tau-options=%s' % tau_options])
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['profile', '--force-tau-options=%s' % tau_options])
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': 'profile'})
        self.assertIsNotNone(meas)
        self.assertNotIn('extra_tau_options', meas)
        self.assertNotIn('force_tau_options', meas)
