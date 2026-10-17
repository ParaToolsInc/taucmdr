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

Functions used for unit tests of tau_installation.py.
"""

import glob
import os
import subprocess
import sys
import tempfile
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.software.tau_installation import TauInstallation, python_build_paths


class TauInstallationTest(tests.TestCase):
    """Tests for TauInstallation CUPTI detection and tagging."""

    def setUp(self):
        super().setUp()
        # Give each test its own isolated temp directory so tests don't
        # pollute each other's filesystem state.
        self._cuda_tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._cuda_tmpdir, ignore_errors=True)
        super().tearDown()

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _make_cupti_header(self, *path_parts):
        """Create a fake cupti_events.h under the per-test cuda tmpdir."""
        inc = os.path.join(self._cuda_tmpdir, *path_parts, 'include')
        os.makedirs(inc, exist_ok=True)
        open(os.path.join(inc, 'cupti_events.h'), 'w').close()

    def _fake_self(self, cuda_prefix):
        class _FakeSelf:
            pass
        fs = _FakeSelf()
        fs.cuda_prefix = cuda_prefix
        return fs

    # ------------------------------------------------------------------ #
    # _find_cupti_prefix                                                   #
    # ------------------------------------------------------------------ #

    def test_find_cupti_standard_sdk_layout(self):
        """extras/CUPTI/include/cupti_events.h — first candidate."""
        self._make_cupti_header('extras', 'CUPTI')
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, os.path.join(self._cuda_tmpdir, 'extras', 'CUPTI'))

    def test_find_cupti_system_packaged_layout(self):
        """<cuda>/include/cupti_events.h — third candidate (e.g. /usr)."""
        self._make_cupti_header()
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, self._cuda_tmpdir)

    def test_find_cupti_orig_layout(self):
        """extras/CUPTI.orig/include/cupti_events.h — fourth candidate."""
        self._make_cupti_header('extras', 'CUPTI.orig')
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, os.path.join(self._cuda_tmpdir, 'extras', 'CUPTI.orig'))

    def test_find_cupti_returns_none_when_missing(self):
        """No headers present: returns None."""
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertIsNone(result)

    def test_find_cupti_returns_none_when_no_cuda_prefix(self):
        """No cuda_prefix: returns None without touching filesystem."""
        result = TauInstallation._find_cupti_prefix(self._fake_self(None))
        self.assertIsNone(result)


def _has_headers(python_path):
    """Return True if the Python interpreter at `python_path` has its C headers installed."""
    check = 'import os, sysconfig; print(os.path.exists(os.path.join(sysconfig.get_path("include"), "Python.h")))'
    proc = subprocess.run([python_path, '-c', check], stdout=subprocess.PIPE, text=True, check=False)
    return proc.stdout.strip() == 'True'


class PythonBuildPathsTest(tests.TestCase):
    """Tests for :any:`python_build_paths`."""

    def test_python_build_paths(self):
        """The header and library directories of the running Python and of /usr/bin/python3 are found."""
        interpreters = [sys.executable]
        system_python = '/usr/bin/python3'
        # A system Python without its development package can't be used to build TAU, so skip it.
        if (os.path.exists(system_python) and os.path.realpath(system_python) != os.path.realpath(sys.executable)
                and _has_headers(system_python)):
            interpreters.append(system_python)
        for interpreter in interpreters:
            with self.subTest(interpreter=interpreter):
                include_dir, lib_dir = python_build_paths(interpreter)
                self.assertEqual(include_dir, include_dir.strip())
                self.assertEqual(lib_dir, lib_dir.strip())
                self.assertTrue(os.path.isfile(os.path.join(include_dir, 'Python.h')), include_dir)
                self.assertTrue(glob.glob(os.path.join(lib_dir, 'libpython*')), lib_dir)

    def test_python_build_paths_no_headers(self):
        """A Python without C headers, such as a distro Python without the corresponding development package, is refused."""
        # Create a fake Python interpreter and demonstrate that it produces a ConfigurationError
        # because it has no correspinding C headers.
        root = tempfile.mkdtemp(dir=os.getcwd())
        stdlib = os.path.join(root, 'lib', 'python3.99')
        include_dir = os.path.join(root, 'include', 'python3.99')
        os.makedirs(stdlib)
        os.makedirs(include_dir)
        with open(os.path.join(stdlib, 'libpython3.99.so'), 'w', encoding='utf-8'):
            pass
        interpreter = os.path.join(root, 'python3')
        with open(interpreter, 'w', encoding='utf-8') as fout:
            fout.write('#!/bin/sh\n'
                       f'case "$2" in *stdlib*) echo "{stdlib}" ;; *) echo "{include_dir}" ;; esac\n')
        os.chmod(interpreter, 0o755)
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn('Python.h', str(context.exception))
