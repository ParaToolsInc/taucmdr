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
"""Tests that the ``tau`` launcher isolates TAU Commander from the user's Python environment.

By default they test the launcher installed next to the running interpreter. Set ``__TAUCMDR_TEST_LAUNCHER__``
to test another installation's launcher.
"""

import os
import shlex
import shutil
import subprocess
import sys
import sysconfig
import unittest
from taucmdr import tests

_PASSED_THROUGH = ('PYTHONPATH', 'PYTHONHOME', 'PYTHONWARNINGS', 'PYTHONINSPECT', '__TAUCMDR_SCRIPT__')

_PAGER_SCRIPT = """\
: > "$1"
for name in %s; do
  eval "value=\\${$name}"
  printf '%%s=%%s\\n' "$name" "$value" >> "$1"
done
cat
""" % ' '.join(_PASSED_THROUGH)


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fout:
        fout.write(text)


class LauncherTest(tests.TestCase):
    """Tests of the ``tau`` launcher script, run as a subprocess in a hostile environment."""

    @classmethod
    def setUpClass(cls):
        cls.launcher = (os.environ.get('__TAUCMDR_TEST_LAUNCHER__') or
                        os.path.join(sysconfig.get_path('scripts'), 'tau'))
        if not os.path.exists(cls.launcher):
            # Skipping would hide a mistyped override, or a tox environment that failed to install the wheel.
            if '__TAUCMDR_TEST_LAUNCHER__' in os.environ:
                raise AssertionError(f"__TAUCMDR_TEST_LAUNCHER__ is set to {cls.launcher}, which doesn't exist")
            if 'TOX_ENV_NAME' in os.environ:
                raise AssertionError(f"No launcher at {cls.launcher}, but tox installs one")
            raise unittest.SkipTest("TAU Commander isn't installed in this environment")
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.tmp = os.path.realpath(os.getcwd())
        self.pager_env = os.path.join(self.tmp, 'pager.env')
        _write(os.path.join(self.tmp, 'pager.sh'), _PAGER_SCRIPT)

    def _hostile_env(self, shadow=True, python_home=True):
        """Return an environment that would break an unisolated TAU Commander.

        Args:
            shadow (bool): Put shadow ``taucmdr`` and ``sitecustomize`` modules on ``PYTHONPATH``.
            python_home (bool): Set ``PYTHONHOME`` to a directory that doesn't exist.
        """
        shadow_dir = os.path.join(self.tmp, 'shadow')
        if shadow:
            _write(os.path.join(shadow_dir, 'taucmdr', '__init__.py'),
                   'raise SystemExit("shadowed taucmdr imported")\n')
            _write(os.path.join(shadow_dir, 'sitecustomize.py'), 'raise SystemExit("sitecustomize ran")\n')
        _write(os.path.join(shadow_dir, 'termcolor.py'), 'raise SystemExit("shadowed termcolor imported")\n')
        env = {key: value for key, value in os.environ.items()
               if key not in ('__TAUCMDR_DISABLE_PAGER__', '__TAUCMDR_SCRIPT__')}
        env.update(PYTHONPATH=shadow_dir,
                   PYTHONWARNINGS='error',
                   PYTHONINSPECT='1',
                   PAGER=f"sh {shlex.quote(os.path.join(self.tmp, 'pager.sh'))} {shlex.quote(self.pager_env)}")
        if python_home:
            env['PYTHONHOME'] = os.path.join(self.tmp, 'no-such-python-home')
        return env

    def _run(self, cmd, env):
        if os.path.exists(self.pager_env):
            os.remove(self.pager_env)
        # A relative storage prefix from the runner (CI uses `system`) resolves inside the test directory.
        return subprocess.run(cmd, env=env, cwd=self.tmp, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=120, check=False)

    def _read_pager_env(self):
        with open(self.pager_env, encoding='utf-8') as fin:
            return dict(line.rstrip('\n').split('=', 1) for line in fin)

    def _check_children_see_env(self, env, script):
        seen = self._read_pager_env()
        for name in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONWARNINGS', 'PYTHONINSPECT'):
            self.assertEqual(seen[name], env[name])
        self.assertEqual(seen['__TAUCMDR_SCRIPT__'], script)

    def test_shebang(self):
        """The launcher is a POSIX sh script."""
        with open(self.launcher, encoding='utf-8') as fin:
            self.assertEqual(fin.readline().rstrip('\n'), '#!/bin/sh')

    def test_hostile_environment(self):
        """The shadowed modules and Python variables don't stop `tau` from running."""
        proc = self._run([self.launcher, '--version'], self._hostile_env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('TAU Commander', proc.stdout)
        for output in proc.stdout, proc.stderr:
            self.assertNotIn('shadowed', output)
            self.assertNotIn('sitecustomize ran', output)

    def test_environment_reaches_children(self):
        """Programs started by `tau` see the user's Python variables and the launcher's path."""
        env = self._hostile_env()
        proc = self._run([self.launcher, 'help', 'target'], env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('Creating new targets:', proc.stdout)
        self._check_children_see_env(env, os.path.realpath(self.launcher))

    def test_symlinked_launcher(self):
        """Absolute, relative and chained symlinks, in a directory with a space, all find the real launcher."""
        env = self._hostile_env()
        base = os.path.join(self.tmp, 'with space')
        os.makedirs(os.path.join(base, 'bin'))
        os.makedirs(os.path.join(base, 'chain'))
        os.symlink(os.path.realpath(self.launcher), os.path.join(base, 'bin', 'tau-abs'))
        os.symlink('tau-abs', os.path.join(base, 'bin', 'tau-rel'))
        os.symlink(os.path.join('..', 'bin', 'tau-rel'), os.path.join(base, 'chain', 'tau'))
        for link in 'bin/tau-abs', 'bin/tau-rel', 'chain/tau':
            with self.subTest(link=link):
                proc = self._run([os.path.join(base, link), 'help', 'target'], env)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self._check_children_see_env(env, os.path.realpath(self.launcher))

    def test_missing_python(self):
        """A launcher with no Python next to it exits with an explanation."""
        bin_dir = os.path.join(self.tmp, 'bin')
        os.makedirs(bin_dir)
        copy = os.path.join(bin_dir, 'tau')
        shutil.copy(self.launcher, copy)
        proc = self._run([copy, '--version'], self._hostile_env())
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("can't find the Python interpreter", proc.stderr)

    def test_backstop_reexecs_isolated(self):
        """Running ``python -m taucmdr`` without the launcher restarts Python in isolated mode."""
        installed = os.path.join(os.path.dirname(sys.executable), 'tau')
        if os.path.realpath(self.launcher) != os.path.realpath(installed):
            self.skipTest("The launcher under test isn't the one next to this interpreter")
        # The shadow taucmdr and sitecustomize and PYTHONHOME would stop the first, non-isolated process
        # before it reaches the code that restarts Python.
        env = self._hostile_env(shadow=False, python_home=False)
        proc = self._run([sys.executable, '-m', 'taucmdr', 'help', 'target'], env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn('shadowed', proc.stdout + proc.stderr)
        self.assertEqual(self._read_pager_env()['__TAUCMDR_SCRIPT__'], installed)
