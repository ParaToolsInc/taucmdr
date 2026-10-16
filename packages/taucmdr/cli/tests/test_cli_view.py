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

Functions used for unit tests of cli_view.py.
"""

import os
import sys
from unittest import mock
import termcolor
from texttable import Texttable as PlainTexttable
from taucmdr import tests, util
from taucmdr.cli.cli_view import Texttable


def _clear_color_cache():
    """Make termcolor check the environment again.  Newer termcolor versions cache whether they can use colors."""
    can_colorize = getattr(getattr(termcolor, 'termcolor', None), 'can_colorize', None)
    if hasattr(can_colorize, 'cache_clear'):
        can_colorize.cache_clear()


def _draw(table_class, isatty):
    """Draw a small table with a header, with stdout reporting `isatty`, and colors forced on."""
    table = table_class(40)
    table.set_deco(table_class.HEADER | table_class.VLINES)
    table.header(['Name', 'Value'])
    table.add_row(['alpha', 'one'])
    env = {key: val for key, val in os.environ.items() if key not in ('NO_COLOR', 'ANSI_COLORS_DISABLED')}
    env['FORCE_COLOR'] = '1'
    _clear_color_cache()
    try:
        with mock.patch.object(sys.stdout, 'isatty', return_value=isatty), \
                mock.patch.dict(os.environ, env, clear=True):
            return table.draw(), termcolor.colored('Name', attrs=['bold'])
    finally:
        _clear_color_cache()


class TexttableTest(tests.TestCase):
    """Tests for :any:`cli_view.Texttable`, which overrides a private texttable method."""

    def test_plain_layout(self):
        """Without a terminal, the table is the same as plain texttable draws it."""
        self.assertEqual(_draw(Texttable, False)[0], _draw(PlainTexttable, False)[0])

    def test_bold_header(self):
        """On a terminal, header cells are bold and the layout is otherwise unchanged."""
        drawn, bold_name = _draw(Texttable, True)
        self.assertNotEqual(bold_name, 'Name', "termcolor didn't use colors")
        self.assertIn(bold_name, drawn.splitlines()[0])
        self.assertEqual(util.uncolor_text(drawn), _draw(PlainTexttable, False)[0])
