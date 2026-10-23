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

Functions used for unit tests of system/import.py.
"""

import datetime
import importlib
import os
import shutil
import stat
import tempfile
from types import SimpleNamespace
from unittest import mock
from taucmdr import tests, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompilerSet
from taucmdr.cf.compiler.host import CC, CXX, GNU
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS
from taucmdr.cf.software import installation
from taucmdr.cf.software.sqlite3_installation import Sqlite3Installation
from taucmdr.cf.software.tau_installation import NIGHTLY, TauInstallation
from taucmdr.cli.commands.system.tests.test_fetch import make_archive

# The module is named after the command, which is a Python keyword.
import_cmd = importlib.import_module('taucmdr.cli.commands.system.import')


class ImportTest(tests.TestCase):
    """Tests for :any:`system.import`."""

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        self.bundle = os.path.join(self.root, 'bundle')
        self.system = os.path.join(self.root, 'sys')
        self.src = os.path.join(self.system, 'src')
        os.mkdir(self.bundle)
        self._readonly = []

    def tearDown(self):
        for path in self._readonly:
            os.chmod(path, stat.S_IRWXU)
        super().tearDown()

    def _bundle(self, *names):
        for name in names:
            make_archive(os.path.join(self.bundle, name))

    def _tau_import(self):
        user = os.path.join(self.root, 'user')
        os.makedirs(user, exist_ok=True)
        return tests.run_tau_subprocess(['system', 'import', self.bundle], None, self.root, user, self.system)

    def test_import_copies_archives(self):
        self._bundle('tau.tgz', 'pdt_lite.tgz')
        with open(os.path.join(self.bundle, 'notes.txt'), 'w', encoding='utf-8') as fout:
            fout.write('notes')
        proc = self._tau_import()
        self.assertSucceeded(proc)
        self.assertEqual(sorted(os.listdir(self.src)), ['pdt_lite.tgz', 'tau.tgz'])
        self.assertIn('notes.txt', proc.stdout + proc.stderr)

    def test_import_skips_identical(self):
        self._bundle('tau.tgz')
        self.assertEqual(import_cmd.import_sources(self.bundle, self.src), ['tau.tgz'])
        self.assertEqual(import_cmd.import_sources(self.bundle, self.src), [])

    def test_import_keeps_different_file(self):
        self._bundle('tau.tgz', 'pdt.tgz')
        os.makedirs(self.src)
        existing = make_archive(os.path.join(self.src, 'tau.tgz'), toplevel='other-1.0')
        with open(existing, 'rb') as fin:
            before = fin.read()
        proc = self._tau_import()
        self.assertSucceeded(proc)
        with open(existing, 'rb') as fin:
            self.assertEqual(fin.read(), before)
        self.assertTrue(os.path.exists(os.path.join(self.src, 'pdt.tgz')))
        self.assertIn('tau.tgz', proc.stdout + proc.stderr)

    def test_import_rejects_corrupt_archive(self):
        """A truncated archive stops the import before anything is copied."""
        self._bundle('tau.tgz')
        path = make_archive(os.path.join(self.bundle, 'pdt.tgz'), size=512 * 1024)
        with open(path, 'r+b') as fout:
            fout.truncate(os.path.getsize(path) * 3 // 4)
        proc = self._tau_import()
        self.assertCleanExit(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('pdt.tgz', proc.stdout + proc.stderr)
        self.assertFalse(os.path.exists(self.src) and os.listdir(self.src))

    def test_import_copy_failure(self):
        """A copy that fails partway leaves nothing under the archive's name in the source directory."""
        self._bundle('tau.tgz')

        def copy_part(source, target):
            with open(target, 'wb') as fout:
                fout.write(b'part')
            raise OSError(28, 'No space left on device')

        with mock.patch.object(import_cmd.shutil, 'copy2', side_effect=copy_part), \
             self.assertRaises(ConfigurationError):
            import_cmd.import_sources(self.bundle, self.src)
        self.assertEqual(os.listdir(self.src), [])

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from writing")
    def test_import_readonly_prefix(self):
        """Importing into a system prefix that isn't writable is an error, not a crash."""
        self._bundle('tau.tgz')
        os.makedirs(self.system)
        os.chmod(self.system, 0o555)
        self._readonly.append(self.system)
        proc = self._tau_import()
        self.assertCleanExit(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('write', proc.stdout + proc.stderr)

    def test_import_adds_dated_nightly(self):
        self._bundle('tau-nightly.tgz')
        dated = datetime.datetime.now().strftime('tau-nightly-%Y-%m-%d.tgz')
        self.assertEqual(sorted(import_cmd.import_sources(self.bundle, self.src)), [dated, 'tau-nightly.tgz'])
        self.assertEqual(sorted(os.listdir(self.src)), [dated, 'tau-nightly.tgz'])

    def test_import_refused_names(self):
        """Only known source archives are imported."""
        self._bundle('tau.tgz')
        make_archive(os.path.join(self.bundle, 'unknown.tgz'))
        self.assertEqual(import_cmd.import_sources(self.bundle, self.src), ['tau.tgz'])
        self.assertEqual(os.listdir(self.src), ['tau.tgz'])

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from renaming files")
    def test_readonly_nightly_not_renamed(self):
        """A TAU nightly build uses a read-only source directory that holds both nightly names."""
        os.makedirs(self.src)
        make_archive(os.path.join(self.src, 'tau-nightly.tgz'), toplevel='tau-2.35')
        shutil.copy(os.path.join(self.src, 'tau-nightly.tgz'), os.path.join(self.src, 'tau-nightly-2026-01-02.tgz'))
        os.chmod(self.src, 0o555)
        self._readonly.append(self.src)
        tau = TauInstallation.__new__(TauInstallation)
        tau.name, tau.title, tau.src, tau.srcs, tau.srcs_avail = 'tau', 'TAU', NIGHTLY, [], [NIGHTLY]
        tau.unmanaged, tau.update_nightly, tau._install_tag = False, False, None  # pylint: disable=protected-access
        with mock.patch.object(installation, 'search_levels', return_value=[SimpleNamespace(prefix=self.system)]):
            tag = tau._get_install_tag()  # pylint: disable=protected-access
        self.assertEqual(tag, 'tau-2.35-2026-01-02')
        self.assertEqual(tau.src, os.path.join(self.src, 'tau-nightly-2026-01-02.tgz'))
        self.assertEqual(sorted(os.listdir(self.src)), ['tau-nightly-2026-01-02.tgz', 'tau-nightly.tgz'])

    def test_offline_acquire(self):
        """An installer uses an imported archive without downloading anything."""
        name = 'sqlite-autoconf-3210000.tar.gz'
        self._bundle(name)
        import_cmd.import_sources(self.bundle, self.src)
        found = GNU.installation()
        compilers = InstalledCompilerSet('offline', Host_CC=found[CC], Host_CXX=found[CXX])
        inst = Sqlite3Installation({'sqlite3': 'download'}, HOST_ARCH, HOST_OS, compilers)
        with mock.patch.object(installation, 'search_levels', return_value=[SimpleNamespace(prefix=self.system)]), \
             mock.patch.object(util, 'download', side_effect=OSError('offline')) as download:
            self.assertEqual(inst.acquire_source(), os.path.join(self.src, name))
        download.assert_not_called()
