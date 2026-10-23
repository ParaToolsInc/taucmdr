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

Functions used for unit tests of system/fetch.py.
"""

import datetime
import filecmp
import os
import tarfile
import tempfile
from unittest import mock
from taucmdr import tests
from taucmdr.cli.commands.system import fetch


def make_archive(path, toplevel='pkg-1.0', size=0):
    """Write a gzipped tar archive rooted in `toplevel` to `path`, and return `path`.

    The archive holds a README and, if `size` is given, that many bytes of random data.
    """
    root = tempfile.mkdtemp(dir=tests.get_test_workdir())
    os.mkdir(os.path.join(root, toplevel))
    with open(os.path.join(root, toplevel, 'README'), 'w', encoding='utf-8') as fout:
        fout.write(path)
    if size:
        with open(os.path.join(root, toplevel, 'data.bin'), 'wb') as fout:
            fout.write(os.urandom(size))
    with tarfile.open(path, 'w:gz') as archive:
        archive.add(os.path.join(root, toplevel), arcname=toplevel)
    return path


class FetchTest(tests.TestCase):
    """Tests for :any:`system.fetch`."""

    def setUp(self):
        super().setUp()
        self.mirror = tempfile.mkdtemp(dir=tests.get_test_workdir())
        self.dest = os.path.join(tempfile.mkdtemp(dir=tests.get_test_workdir()), 'bundle')

    def _archive(self, name):
        return 'file://' + make_archive(os.path.join(self.mirror, name))

    def test_fetch_all(self):
        sources = {name: [self._archive(name)] for name in ('tau.tgz', 'pdt.tgz', 'tau-nightly.tgz')}
        self.assertEqual(fetch.fetch_sources(self.dest, sources), [])
        dated = datetime.datetime.now().strftime('tau-nightly-%Y-%m-%d.tgz')
        self.assertEqual(sorted(os.listdir(self.dest)), sorted([*sources, dated]))
        self.assertTrue(filecmp.cmp(os.path.join(self.dest, 'tau-nightly.tgz'), os.path.join(self.dest, dated),
                                    shallow=False))

    def test_fetch_mirror_fallback(self):
        missing = 'file://' + os.path.join(self.mirror, 'missing', 'tau.tgz')
        sources = {'tau.tgz': [missing, self._archive('tau.tgz')]}
        self.assertEqual(fetch.fetch_sources(self.dest, sources), [])
        self.assertEqual(os.listdir(self.dest), ['tau.tgz'])

    def test_fetch_rejects_non_archive(self):
        """A mirror that answers with an error page counts as a failed mirror."""
        error_dir = os.path.join(self.mirror, 'error')
        os.mkdir(error_dir)
        with open(os.path.join(error_dir, 'tau.tgz'), 'w', encoding='utf-8') as fout:
            fout.write('<html><body>404 Not Found</body></html>')
        error_page = 'file://' + os.path.join(error_dir, 'tau.tgz')
        self.assertEqual(fetch.fetch_sources(self.dest, {'tau.tgz': [error_page, self._archive('tau.tgz')]}), [])
        self.assertTrue(tarfile.is_tarfile(os.path.join(self.dest, 'tau.tgz')))
        dest = self.dest + '-only-error'
        self.assertEqual(fetch.fetch_sources(dest, {'tau.tgz': [error_page]}), ['tau.tgz'])
        self.assertEqual(os.listdir(dest), [])

    def test_fetch_keeps_good_archive(self):
        """Fetching again keeps an archive that's already there, even if no mirror answers."""
        os.makedirs(self.dest)
        existing = make_archive(os.path.join(self.dest, 'tau.tgz'))
        with open(existing, 'rb') as fin:
            before = fin.read()
        missing = 'file://' + os.path.join(self.mirror, 'missing', 'tau.tgz')
        self.assertEqual(fetch.fetch_sources(self.dest, {'tau.tgz': [missing]}), [])
        with open(existing, 'rb') as fin:
            self.assertEqual(fin.read(), before)
        self.assertEqual(os.listdir(self.dest), ['tau.tgz'])

    def test_fetch_reports_failures(self):
        missing = 'file://' + os.path.join(self.mirror, 'missing', 'pdt.tgz')
        sources = {'tau.tgz': [self._archive('tau.tgz')], 'pdt.tgz': [missing]}
        self.assertEqual(fetch.fetch_sources(self.dest, sources), ['pdt.tgz'])
        self.assertEqual(os.listdir(self.dest), ['tau.tgz'])
        dest = self.dest + '-command'
        with mock.patch.object(fetch, 'all_sources', return_value=sources):
            retval, stdout, stderr = self.exec_command(fetch.COMMAND, [dest])
        self.assertNotEqual(retval, 0)
        self.assertIn('pdt.tgz', stdout + stderr)
        self.assertTrue(os.path.exists(os.path.join(dest, 'tau.tgz')))
