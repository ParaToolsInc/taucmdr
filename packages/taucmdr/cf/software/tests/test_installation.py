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

Functions used for unit tests of installation.py.
"""

import os
import multiprocessing
import shutil
import stat
import tempfile
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompilerSet
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, DARWIN, LINUX, X86_64, PPC64LE
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software import installation
from taucmdr.cf.software.installation import Installation, parallel_make_flags


_REPOS = ['http://example.com/widget.tgz', 'http://mirror.example.com/widget.tgz']


def _widget(src, repos=None, commands=None, libraries=None, headers=None, arch=HOST_ARCH, target_os=HOST_OS):
    """Build a bare Installation for a package named 'widget' without touching any storage level."""
    return Installation('widget', 'Widget', {'widget': src}, arch, target_os,
                        InstalledCompilerSet('test-compilers'), repos, commands, libraries, headers)


class InstallationSourceTest(tests.TestCase):
    """Tests for how Installation resolves the package source given at construction."""

    def test_download_uses_repo_list(self):
        """'download' takes the first repository and keeps the rest as fallbacks."""
        inst = _widget('download', repos={None: _REPOS})
        self.assertEqual(inst.src, _REPOS[0])
        self.assertEqual(inst.srcs, _REPOS[1:])
        self.assertEqual(inst.srcs_avail, _REPOS)
        self.assertFalse(inst.unmanaged)

    def test_download_keyword_is_case_insensitive(self):
        """'DOWNLOAD' works like 'download'."""
        inst = _widget('DOWNLOAD', repos={None: _REPOS})
        self.assertEqual(inst.src, _REPOS[0])

    def test_download_single_repo_string(self):
        """A single repository string is a source with no fallbacks."""
        inst = _widget('download', repos={None: _REPOS[0]})
        self.assertEqual(inst.src, _REPOS[0])
        self.assertEqual(inst.srcs, [])
        self.assertEqual(inst.srcs_avail, [_REPOS[0]])

    def test_download_without_repos_rejected(self):
        """An empty repository list cannot be downloaded from."""
        with self.assertRaises(ConfigurationError):
            _widget('download', repos={None: []})

    def test_tr4_tr6_rejected(self):
        """The retired OMPT TR4/TR6 keywords are not valid sources for any package."""
        for src in ('download-tr4', 'download-tr6', 'Download-TR6'):
            with self.assertRaises(ConfigurationError):
                _widget(src, repos={None: _REPOS})

    def test_arch_and_os_specific_repos(self):
        """Repositories are looked up by target architecture, then OS, falling back to the defaults."""
        repos = {None: ['default'],
                 X86_64: {LINUX: ['x86_64-linux'], None: ['x86_64-any']}}
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=LINUX).src, 'x86_64-linux')
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=DARWIN).src, 'x86_64-any')
        self.assertEqual(_widget('download', repos=repos, arch=PPC64LE, target_os=LINUX).src, 'default')
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=LINUX).srcs_avail,
                         ['x86_64-linux'])

    def test_no_lists_means_nothing_to_verify(self):
        """Packages without commands, libraries, or headers verify nothing beyond the prefix."""
        inst = _widget('download', repos={None: _REPOS})
        self.assertEqual(inst.verify_commands, [])
        self.assertEqual(inst.verify_libraries, [])
        self.assertEqual(inst.verify_headers, [])

    def test_existing_directory_is_unmanaged(self):
        """A directory is an existing installation: unmanaged, and used as the install prefix."""
        prefix = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, prefix, ignore_errors=True)
        inst = _widget(prefix)
        self.assertTrue(inst.unmanaged)
        self.assertEqual(inst.srcs, [])
        self.assertEqual(inst.srcs_avail, [prefix])
        self.assertEqual(inst.install_prefix, prefix)
        self.assertEqual(inst.bin_path, os.path.join(prefix, 'bin'))
        self.assertEqual(inst.lib_path, os.path.join(prefix, 'lib'))
        self.assertEqual(inst.include_path, os.path.join(prefix, 'include'))

    def test_archive_path_is_managed(self):
        """A path that is not a directory (an archive) still has to be installed."""
        inst = _widget('/no/such/widget.tgz')
        self.assertFalse(inst.unmanaged)
        self.assertEqual(inst.src, '/no/such/widget.tgz')
        self.assertEqual(inst.srcs_avail, ['/no/such/widget.tgz'])


class InstallationVerifyTest(tests.TestCase):
    """Tests for verify() against a fabricated installation prefix."""

    def setUp(self):
        super().setUp()
        self._prefix = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._prefix, ignore_errors=True)

    def _touch(self, *parts, executable=False):
        path = os.path.join(self._prefix, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8'):
            pass
        if executable:
            os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path

    def _widget(self, commands=(), libraries=(), headers=()):
        return _widget(self._prefix,
                       commands={None: list(commands)},
                       libraries={None: list(libraries)},
                       headers={None: list(headers)})

    def test_complete_installation_verifies(self):
        """Executable commands, libraries, and headers in the usual places pass."""
        self._touch('bin', 'widget-cli', executable=True)
        self._touch('lib', 'libwidget.so')
        self._touch('include', 'widget.h')
        self._widget(['widget-cli'], ['libwidget.so'], ['widget.h']).verify()

    def test_missing_prefix_rejected(self):
        """The prefix itself must exist."""
        inst = self._widget()
        shutil.rmtree(self._prefix)
        with self.assertRaises(SoftwarePackageError):
            inst.verify()

    def test_missing_command_rejected(self):
        """A missing command fails verification."""
        with self.assertRaises(SoftwarePackageError) as ctx:
            self._widget(['widget-cli']).verify()
        self.assertIn('is missing', str(ctx.exception))

    def test_non_executable_command_rejected(self):
        """A command that exists but is not executable fails verification."""
        self._touch('bin', 'widget-cli')
        with self.assertRaises(SoftwarePackageError) as ctx:
            self._widget(['widget-cli']).verify()
        self.assertIn('not executable', str(ctx.exception))

    def test_library_in_lib64_accepted(self):
        """Distributions that install into lib64 (e.g. SuSE) pass."""
        self._touch('lib64', 'libwidget.so')
        self._widget(libraries=['libwidget.so']).verify()

    def test_missing_library_rejected(self):
        """A library missing from lib and lib64 fails verification."""
        with self.assertRaises(SoftwarePackageError) as ctx:
            self._widget(libraries=['libwidget.so']).verify()
        self.assertIn('not accessible', str(ctx.exception))

    def test_dylib_accepted_on_darwin(self):
        """On Darwin a .so listed for verification may exist as a .dylib instead."""
        self._touch('lib', 'libwidget.dylib')
        inst = self._widget(libraries=['libwidget.so'])
        with mock.patch.object(installation, 'HOST_OS', DARWIN):
            inst.verify()
        with mock.patch.object(installation, 'HOST_OS', LINUX):
            with self.assertRaises(SoftwarePackageError):
                inst.verify()

    def test_dylib_fallback_only_for_shared_objects(self):
        """A static library is never satisfied by a .dylib, even on Darwin."""
        self._touch('lib', 'libwidget.dylib')
        inst = self._widget(libraries=['libwidget.a'])
        with mock.patch.object(installation, 'HOST_OS', DARWIN):
            with self.assertRaises(SoftwarePackageError):
                inst.verify()

    def test_missing_header_rejected(self):
        """A missing header fails verification."""
        self._touch('include', 'widget.h')
        with self.assertRaises(SoftwarePackageError):
            self._widget(headers=['widget.h', 'widget_config.h']).verify()


class InstallationEnvironmentTest(tests.TestCase):
    """Tests for the compile-time and runtime environments an installation contributes."""

    def setUp(self):
        super().setUp()
        self._prefix = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._prefix, ignore_errors=True)

    def test_bin_and_lib_paths_prepended(self):
        """PATH and the loader path start with the installation's directories."""
        os.makedirs(os.path.join(self._prefix, 'bin'))
        os.makedirs(os.path.join(self._prefix, 'lib'))
        inst = _widget(self._prefix)
        library_path = 'DYLD_LIBRARY_PATH' if HOST_OS is DARWIN else 'LD_LIBRARY_PATH'
        opts, env = inst.compiletime_config(['-O2'], {'PATH': '/usr/bin', library_path: '/usr/lib'})
        self.assertEqual(opts, ['-O2'])
        self.assertEqual(env['PATH'], os.pathsep.join([inst.bin_path, '/usr/bin']))
        self.assertEqual(env[library_path], '/usr/lib')
        opts, env = inst.runtime_config(None, {'PATH': '/usr/bin', library_path: '/usr/lib'})
        self.assertEqual(opts, [])
        self.assertEqual(env['PATH'], os.pathsep.join([inst.bin_path, '/usr/bin']))
        self.assertEqual(env[library_path], os.pathsep.join([inst.lib_path, '/usr/lib']))

    def test_paths_created_when_absent(self):
        """Without a PATH or loader path in the environment the installation's directories become them."""
        os.makedirs(os.path.join(self._prefix, 'bin'))
        os.makedirs(os.path.join(self._prefix, 'lib'))
        inst = _widget(self._prefix)
        library_path = 'DYLD_LIBRARY_PATH' if HOST_OS is DARWIN else 'LD_LIBRARY_PATH'
        _, env = inst.compiletime_config(env={'HOME': '/h'})
        self.assertEqual(env['PATH'], inst.bin_path)
        _, env = inst.runtime_config(env={'HOME': '/h'})
        self.assertEqual(env['PATH'], inst.bin_path)
        self.assertEqual(env[library_path], inst.lib_path)

    def test_missing_directories_leave_environment_alone(self):
        """An installation without bin or lib directories changes nothing."""
        inst = _widget(self._prefix)
        env = {'PATH': '/usr/bin'}
        self.assertEqual(inst.compiletime_config(env=env)[1], env)
        self.assertEqual(inst.runtime_config(env=env)[1], env)


