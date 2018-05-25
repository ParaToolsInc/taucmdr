# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, ParaTools, Inc.
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
# pylint: disable=missing-docstring
import os

from taucmdr import tests
from taucmdr.cf.platforms import HOST_ARCH
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.trial.renumber import COMMAND as RENUMBER_COMMAND
from taucmdr.cli.commands.trial.create import COMMAND as CREATE_COMMAND
from taucmdr.cli.commands.trial.list import COMMAND as LIST_COMMAND
from taucmdr.cli.commands.trial.edit import COMMAND as EDIT_COMMAND
from taucmdr.model.project import Project
from taucmdr.model.trial import Trial
from taucmdr.cli.commands.trial.delete import COMMAND as DELETE_COMMAND


class RenumberTest(tests.TestCase):
    """Tests for :any:`trial.renumber`."""

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_newtrial(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['0', '--description', 'desc0'])
        exp = Project.selected().experiment().eid
        old_path = Trial.controller(storage=PROJECT_STORAGE).search(
            {'number': 0, 'experiment': exp})[0].get_data_files()['tau']
        self.assertTrue(os.path.exists(old_path), "Data directory should exist after create")
        old_profile = os.path.join(old_path, "profile.0.0.0")
        self.assertTrue(os.path.exists(old_profile), "Profile should exist after create")
        with open(old_profile, 'r') as f:
            old_profile_contents = f.read()
        num_trials_before = Trial.controller(storage=PROJECT_STORAGE).count()
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['0', '--to', '1'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, [])
        self.assertIn('./a.out', stdout)
        self.assertIn('  1  ', stdout)
        self.assertIn('desc0', stdout)
        self.assertNotIn('  0  ', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        num_trials_after = Trial.controller(storage=PROJECT_STORAGE).count()
        self.assertEqual(num_trials_before, num_trials_after, "Renumbering should not change number of trials")
        self.assertFalse(os.path.exists(old_path), "Data directory for old number should not exist after renumber")
        self.assertFalse(os.path.exists(os.path.join(old_path, "profile.0.0.0")),
                         "Profile in old data directory should not exist after renumber")
        new_path = Trial.controller(storage=PROJECT_STORAGE).search(
            {'number': 1, 'experiment': exp})[0].get_data_files()['tau']
        self.assertTrue(os.path.exists(new_path),
                        "Data directory for new number should exist after renumber")
        new_profile = os.path.join(new_path, "profile.0.0.0")
        self.assertTrue(os.path.exists(new_profile),
                        "Profile in data directory for new number should exist after renumber")
        with open(new_profile, 'r') as f:
            new_profile_contents = f.read()
        self.assertEqual(old_profile_contents, new_profile_contents, "Profiles should be identical after renumber")

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_swaptrials(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        for i in xrange(3):
            self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
            self.assertCommandReturnValue(0, EDIT_COMMAND, [str(i), '--description', 'desc%s' % i])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['0', '1', '2', '--to', '1', '2', '0'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '0')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc2', stdout)
        self.assertNotIn('desc0', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '1')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc0', stdout)
        self.assertNotIn('desc1', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '2')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc1', stdout)
        self.assertNotIn('desc2', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        trials = Trial.controller(storage=PROJECT_STORAGE).search()
        self.assertEqual(len(trials), 3, "There should be three trials after renumber")
        for trial in trials:
            self.assertTrue(os.path.exists(trial.get_data_files()['tau']), "Trial should have data directory")
            self.assertTrue(os.path.exists(os.path.join(trial.get_data_files()['tau'], 'profile.0.0.0')),
                            "Trial should have profile in data directory")
            self.assertEqual(int(os.path.basename(trial.get_data_files()['tau'])), trial['number'],
                             "Trial number should match data directory name after renumber")

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_compresstrials(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        for i in xrange(13):
            self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
            self.assertCommandReturnValue(0, EDIT_COMMAND, [str(i), '--description', 'desc%s' % i])
        self.assertCommandReturnValue(0, DELETE_COMMAND, ['9', '11'])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['12', '--to', '9'])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['13', '--to', '11'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '8')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc8', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '9')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc12', stdout)
        self.assertNotIn('desc9', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '11')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc13', stdout)
        self.assertNotIn('desc11', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
