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

Functions used for unit tests of copy.py.
"""


from taucmdr import tests, util
from taucmdr.cli.commands.target import copy

class CopyTest(tests.TestCase):
    """Tests for :any:`target.delete`."""

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, copy.COMMAND, [])
        self.assertIn('the following arguments are required', stderr)
        self.assertFalse(stdout)

    def test_copy(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn('Added target \'targ2\' to project configuration', stdout)
        self.assertFalse(stderr)

    def test_wrongname(self):
        self.reset_project_storage()
        argv = ['targ2', 'targ3']
        _, stderr = self.assertNotCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn('target copy <target_name> <copy_name> [arguments]', stderr)
        self.assertIn('target copy: error: No project-level target with name', stderr)

    def test_wrongarg(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--arg', 'T']
        _, stderr = self.assertNotCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn('target copy <target_name> <copy_name> [arguments]', stderr)
        self.assertIn('target copy: error: unrecognized arguments: --arg', stderr)

    def test_ambiguousarg(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--mpi', 'T']
        _, stderr = self.assertNotCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn('target copy <target_name> <copy_name> [arguments]', stderr)
        self.assertIn('target copy: error: ambiguous option: --mpi could match --mpi-', stderr)

    def test_compilerarg(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--compiler', 'System']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn('Added target \'targ2\' to project configuration', stdout)
        self.assertFalse(stderr)

    @tests.skipUnless(util.which('mpicc'), "MPI compilers required for this test")
    def test_no_mpi(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--mpi-wrappers', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn("Added target \'targ2\' to project configuration", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ2 = ctrl.one({'name': 'targ2'})
        for role, expected in (MPI_CC, ''), (MPI_CXX, ''), (MPI_FC, ''):
            path = targ2.populate(role.keyword)['path']
            self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")


    @tests.skipUnless(util.which('mpicc'), "MPI compilers required for this test")
    def test_no_mpi_cc(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--mpi-cc', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn("Added target \'targ2\' to project configuration", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ2 = ctrl.one({'name': 'targ2'})
        path = targ2.populate(MPI_CC.keyword)['path']
        self.assertEqual(path, '', f"Target[MPI_CC] is '{path}', not ''")

    @tests.skipUnless(util.which('nvcc'), "CUDA compilers required for this test")
    def test_no_cuda_cxx(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--cuda-cxx', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn("Added target \'targ2\' to project configuration", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.cuda import CUDA_CXX, CUDA_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ2 = ctrl.one({'name': 'targ2'})
        role = CUDA_CXX
        expected = ''
        path = targ2.populate(role.keyword)['path']
        self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")

    @tests.skipUnless(util.which('xlcuf'), "CUDA compilers required for this test")
    def test_no_cuda_fc(self):
        self.reset_project_storage()
        argv = ['targ1', 'targ2', '--cuda-fc', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, copy.COMMAND, argv)
        self.assertIn("Added target \'targ2\' to project configuration", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.cuda import CUDA_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ2 = ctrl.one({'name': 'targ2'})
        role = CUDA_FC
        expected = ''
        path = targ2.populate(role.keyword)['path']
        self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")
