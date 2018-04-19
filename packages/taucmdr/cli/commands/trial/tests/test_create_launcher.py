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

import shutil
from taucmdr import tests, util
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.caf import CAF_FC
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_cmd

class CreateLauncherTest(tests.TestCase):
    """Tests for :any:`trial.create` with an application launcher.
    
    https://github.com/ParaToolsInc/taucmdr/issues/210
    """

    def test_foo_launcher_simple(self):
        self.reset_project_storage()
        self.copy_testfile('foo_launcher')
        self.assertManagedBuild(0, CC, [], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./foo_launcher', './a.out'])
        self.assertFalse(stderr)
        self.assertIn("Multiple executables were found", stdout)
        self.assertIn("executable is './foo_launcher'", stdout)
        self.assertIn("FOO LAUNCHER\nDone", stdout)
        self.assertRegexpMatches(stdout, r'tau_exec .* ./foo_launcher ./a.out')
 
    def test_launcher_flag(self):
        self.reset_project_storage()
        self.copy_testfile('foo_launcher')
        self.assertManagedBuild(0, CC, [], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./foo_launcher', '--', './a.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertIn("FOO LAUNCHER\nDone", stdout)
        self.assertRegexpMatches(stdout, r'./foo_launcher tau_exec .* ./a.out')
         
    def test_invalid_exe(self):
        self.reset_project_storage()
        self.copy_testfile('foo_launcher')
        stdout, stderr = self.assertNotCommandReturnValue(0, trial_create_cmd, ['./foo_launcher', './invalid'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertIn("FOO LAUNCHER", stdout)
        self.assertRegexpMatches(stdout, r'tau_exec .* ./foo_launcher ./invalid')
         
    @tests.skipUnless(util.which('mpirun'), "mpirun required for this test")
    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_mpirun(self):
        self.reset_project_storage(['--mpi'])
        self.assertManagedBuild(0, MPI_CC, ['-DTAU_MPI'], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertRegexpMatches(stdout, r'mpirun -np 4 tau_exec .* ./a.out')

    @tests.skipUnless(util.which('mpirun'), "mpirun required for this test")
    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_mpirun_with_flag(self):
        self.reset_project_storage(['--mpi'])
        self.assertManagedBuild(0, MPI_CC, ['-DTAU_MPI'], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['mpirun', '-np', '4', '--', './a.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertIn("produced 4 profile files", stdout)
        self.assertRegexpMatches(stdout, r'mpirun -np 4 tau_exec .* ./a.out')

    @tests.skipUnless(util.which('mpirun'), "mpirun required for this test")
    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_mpirun_mpmd(self):
        self.reset_project_storage(['--mpi'])
        self.assertManagedBuild(0, MPI_CC, ['-DTAU_MPI'], 'matmult.c')
        shutil.copy('./a.out', './b.out')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, 
                                                       ['mpirun', '-np', '2', './a.out', ':', '-np', '2', './b.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertIn("produced 4 profile files", stdout)
        self.assertRegexpMatches(stdout, r'mpirun -np 2 tau_exec .* ./a.out : -np 2 tau_exec .* ./b.out')
         
    @tests.skipUnless(util.which('cafrun'), "cafrun required for this test")
    @tests.skipUnlessHaveCompiler(CAF_FC)
    def test_cafrun(self):
        self.reset_project_storage(['--caf','--caf-fc','caf','--source-inst','never','--compiler-inst','always','--mpi'])
        self.assertManagedBuild(0, CAF_FC, [], 'blockmatrix-coarray.f90')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['cafrun', '-np', '9', './a.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertRegexpMatches(stdout, r'cafrun -np 9 tau_exec .* ./a.out')

    @tests.skipUnless(util.which('cafrun'), "cafrun required for this test")
    @tests.skipUnlessHaveCompiler(CAF_FC)
    def test_cafrun_with_flag(self):
        self.reset_project_storage(['--caf','--caf-fc','caf','--source-inst','never','--compiler-inst','always','--mpi'])
        self.assertManagedBuild(0, CAF_FC, [], 'blockmatrix-coarray.f90')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['cafrun', '-np', '9', '--', './a.out'])
        self.assertFalse(stderr)
        self.assertNotIn("Multiple executables were found", stdout)
        self.assertNotIn("executable is './foo_launcher'", stdout)
        self.assertIn("produced 9 profile files", stdout)
        self.assertRegexpMatches(stdout, r'cafrun -np 9 tau_exec .* ./a.out')


