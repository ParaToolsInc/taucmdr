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

Functions used for unit tests of taucmdr/__init__.py.
"""

import importlib.metadata
import os
import sys
import tempfile
import textwrap
import taucmdr
from taucmdr import tests


def _import_with_version(version):
    """Import taucmdr in a new interpreter whose ``sys.version_info`` reports `version` (MAJOR, MINOR)."""
    version_info = tuple(version) + (0, 'final', 0)
    code = f"import sys; sys.version_info = {version_info!r}; import taucmdr"
    return tests.run_python_subprocess(['-c', code], isolated=False)


class PythonVersionTest(tests.TestCase):
    """Tests for the Python version check in :py:mod:`taucmdr`."""

    def test_supported_versions(self):
        for version in ((3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16)):
            with self.subTest(version=version):
                proc = _import_with_version(version)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unsupported_versions(self):
        for version in ((2, 7), (3, 7), (3, 8), (3, 10)):
            with self.subTest(version=version):
                proc = _import_with_version(version)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn('Python 3.11 or newer is required', proc.stderr)


class VersionTest(tests.TestCase):
    """Tests for :py:data:`taucmdr.__version__`."""

    def test_installed_version(self):
        """The version is the installed package's version, derived from a release tag."""
        self.assertEqual(taucmdr.__version__, importlib.metadata.version('taucmdr'))
        self.assertNotEqual(taucmdr.__version__, '0.0.0')
        # setuptools-scm gives 0.1.dev... when it can't see any tags, e.g. in a shallow clone.
        self.assertFalse(taucmdr.__version__.startswith('0.1.dev'), taucmdr.__version__)


class InstalledPackageTest(tests.TestCase):
    """Tests that tox tests the installed wheel."""

    @tests.skipUnless(os.environ.get('TOX_ENV_NAME'), "Only checked under tox")
    def test_tests_use_installed_package(self):
        """Under tox, the tested taucmdr is the one installed in the environment, not a checkout on `PYTHONPATH`."""
        package = os.path.realpath(taucmdr.__file__)
        prefix = os.path.realpath(sys.prefix)
        self.assertEqual(os.path.commonpath([package, prefix]), prefix, package)


class GlobalsTest(tests.TestCase):
    """Tests for the paths and names :py:mod:`taucmdr` defines when it is imported."""

    @staticmethod
    def _print_system_prefix(env, cwd=None):
        """Print :any:`taucmdr.SYSTEM_PREFIX` in a new process.

        Both system prefix variables are unset unless `env` sets them.
        """
        env = dict({'TAUCMDR_SYSTEM_PREFIX': None, '__TAUCMDR_SYSTEM_PREFIX__': None}, **env)
        proc = tests.run_python_subprocess(['-c', 'import taucmdr; print(taucmdr.SYSTEM_PREFIX)'], env=env, cwd=cwd,
                                           isolated=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr

    def test_system_prefix_default(self):
        """There is no system prefix unless one is set."""
        home = tempfile.mkdtemp(dir=os.getcwd())
        retval, out, err = self._print_system_prefix({'HOME': home})
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, 'None')

    def test_system_prefix_empty(self):
        """An empty TAUCMDR_SYSTEM_PREFIX means there is no system prefix."""
        retval, out, err = self._print_system_prefix({'TAUCMDR_SYSTEM_PREFIX': ''})
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, 'None')

    def test_system_prefix_public_name(self):
        """The system prefix is set by TAUCMDR_SYSTEM_PREFIX."""
        absolute = tempfile.mkdtemp(dir=os.getcwd())
        retval, out, err = self._print_system_prefix({'TAUCMDR_SYSTEM_PREFIX': absolute})
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, os.path.realpath(absolute))

    def test_system_prefix_override(self):
        """The system prefix is set by __TAUCMDR_SYSTEM_PREFIX__; a relative path is relative to the working directory."""
        cwd = tempfile.mkdtemp(dir=os.getcwd())
        retval, out, err = self._print_system_prefix({'__TAUCMDR_SYSTEM_PREFIX__': 'system'}, cwd=cwd)
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, os.path.realpath(os.path.join(cwd, 'system')))
        absolute = tempfile.mkdtemp(dir=os.getcwd())
        retval, out, err = self._print_system_prefix({'__TAUCMDR_SYSTEM_PREFIX__': absolute}, cwd=cwd)
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, os.path.realpath(absolute))

    def test_same_prefix_both_names(self):
        """Both variables may be set if they lead to the same directory."""
        real = tempfile.mkdtemp(dir=os.getcwd())
        link = real + '-link'
        os.symlink(real, link)
        retval, out, err = self._print_system_prefix({'TAUCMDR_SYSTEM_PREFIX': link,
                                                      '__TAUCMDR_SYSTEM_PREFIX__': real + os.sep})
        self.assertEqual(retval, 0, err)
        self.assertEqual(out, os.path.realpath(real))

    def test_system_prefix_conflict(self):
        """Both variables set to different directories is an error."""
        first = tempfile.mkdtemp(dir=os.getcwd())
        second = tempfile.mkdtemp(dir=os.getcwd())
        retval, out, err = self._print_system_prefix({'TAUCMDR_SYSTEM_PREFIX': first,
                                                      '__TAUCMDR_SYSTEM_PREFIX__': second})
        self.assertEqual(retval, taucmdr.EXIT_FAILURE % 256, out)
        self.assertIn(first, err)
        self.assertIn(second, err)
        self.assertIn('Set only one.', err)

    def test_no_install_tree(self):
        """TAU Commander doesn't assume it lives in an install tree."""
        self.assertFalse(hasattr(taucmdr, 'TAUCMDR_HOME'))

    def test_script_name_default(self):
        """The script name is `tau` unless the launcher specifies otherwise, however Python was started."""
        cwd = tempfile.mkdtemp(dir=os.getcwd())
        os.mkdir(os.path.join(cwd, 'probe'))
        with open(os.path.join(cwd, 'probe', '__init__.py'), 'w', encoding='utf-8') as fout:
            fout.write(textwrap.dedent("""\
                import taucmdr
                print(taucmdr.TAUCMDR_SCRIPT)
                """))
        with open(os.path.join(cwd, 'probe', 'main.py'), 'w', encoding='utf-8'):
            pass
        for args in (['-c', 'import taucmdr; print(taucmdr.TAUCMDR_SCRIPT)'], ['-m', 'probe.main']):
            with self.subTest(args=args):
                proc = tests.run_python_subprocess(args, env={'__TAUCMDR_SCRIPT__': None}, cwd=cwd, isolated=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), 'tau')
