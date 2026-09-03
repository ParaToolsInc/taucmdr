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

Functions used for unit tests of target.py.
"""

import os
from unittest import mock
from taucmdr import tests
from taucmdr.model import target
from taucmdr.model.target import tau_source_default


class TauSourceDefaultTest(tests.TestCase):
    """Tests for the system-wide TAU source override file."""

    @staticmethod
    def _override(contents):
        """Patch the override file read in tau_source_default() to return `contents`."""
        return mock.patch('taucmdr.model.target.open', mock.mock_open(read_data=contents), create=True)

    def test_download_without_override_file(self):
        """No override file: managed TAU is downloaded."""
        with mock.patch('taucmdr.model.target.open', side_effect=FileNotFoundError, create=True):
            self.assertEqual(tau_source_default(), 'download')

    def test_existing_directory_used(self):
        """The override file names an accessible directory: that TAU is used, whitespace stripped."""
        with self._override(f'  {os.getcwd()}\n'):
            self.assertEqual(tau_source_default(), os.getcwd())

    def test_inaccessible_path_warns_and_downloads(self):
        """The override file names a missing directory: warn, naming the path, and download instead."""
        with self._override('/no/such/tau\n'):
            with self.assertLogs(target.LOGGER, level='WARNING') as logs:
                self.assertEqual(tau_source_default(), 'download')
        self.assertIn('/no/such/tau', logs.output[0])
