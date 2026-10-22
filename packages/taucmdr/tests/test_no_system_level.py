#
# Copyright (c) 2026, ParaTools, Inc.
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

Checks that TAU Commander builds and runs everything from user and project storage when there's no system level.
"""

import glob
import os
import shutil
import tempfile
import taucmdr
from taucmdr import tests

_BACKENDS = ('tinydb', 'sqlite')

# Compiler instrumentation needs only binutils and libunwind besides TAU.
_INIT_ARGS = ['initialize', '--tau', 'nightly', '--sample', 'False', '--source-inst', 'never',
              '--compiler-inst', 'always', '--trace', 'none', '--mpi', 'False', '--openmp', 'ignore',
              '--pdt', 'None', '--libdwarf', 'None', '--libelf', 'None', '--gotcha', 'None', '--papi', 'None',
              '--otf', 'None', '--scorep', 'None', '--sqlite3', 'None', '--ompt', 'None']


class NoSystemLevelTest(tests.TestCase):
    """Builds TAU and runs a trial with no system level."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        cls.user = os.path.join(root, 'user')
        cls.project = os.path.join(root, 'project')
        os.makedirs(os.path.join(cls.user, 'src'))
        os.mkdir(cls.project)
        # Source archives the test runner's system level already has are linked rather than downloaded again
        # to reduce the time required to run the tests.
        for archive in glob.glob(os.path.join(taucmdr.SYSTEM_PREFIX, 'src', '*')):
            os.symlink(archive, os.path.join(cls.user, 'src', os.path.basename(archive)))
        cls.backend = os.environ.get('__TAUCMDR_DB_BACKEND__')
        cls.init = tests.run_tau_subprocess(_INIT_ARGS, cls.backend, cls.project, cls.user)

    def _tau(self, args, cwd=None):
        proc = tests.run_tau_subprocess(args, self.backend, cwd or self.project, self.user)
        self.assertSucceeded(proc)
        return proc

    def test_packages_in_user_storage(self):
        self.assertSucceeded(self.init)
        self.assertTrue(glob.glob(os.path.join(self.user, 'tau', '*', '*', 'lib', 'Makefile.tau*')))
        for args in ['dashboard', '-l'], ['experiment', 'list', '-l']:
            self.assertNotIn(taucmdr.SYSTEM_PREFIX, self._tau(args).stdout)

    def test_trial_without_system_level(self):
        self.assertSucceeded(self.init)
        shutil.copy(os.path.join(tests.REPO_DIR, '.testfiles', 'matmult.c'), self.project)
        self._tau(['gcc', 'matmult.c', '-o', 'a.out'])
        self.assertIn('produced', self._tau(['trial', 'create', './a.out']).stdout)
        self.assertTrue(glob.glob(os.path.join(self.project, '.tau', '**', 'profile.*'), recursive=True))

    def test_system_commands_refused(self):
        """The commands that write to the system level say how to configure one."""
        empty = tempfile.mkdtemp(dir=tests.get_test_workdir())
        for backend in _BACKENDS:
            for args in ['system', 'configure', '--tau-config', 'minimal'], ['system', 'import', empty]:
                with self.subTest(backend=backend, args=args):
                    proc = tests.run_tau_subprocess(args, backend, empty, self.user)
                    self.assertCleanExit(proc)
                    self.assertNotEqual(proc.returncode, 0)
                    self.assertIn('No system-level storage is configured.', proc.stdout + proc.stderr)
                    self.assertIn('TAUCMDR_SYSTEM_PREFIX', proc.stdout + proc.stderr)
                    self.assertFalse(os.path.exists(os.path.join(empty, '.tau')))

    def test_project_after_removal(self):
        """A project made while a system level was set still works after it's unset."""
        for backend in _BACKENDS:
            with self.subTest(backend=backend):
                root = tempfile.mkdtemp(dir=tests.get_test_workdir())
                user, project, system = (os.path.join(root, name) for name in ('user', 'project', 'sys'))
                for path in user, project, system:
                    os.mkdir(path)
                self.assertSucceeded(tests.run_tau_subprocess(['initialize', '--bare'], backend, project, user, system))
                for args in ['dashboard'], ['target', 'list']:
                    self.assertSucceeded(tests.run_tau_subprocess(args, backend, project, user))
