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
"""Tests for the Sphinx extension that writes the command reference."""

import importlib.util
import os
import sys
import tempfile
from unittest import mock

from taucmdr import cli, logger, tests


def _load_extension():
    path = os.path.join(tests.REPO_DIR, 'docs', '_ext', 'cli_reference.py')
    spec = importlib.util.spec_from_file_location('cli_reference', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CliReferenceTest(tests.TestCase):
    """Tests for ``docs/_ext/cli_reference.py``."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ext = _load_extension()

    def test_page_content(self):
        page = self.ext.command_page('target create')
        title, underline = page.splitlines()[:2]
        self.assertEqual(title, 'tau target create')
        self.assertEqual(underline, '=' * len(title))
        self.assertIn('--python-interpreter', page)
        self.assertIn(cli.find_command(['target', 'create']).summary, page)

    def test_no_defaults(self):
        """Pages leave out argument defaults, which depend on the host that builds the docs."""
        self.assertNotIn('- default:', self.ext.command_page('target create'))

    def test_no_help_page_placeholder(self):
        """A command without a help page gets no help block, rather than a placeholder."""
        page = self.ext.command_page('trial create')
        self.assertNotIn('No help page for', page)
        self.assertEqual(page.count('.. code-block::'), 1)

    def test_no_escape_sequences(self):
        with mock.patch.object(sys.stdout, 'isatty', return_value=True):
            for name in self.ext.command_names():
                self.assertNotIn('\x1b', self.ext.command_page(name), name)

    def test_all_commands(self):
        names = self.ext.command_names()
        self.assertEqual(names[0], '__main__')
        for name in 'system configure', 'system import', 'trial create':
            self.assertIn(name, names)
        self.assertEqual(len(names), len(cli.get_all_commands()) + 1)
        self.assertFalse([name for name in names if name.startswith('tau ')])

    def test_main_page(self):
        page = self.ext.command_page('__main__')
        self.assertTrue(page.startswith('tau\n===\n'))
        self.assertIn('<subcommand>', page)

    def test_fixed_width(self):
        """Pages don't depend on the width of the terminal running the build."""
        with mock.patch.object(logger, 'LINE_WIDTH', 40):
            narrow = self.ext.command_page('trial create')
        with mock.patch.object(logger, 'LINE_WIDTH', 200):
            wide = self.ext.command_page('trial create')
        self.assertEqual(narrow, wide)

    def test_write_pages_unchanged(self):
        """Pages whose content hasn't changed aren't rewritten, so Sphinx doesn't rebuild them."""
        with tempfile.TemporaryDirectory() as outdir:
            paths = self.ext.write_pages(outdir)
            self.assertIn(os.path.join(outdir, 'index.rst'), paths)
            mtimes = {path: os.stat(path).st_mtime_ns for path in paths}
            for path in paths:
                os.utime(path, ns=(0, 0))
            self.ext.write_pages(outdir)
            for path in paths:
                self.assertEqual(os.stat(path).st_mtime_ns, 0, path)
            self.assertEqual(len(mtimes), len(self.ext.command_names()) + 1)

    def test_write_pages_removes_stale(self):
        """A page left from a command that no longer exists is removed."""
        with tempfile.TemporaryDirectory() as outdir:
            stale = os.path.join(outdir, 'removed_command.rst')
            with open(stale, 'w', encoding='utf-8') as fout:
                fout.write('stale\n')
            self.ext.write_pages(outdir)
            self.assertFalse(os.path.exists(stale))