class ParallelMakeFlagsTest(tests.TestCase):
    """Tests for the make -j flags."""

    def test_explicit_count(self):
        """An explicit job count is used as-is."""
        self.assertEqual(parallel_make_flags(4), ['-j', '4'])

    def test_environment_override(self):
        """__TAUCMDR_MAX_MAKE_JOBS__ sets the job count."""
        with mock.patch.dict(os.environ, {'__TAUCMDR_MAX_MAKE_JOBS__': '3'}):
            self.assertEqual(parallel_make_flags(), ['-j', '3'])

    def test_invalid_environment_override(self):
        """A non-positive count is an error; a non-numeric one falls back to the default."""
        with mock.patch.dict(os.environ, {'__TAUCMDR_MAX_MAKE_JOBS__': '0'}):
            with self.assertRaises(ConfigurationError):
                parallel_make_flags()
        with mock.patch.dict(os.environ, {'__TAUCMDR_MAX_MAKE_JOBS__': 'lots'}):
            self.assertEqual(parallel_make_flags(), ['-j', str(max(1, multiprocessing.cpu_count() - 1))])

    def test_default_leaves_one_core_free(self):
        """Without an override, all but one core are used."""
        env = {key: val for key, val in os.environ.items() if key != '__TAUCMDR_MAX_MAKE_JOBS__'}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(parallel_make_flags(), ['-j', str(max(1, multiprocessing.cpu_count() - 1))])
