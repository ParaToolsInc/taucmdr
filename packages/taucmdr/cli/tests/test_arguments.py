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

Functions used for unit tests of arguments.py.
"""

import os
from unittest import mock
from taucmdr import tests
from taucmdr.cli import arguments


def _help_text(description=None):
    """Return the help text of a parser with a positional argument, an option and two more groups."""
    parser = arguments.get_parser(prog='tau example', description=description)
    parser.add_argument('target', help="target to use")
    parser.add_argument('--flag', help="turn the flag on", action='store_true')
    parser.add_argument_group('zebra arguments').add_argument('--zebra', help="a zebra option")
    parser.add_argument_group('apple arguments').add_argument('--apple', help="an apple option")
    return parser.format_help()


class ArgumentsTest(tests.TestCase):
    """Tests for :py:mod:`taucmdr.cli.arguments`."""

    def test_group_order(self):
        """Help lists positional arguments, then options, then the other groups alphabetically."""
        headings = [line for line in _help_text().splitlines() if line.endswith(':') and not line.startswith(' ')]
        self.assertEqual(headings, ['Positional Arguments:', 'Options:', 'Apple Arguments:', 'Zebra Arguments:'])

    def test_no_argparse_colors(self):
        """Help text has no colors from argparse itself, even where argparse would add them."""
        env = {key: val for key, val in os.environ.items() if key not in ('NO_COLOR', 'PYTHON_COLORS')}
        env['FORCE_COLOR'] = '1'
        with mock.patch.dict(os.environ, env, clear=True):
            text = _help_text(description="See `tau help` for more.")
        self.assertNotIn('\x1b[', text)
        self.assertIn('See `tau help` for more.', text)
