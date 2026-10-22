#
# Copyright (c) 2016-2026, ParaTools, Inc.
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

Functions used for unit tests of levels.py.
"""

import os
import stat
import subprocess
import sys
import tempfile
from taucmdr import tests

_BACKENDS = ('tinydb', 'sqlite')

# Prints the storage levels a new process sees, one fact per line.
_SHOW_LEVELS = '''
from taucmdr.cf.storage import levels
print(','.join(level.name for level in levels.ORDERED_LEVELS))
print(levels.SYSTEM_STORAGE is None)
print(levels.highest_writable_storage().name)
'''


class LevelsTest(tests.TestCase):
    """Tests for the storage levels with and without a system level."""

    def setUp(self):
        super().setUp()
        self._readonly = []

    def tearDown(self):
        for path in self._readonly:
            for root, dirs, files in os.walk(path):
                for name in dirs + files:
                    os.chmod(os.path.join(root, name), stat.S_IRWXU)
            os.chmod(path, stat.S_IRWXU)
        super().tearDown()

    def _make_readonly(self, path):
        """Remove write permission from `path` and everything under it until the test ends."""
        self._readonly.append(path)
        for root, dirs, files in os.walk(path):
            for name in dirs + files:
                full = os.path.join(root, name)
                os.chmod(full, os.stat(full).st_mode & ~0o222)
        os.chmod(path, os.stat(path).st_mode & ~0o222)

    @staticmethod
    def _dirs():
        """Return a new user prefix and project directory under the test work dir."""
        root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        user, project = os.path.join(root, 'user'), os.path.join(root, 'project')
        os.mkdir(user)
        os.mkdir(project)
        return root, user, project

    def _python(self, code, backend, user, system=None):
        proc = subprocess.run([sys.executable, '-I', '-c', code], capture_output=True, text=True,
                              env=tests.tau_subprocess_env(backend, user, system), check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout.splitlines()

    def _tau(self, args, backend, cwd, user, system=None, *, expect_success=True):
        proc = tests.run_tau_subprocess(args, backend, cwd, user, system)
        for text in 'Traceback', 'Exception ignored':
            self.assertNotIn(text, proc.stderr)
        if expect_success:
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def test_no_system_level(self):
        for backend in _BACKENDS:
            with self.subTest(backend=backend):
                _, user, project = self._dirs()
                self.assertEqual(self._python(_SHOW_LEVELS, backend, user), ['project,user', 'True', 'user'])
                proc = self._tau(['target', 'list', '-@', 'system'], backend, project, user, expect_success=False)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn('invalid choice', proc.stderr)

    def test_missing_system_prefix(self):
        """A system prefix that doesn't exist is an empty level that nothing writes to or creates."""
        for backend in _BACKENDS:
            with self.subTest(backend=backend):
                root, user, project = self._dirs()
                parent = os.path.join(root, 'ro')
                os.mkdir(parent)
                self._make_readonly(parent)
                system = os.path.join(parent, 'sys')
                self._tau(['--version'], backend, project, user, system)
                self._tau(['initialize', '--bare'], backend, project, user, system)
                self._tau(['target', 'list'], backend, project, user, system)
                self._tau(['target', 'list', '-@', 'system'], backend, project, user, system)
                self.assertEqual(self._python(_SHOW_LEVELS, backend, user, system),
                                 ['project,user,system', 'False', 'user'])
                self.assertFalse(os.path.exists(system))

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from writing")
    def test_readonly_system_level(self):
        """A read-only system level is still read, and writing to it is an error, not a crash."""
        for backend in _BACKENDS:
            with self.subTest(backend=backend):
                root, user, project = self._dirs()
                system = os.path.join(root, 'sys')
                os.mkdir(system)
                self._tau(['initialize', '--bare'], backend, project, user, system)
                self._tau(['target', 'create', 'systarg', '-@', 'system'], backend, project, user, system)
                self._make_readonly(system)
                proc = self._tau(['target', 'list', '-s', '-@', 'system'], backend, project, user, system)
                self.assertIn('systarg', proc.stdout)
                self.assertEqual(self._python(_SHOW_LEVELS, backend, user, system)[2], 'user')
                proc = self._tau(['target', 'create', 'other', '-@', 'system'], backend, project, user, system,
                                 expect_success=False)
                output = proc.stdout + proc.stderr
                self.assertNotEqual(proc.returncode, 0, output)
                self.assertIn('write', output)
                self.assertNotIn('Traceback', output)

    def test_tau_source_default(self):
        """Without a system level, TAU is downloaded by default."""
        for backend in _BACKENDS:
            with self.subTest(backend=backend):
                _, user, _ = self._dirs()
                code = 'from taucmdr.model.target import tau_source_default; print(tau_source_default())'
                self.assertEqual(self._python(code, backend, user), ['download'])

    def test_import_computes_no_level(self):
        """Importing the experiment model doesn't look for a writable storage level."""
        code = '\n'.join(['from taucmdr.cf.storage import levels',
                          'def refuse():',
                          '    raise RuntimeError("highest_writable_storage called on import")',
                          'levels.highest_writable_storage = refuse',
                          'import taucmdr.model.experiment'])
        _, user, _ = self._dirs()
        self._python(code, None, user)
