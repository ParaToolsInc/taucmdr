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

Checks that project and user databases written by TAU Commander v1.6.0 still open.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from taucmdr import tests

_FIXTURES = os.path.join(tests.REPO_DIR, '.testfiles', 'storage', 'v1.6.0')

_BACKENDS = ('tinydb', 'sqlite')


class OldDatabaseTest(tests.TestCase):
    """Opens, lists and changes records in v1.6.0 databases under both backends."""

    @staticmethod
    def _run_tau(args, backend, cwd, user_prefix, system_prefix=None):
        """Run ``tau`` in a new process.

        Args:
            args (list): Arguments to ``tau``.
            backend (str): Value for ``__TAUCMDR_DB_BACKEND__``, or None to leave it unset.
            cwd (str): Working directory of the new process.
            user_prefix (str): User-level storage prefix.
            system_prefix (str): System-level storage prefix, or None for no system prefix variables.

        Returns:
            subprocess.CompletedProcess: The finished process, with text output captured.
        """
        env = dict(os.environ, __TAUCMDR_USER_PREFIX__=user_prefix)
        for var in 'TAUCMDR_SYSTEM_PREFIX', '__TAUCMDR_SYSTEM_PREFIX__', '__TAUCMDR_DB_BACKEND__':
            env.pop(var, None)
        if system_prefix is not None:
            env['__TAUCMDR_SYSTEM_PREFIX__'] = system_prefix
        if backend is not None:
            env['__TAUCMDR_DB_BACKEND__'] = backend
        return subprocess.run([sys.executable, '-I', '-m', 'taucmdr', *args], env=env, cwd=cwd,
                              capture_output=True, text=True, check=False)

    def _check_each_fixture(self, check):
        """Call `check` on a fresh copy of each backend's fixture, in a subtest for each case.

        Args:
            check: function to call to check the fixture's result.
        """
        for backend in _BACKENDS:
            for backend_var in None, backend:
                with self.subTest(backend=backend, backend_var=backend_var):
                    root = tempfile.mkdtemp(dir=tests.get_test_workdir())
                    shutil.copytree(os.path.join(_FIXTURES, backend), root, dirs_exist_ok=True)
                    check(backend_var, os.path.join(root, 'project'), os.path.join(root, 'user'),
                          os.path.join(root, 'system'))

    def _assert_success(self, proc):
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_project_from_v160(self):
        def check(backend_var, project, user, system):
            proc = self._run_tau(['dashboard'], backend_var, project, user, system)
            self._assert_success(proc)
            for name in 'oldproj', 'oldtarg', 'oldapp', 'oldmeas':
                self.assertIn(name, proc.stdout)
            self._assert_success(self._run_tau(['experiment', 'list'], backend_var, project, user, system))
        self._check_each_fixture(check)

    def test_user_records_from_v160(self):
        def check(backend_var, project, user, system):
            proc = self._run_tau(['target', 'list', '-s', '-@', 'user'], backend_var, project, user, system)
            self._assert_success(proc)
            self.assertIn('usertarg', proc.stdout)
        self._check_each_fixture(check)

    def test_project_from_v160_writable(self):
        def check(backend_var, project, user, system):
            self._assert_success(self._run_tau(['measurement', 'copy', 'oldmeas', 'newmeas'],
                                               backend_var, project, user, system))
            proc = self._run_tau(['measurement', 'list', '-s'], backend_var, project, user, system)
            self._assert_success(proc)
            self.assertIn('newmeas', proc.stdout)
        self._check_each_fixture(check)
