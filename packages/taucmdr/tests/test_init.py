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

import os
import subprocess
import sys
from taucmdr import tests


def _import_with_version(version):
    """Import taucmdr in a new interpreter whose ``sys.version_info`` reports `version` (MAJOR, MINOR)."""
    version_info = tuple(version) + (0, 'final', 0)
    code = f"import sys; sys.version_info = {version_info!r}; import taucmdr"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    return subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=False)


class PythonVersionTest(tests.TestCase):
    """Tests for the Python version check in :py:mod:`taucmdr`."""

    def test_supported_versions(self):
        for version in ((3, 7), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16)):
            with self.subTest(version=version):
                proc = _import_with_version(version)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unsupported_versions(self):
        for version in ((2, 7), (3, 6), (3, 8), (3, 10)):
            with self.subTest(version=version):
                proc = _import_with_version(version)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn('Python 3.7 or Python 3.11 or newer is required', proc.stderr)
