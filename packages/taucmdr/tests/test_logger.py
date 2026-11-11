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

Functions used for unit tests of logger.py.
"""

import os
from unittest import mock
from taucmdr import logger, tests


class TerminalSizeTest(tests.TestCase):
    """Tests for :any:`logger.get_terminal_size`."""

    def _size(self, env, detected=None):
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(logger, '_get_term_size_posix', return_value=detected), \
             mock.patch.object(logger, '_get_term_size_windows', return_value=detected), \
             mock.patch.object(logger, '_get_term_size_tput', return_value=detected):
            return logger.get_terminal_size()

    def test_columns_and_lines(self):
        self.assertEqual(self._size({'COLUMNS': '160', 'LINES': '50'}), (160, 50))

    def test_columns_alone(self):
        self.assertEqual(self._size({'COLUMNS': '160'}), (160, 25))
        self.assertEqual(self._size({'COLUMNS': '160'}, detected=(100, 40)), (160, 40))

    def test_lines_alone(self):
        self.assertEqual(self._size({'LINES': '50'}), (80, 50))
        self.assertEqual(self._size({'LINES': '50'}, detected=(100, 40)), (100, 50))

    def test_invalid(self):
        self.assertEqual(self._size({'COLUMNS': 'wide', 'LINES': '50'}, detected=(100, 40)), (100, 50))
