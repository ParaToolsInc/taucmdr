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

Functions used for unit tests of command.py.
"""


from taucmdr import cli, tests
#from taucmdr.cli import command

class CommandTest(tests.TestCase):
    def test_command(self):
        self.assertEqual(1, 1)


class FormatUsageTest(tests.TestCase):
    """Tests for :any:`AbstractCommand.format_usage`."""

    def test_defaults_shown(self):
        self.assertIn('- default:', cli.find_command(['target', 'create']).format_usage())

    def test_defaults_omitted(self):
        usage = cli.find_command(['target', 'create']).format_usage(show_defaults=False)
        self.assertNotIn('- default:', usage)
        self.assertIn('--python-interpreter', usage)

    def test_cached_parser_unchanged(self):
        """Usage without defaults doesn't change the parser that ``--help`` uses."""
        command = cli.find_command(['target', 'create'])
        parser = command.parser
        command.format_usage(show_defaults=False)
        self.assertIs(command.parser, parser)
        self.assertIn('- default:', command.usage)
