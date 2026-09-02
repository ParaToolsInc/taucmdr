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

Functions used for unit tests of tau_installation.py.
"""

import os
import tempfile
from taucmdr import tests
from taucmdr.cf.software.tau_installation import TauInstallation


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


class TauVersionTest(tests.TestCase):
    """Tests for TauInstallation.get_tau_version() header parsing."""

    def setUp(self):
        super().setUp()
        self._prefix = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._prefix, ignore_errors=True)
        super().tearDown()

    def _write_header(self, *lines):
        """Write include/TAU.h.default under the per-test install prefix."""
        inc = os.path.join(self._prefix, 'include')
        os.makedirs(inc, exist_ok=True)
        with open(os.path.join(inc, 'TAU.h.default'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

    def _fake_self(self):
        class _FakeSelf:
            pass
        fs = _FakeSelf()
        fs.install_prefix = self._prefix
        return fs

    def test_release_version(self):
        """Plain release string parses to a tuple of ints."""
        self._write_header('#ifndef TAU_H_DEFAULT', '#define TAU_VERSION "2.33.2"', '#endif')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 33, 2))

    def test_git_suffix_stripped(self):
        """Nightly builds carry a -git suffix that must not break parsing."""
        self._write_header('#define TAU_VERSION "2.35.1-git"')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 35, 1))

    def test_two_component_version(self):
        """Major.minor only is a valid, comparable tuple."""
        self._write_header('#define TAU_VERSION "2.32"')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 32))

    def test_missing_header_returns_none(self):
        """No TAU.h.default under the prefix: returns None instead of raising."""
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_header_without_version_returns_none(self):
        """Header present but no TAU_VERSION define: returns None."""
        self._write_header('#define TAU_MAX_THREADS 128')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_malformed_version_returns_none(self):
        """Non-numeric version string is swallowed and reported as None."""
        self._write_header('#define TAU_VERSION "unknown"')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_unquoted_version_returns_none(self):
        """Define without quotes cannot be split on '"' and is reported as None."""
        self._write_header('#define TAU_VERSION 2.33.2')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))
