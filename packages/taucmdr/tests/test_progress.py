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
"""Tests for progress.py."""

import io
import re
from unittest import mock
from taucmdr import logger, progress, tests, util


class ProgressIndicatorTest(tests.TestCase):
    """Tests for :any:`progress.ProgressIndicator`."""

    def _draw(self, width, load, count):
        """Return the download progress as would be drawn on a terminal `width` characters wide."""
        out = io.StringIO()
        with mock.patch.object(logger, 'LINE_WIDTH', width), \
                mock.patch.object(progress, 'load_average', return_value=load), \
                mock.patch('sys.stdout', new=out):
            with progress.ProgressIndicator('Downloading', total_size=1000, auto_refresh=0) as indicator:
                indicator.update(count=count)
        return [line for line in re.split('[\r\n]', util.uncolor_text(out.getvalue())) if line]

    def test_line_width(self):
        for width in range(30, 160):
            for load in (None, 0.5, 1.0):
                for count in (0, 745, 1000):
                    with self.subTest(width=width, load=load, count=count):
                        for line in self._draw(width, load, count):
                            self.assertEqual(len(line), len(logger.LINE_MARKER) + width, line)
