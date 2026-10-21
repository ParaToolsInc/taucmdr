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
"""Unit tests for the test runner itself."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import taucmdr
from taucmdr import tests

_RUN_TESTS = os.path.join(tests.REPO_DIR, 'scripts', 'run_tests.py')

_PASSING_TEST = '''
    import unittest

    class Probe(unittest.TestCase):
        def test_probe(self):
            pass
'''

_LOCKED_DIR_TEST = '''
    import os
    import unittest

    class Probe(unittest.TestCase):
        def test_probe(self):
            locked = os.path.join(os.environ['__TAUCMDR_USER_PREFIX__'], 'locked')
            os.makedirs(locked)
            with open(os.path.join(locked, 'file'), 'w'):
                pass
            os.chmod(locked, 0o500)
'''

_WARNING_TEST = '''
    import unittest
    import warnings

    class Probe(unittest.TestCase):
        def test_taucmdr_warning(self):
            warnings.warn_explicit('old taucmdr feature', DeprecationWarning, 'probe.py', 1, module='taucmdr.probe')

        def test_other_warning(self):
            warnings.warn_explicit('old feature elsewhere', DeprecationWarning, 'probe.py', 1, module='otherpackage')
'''


class RunTestsTest(tests.TestCase):
    """Tests for ``scripts/run_tests.py``."""

    def _run(self, *args, pythonpath=()):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(list(pythonpath) + sys.path))
        proc = subprocess.run([sys.executable, _RUN_TESTS] + list(args), env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, check=False)
        test_ids = [line for line in proc.stdout.splitlines() if line.startswith('taucmdr.')]
        return proc.returncode, test_ids, proc.stdout

    @staticmethod
    def _make_modules(files):
        """Write `files` into a new directory and return the directory."""
        root = tempfile.mkdtemp(dir=os.getcwd())
        for relpath, source in files.items():
            path = os.path.join(root, relpath)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as fout:
                fout.write(textwrap.dedent(source))
        return root

    def test_script_name(self):
        """The runner makes help messages use the name `tau`."""
        self.assertEqual(taucmdr.TAUCMDR_SCRIPT, 'tau')

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_repo_dir(self):
        """The runner tells the tests where the checkout is."""
        repo_dir = os.path.dirname(os.path.dirname(_RUN_TESTS))
        self.assertEqual(os.path.realpath(os.environ['__TAUCMDR_REPO_DIR__']), os.path.realpath(repo_dir))
        self.assertEqual(os.path.realpath(tests.REPO_DIR), os.path.realpath(repo_dir))
        self.assertTrue(os.path.exists(os.path.join(tests.REPO_DIR, '.testfiles', 'foo_launcher')))
        self.assertTrue(os.path.exists(os.path.join(tests.REPO_DIR, 'pylintrc')))

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_prints_tested_package(self):
        """The runner says which copy of taucmdr it is testing."""
        retval, _, output = self._run('--list', 'taucmdr.tests.test_init')
        self.assertEqual(retval, 0, output)
        self.assertIn(f"Testing taucmdr from {os.path.dirname(os.path.abspath(taucmdr.__file__))}", output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_package_name(self):
        """Listing tests by package name lists the tests in every test module under it."""
        retval, test_ids, output = self._run('--list', 'taucmdr.model.tests')
        self.assertEqual(retval, 0, output)
        self.assertIn('taucmdr.model.tests.test_target.TargetTest.test_unknown_host_arch', test_ids)
        self.assertIn('taucmdr.model.tests.test_compiler.CompilerTest.test_unknown_family', test_ids)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_name_without_tests(self):
        """Listing a package that holds no tests is an error."""
        for args in (['--list', 'taucmdr.error'], ['taucmdr.error']):
            retval, test_ids, output = self._run(*args)
            self.assertEqual(retval, 1, output)
            self.assertEqual(test_ids, [])
            self.assertIn('taucmdr.error', output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_list_unloadable_name(self):
        """Listing a name that can't be loaded is an error."""
        for name in ('taucmdr.nosuchmodule', 'taucmdr.model.tests.test_target.TargetTest.test_nosuchtest'):
            with self.subTest(name=name):
                retval, _, output = self._run('--list', name)
                self.assertEqual(retval, 1, output)
                self.assertIn("ERROR: Couldn't load", output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_import_error_traceback(self):
        """A package that raises an exception when imported shows a traceback, not a "no tests" error."""
        root = self._make_modules({'brokenpkg/__init__.py': "raise ValueError('broken package')\n"})
        retval, _, output = self._run('--list', 'brokenpkg', pythonpath=[root])
        self.assertNotEqual(retval, 0, output)
        self.assertIn('Traceback', output)
        self.assertIn('broken package', output)
        self.assertNotIn("doesn't contain any tests", output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_namespace_package(self):
        """Listing a namespace package gives a "no tests" error."""
        root = self._make_modules({'nspkg/test_probe.py': _PASSING_TEST})
        retval, _, output = self._run('--list', 'nspkg', pythonpath=[root])
        self.assertEqual(retval, 1, output)
        self.assertIn("ERROR: 'nspkg' doesn't contain any tests", output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from deleting files")
    def test_sandbox_cleanup_failure(self):
        """The runner warns about a sandbox directory it can't delete."""
        root = self._make_modules({'sandboxprobe/__init__.py': '', 'sandboxprobe/test_probe.py': _LOCKED_DIR_TEST})
        retval, _, output = self._run('-U', 'sandboxprobe.test_probe', pythonpath=[root])
        sandbox = re.search(r'Sandboxing user storage: (\S+)', output).group(1)
        self.addCleanup(shutil.rmtree, sandbox, ignore_errors=True)
        self.addCleanup(os.chmod, os.path.join(sandbox, 'locked'), 0o700)
        self.assertEqual(retval, 0, output)
        self.assertIn(f"WARNING: Couldn't delete sandbox directory {sandbox}", output)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_deprecation_warnings(self):
        """Deprecation warnings from TAU Commander's own modules fail the run; other deprecation warnings don't."""
        root = self._make_modules({'warnprobe/__init__.py': '', 'warnprobe/test_probe.py': _WARNING_TEST})
        retval, _, output = self._run('warnprobe.test_probe.Probe.test_taucmdr_warning', pythonpath=[root])
        self.assertEqual(retval, 1, output)
        self.assertIn('old taucmdr feature', output)
        retval, _, output = self._run('warnprobe.test_probe.Probe.test_other_warning', pythonpath=[root])
        self.assertEqual(retval, 0, output)
