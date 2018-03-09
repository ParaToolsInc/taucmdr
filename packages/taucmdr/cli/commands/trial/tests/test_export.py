# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, ParaTools, Inc.
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

Functions used for unit tests of export.py.
"""

import os
from taucmdr import tests, util, EXIT_SUCCESS
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_cmd
from taucmdr.cli.commands.trial.export import COMMAND as trial_export_cmd
from taucmdr.model.project import Project


class ExportTest(tests.TestCase):

    @tests.skipUnless(util.which('java'), "A java interpreter is required for this test")
    def test_export_tau_profile(self):
        self.reset_project_storage(['--profile', 'tau', '--trace', 'none'])
        expr = Project.selected().experiment()
        meas = expr.populate('measurement')
        self.assertEqual(meas['profile'], 'tau')
        self.assertEqual(meas['trace'], 'none')
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['./a.out'])
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_export_cmd, [])
        export_file = expr['name'] + '.trial0.ppk'
        self.assertTrue(os.path.exists(export_file))

    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_export_merged_profile(self):
        self.reset_project_storage(['--mpi', '--profile', 'merged', '--trace', 'none'])
        expr = Project.selected().experiment()
        meas = expr.populate('measurement')
        self.assertEqual(meas['profile'], 'merged')
        self.assertEqual(meas['trace'], 'none')
        self.assertManagedBuild(0, MPI_CC, [], 'mpi_hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_export_cmd, [])
        export_file = expr['name'] + '.trial0.xml.gz'
        self.assertTrue(os.path.exists(export_file))

    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_export_cubex(self):
        self.reset_project_storage(['--mpi', '--profile', 'cubex', '--trace', 'none'])
        expr = Project.selected().experiment()
        meas = expr.populate('measurement')
        self.assertEqual(meas['profile'], 'cubex')
        self.assertEqual(meas['trace'], 'none')
        self.assertManagedBuild(0, MPI_CC, [], 'mpi_hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_export_cmd, [])
        export_file = expr['name'] + '.trial0.cubex'
        self.assertTrue(os.path.exists(export_file))

    @tests.skipUnless(util.which('java'), "A java interpreter is required for this test")
    def test_export_slog2(self):
        self.reset_project_storage(['--trace', 'slog2', '--profile', 'none'])
        expr = Project.selected().experiment()
        meas = expr.populate('measurement')
        self.assertEqual(meas['trace'], 'slog2')
        self.assertEqual(meas['profile'], 'none')
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['./a.out'])
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_export_cmd, [])
        export_file = expr['name'] + '.trial0.slog2'
        self.assertTrue(os.path.exists(export_file))

    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_export_otf2(self):
        self.reset_project_storage(['--mpi', '--trace', 'otf2', '--profile', 'none'])
        expr = Project.selected().experiment()
        meas = expr.populate('measurement')
        self.assertEqual(meas['trace'], 'otf2')
        self.assertEqual(meas['profile'], 'none')
        self.assertManagedBuild(0, MPI_CC, [], 'mpi_hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_export_cmd, [])
        export_file = expr['name'] + '.trial0.tgz'
        self.assertTrue(os.path.exists(export_file))
