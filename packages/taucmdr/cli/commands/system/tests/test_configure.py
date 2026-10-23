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

Functions used for unit tests of system/configure.py.
"""

import os
import tempfile
from types import SimpleNamespace
import taucmdr
from taucmdr import tests
from taucmdr.error import InternalError
from taucmdr.cf.platforms import DARWIN, LINUX
from taucmdr.cli.commands.system import configure

_HINT = 'Set the environment variable TAUCMDR_SYSTEM_PREFIX'


class ConfigureTest(tests.TestCase):
    """Tests for :any:`system.configure`."""

    def test_full_features_darwin(self):
        args = SimpleNamespace()
        darwin = configure.full_features(args, DARWIN)
        self.assertEqual(list(darwin), ['papi', 'openmp', 'mpi', 'shmem', 'cuda'])
        self.assertEqual(darwin, dict.fromkeys(darwin, False))
        linux = configure.full_features(args, LINUX)
        self.assertEqual(linux, {'papi': True, 'openmp': True, 'mpi': False, 'shmem': False, 'cuda': False})

    def test_requires_system_level(self):
        cwd = tempfile.mkdtemp(dir=tests.get_test_workdir())
        proc = tests.run_tau_subprocess(['system', 'configure', '--tau-config', 'minimal'], None, cwd, cwd)
        self.assertCleanExit(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('No system-level storage is configured.', proc.stdout + proc.stderr)
        self.assertIn(_HINT, proc.stdout + proc.stderr)
        self.assertFalse(os.path.exists(os.path.join(cwd, '.tau')))

    def test_override_tau_source(self):
        """An existing TAU installation becomes the default in a system prefix that didn't exist yet."""
        root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        cwd, user, tau_dir = (os.path.join(root, name) for name in ('cwd', 'user', 'tau'))
        for path in cwd, user, tau_dir:
            os.mkdir(path)
        system = os.path.join(root, 'newsys')
        proc = tests.run_tau_subprocess(['system', 'configure', '--tau-config', tau_dir], None, cwd, user, system)
        self.assertSucceeded(proc)
        with open(os.path.join(system, 'override_tau_source'), encoding='utf-8') as fin:
            self.assertEqual(fin.read(), tau_dir)
        self.assertEqual(os.listdir(cwd), [])

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from writing")
    def test_readonly_prefix(self):
        """Configuring a system prefix that isn't writable is an error, not a crash."""
        root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        cwd, user, tau_dir, system = (os.path.join(root, name) for name in ('cwd', 'user', 'tau', 'sys'))
        for path in cwd, user, tau_dir, system:
            os.mkdir(path)
        os.chmod(system, 0o555)
        try:
            proc = tests.run_tau_subprocess(['system', 'configure', '--tau-config', tau_dir], None, cwd, user, system)
        finally:
            os.chmod(system, 0o755)
        self.assertCleanExit(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('write', proc.stdout + proc.stderr)
        self.assertFalse(os.path.exists(os.path.join(system, 'override_tau_source')))

    def test_minimal_from_empty_directory(self):
        cwd = tempfile.mkdtemp(dir=tests.get_test_workdir())
        os.chdir(cwd)
        try:
            stdout, _ = self.assertCommandReturnValue(0, configure.COMMAND, ['--tau-config', 'minimal'])
        finally:
            os.chdir(tests.get_test_workdir())
        self.assertEqual(os.listdir(cwd), [])
        makefiles = [line.strip() for line in stdout.splitlines() if 'Makefile.tau' in line]
        self.assertTrue(makefiles, stdout)
        for makefile in makefiles:
            self.assertIn(taucmdr.SYSTEM_PREFIX, makefile)

    def test_both_nightly_names(self):
        """Configuring leaves both names of the TAU nightly archive in the system source directory."""
        root = tempfile.mkdtemp(dir=tests.get_test_workdir())
        cwd, user, tau_dir, src = (os.path.join(root, name) for name in ('cwd', 'user', 'tau', 'sys/src'))
        for path in cwd, user, tau_dir, src:
            os.makedirs(path)
        with open(os.path.join(src, 'tau-nightly-2026-01-02.tgz'), 'w', encoding='utf-8') as fout:
            fout.write('nightly')
        proc = tests.run_tau_subprocess(['system', 'configure', '--tau-config', tau_dir], None, cwd, user,
                                        os.path.dirname(src))
        self.assertSucceeded(proc)
        with open(os.path.join(src, 'tau-nightly.tgz'), encoding='utf-8') as fin:
            self.assertEqual(fin.read(), 'nightly')

    def test_reset_project_elsewhere(self):
        """Configuring refuses to delete a project outside its own working directory."""
        self.reset_project_storage(['--bare'])
        project_dir = os.path.join(os.getcwd(), '.tau')
        workdir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        with self.assertRaises(InternalError):
            configure.reset_project(workdir)
        self.assertTrue(os.path.isdir(project_dir))

    def test_help_lists_system(self):
        from taucmdr.cli.commands.__main__ import COMMAND as main_command
        from taucmdr.cli.commands.system import COMMAND as system_command
        stdout, _ = self.assertCommandReturnValue(0, main_command, ['--help'])
        self.assertIn('System Subcommands', stdout)
        self.assertIn('system', stdout)
        stdout, _ = self.assertCommandReturnValue(0, system_command, ['--help'])
        self.assertIn('configure', stdout)
