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


from taucmdr import tests, util
from taucmdr.cli.commands.target import edit

class EditTest(tests.TestCase):
    """Tests for :any:`target.delete`."""

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, [])
        self.assertIn('the following arguments are required', stderr)
        self.assertFalse(stdout)

    def test_edit(self):
        self.reset_project_storage()
        argv = ['targ1', '--new-name', 'targ2']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('Updated target \'targ1\'', stdout)
        self.assertFalse(stderr)

    def test_wrongname(self):
        self.reset_project_storage()
        argv = ['targ2', '--new-name', 'targ3']
        _, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('target edit <target_name> [arguments]', stderr)
        self.assertIn('target edit: error: No project-level target with name', stderr)

    def test_wrongarg(self):
        self.reset_project_storage()
        argv = ['app1', '--arg', 'T']
        _, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('target edit <target_name> [arguments]', stderr)
        self.assertIn('target edit: error: unrecognized arguments: --arg', stderr)

    def test_ambiguousarg(self):
        self.reset_project_storage()
        argv = ['targ1', '--mpi', 'T']
        _, stderr = self.assertNotCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn('target edit <target_name> [arguments]', stderr)
        self.assertIn('target edit: error: ambiguous option: --mpi could match --mpi-', stderr)

    @tests.skipUnless(util.which('mpicc'), "MPI compilers required for this test")
    def test_no_mpi(self):
        self.reset_project_storage()
        argv = ['targ1', '--mpi-wrappers', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn("Updated target \'targ1\'", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ1 = ctrl.one({'name': 'targ1'})
        for role, expected in (MPI_CC, ''), (MPI_CXX, ''), (MPI_FC, ''):
            path = targ1.populate(role.keyword)['path']
            self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")

    @tests.skipUnless(util.which('mpicc'), "MPI compilers required for this test")
    def test_no_mpi_cc(self):
        self.reset_project_storage()
        argv = ['targ1', '--mpi-cc', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn("Updated target \'targ1\'", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ1 = ctrl.one({'name': 'targ1'})
        path = targ1.populate(MPI_CC.keyword)['path']
        self.assertEqual(path, '', f"Target[{MPI_CC}] is '{path}', not ''")

    @tests.skipUnless(util.which('nvcc'), "CUDA CXX compiler required for this test")
    def test_no_cuda_cxx(self):
        self.reset_project_storage()
        argv = ['targ1', '--cuda-cxx', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn("Updated target \'targ1\'", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.cuda import CUDA_CXX
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ1 = ctrl.one({'name': 'targ1'})
        role = CUDA_CXX
        expected = ''
        path = targ1.populate(role.keyword)['path']
        self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")

    @tests.skipUnless(util.which('xlcuf'), "CUDA CXX compiler required for this test")
    def test_no_cuda_fc(self):
        self.reset_project_storage()
        argv = ['targ1', '--cuda-fc', 'None']
        stdout, stderr = self.assertCommandReturnValue(0, edit.COMMAND, argv)
        self.assertIn("Updated target \'targ1\'", stdout)
        self.assertFalse(stderr)
        from taucmdr.cf.compiler.cuda import CUDA_FC
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.model.target import Target
        ctrl = Target.controller(PROJECT_STORAGE)
        targ1 = ctrl.one({'name': 'targ1'})
        role = CUDA_FC
        expected = ''
        path = targ1.populate(role.keyword)['path']
        self.assertEqual(path, expected, f"Target[{role}] is '{path}', not '{expected}'")
