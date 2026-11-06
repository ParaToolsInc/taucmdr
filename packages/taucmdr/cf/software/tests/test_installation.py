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

Functions used for unit tests of installation.py.
"""

import os
import shutil
import tempfile
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompilerSet
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, DARWIN, LINUX, X86_64, PPC64LE
from taucmdr.cf.software.installation import Installation


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

    def test_arch_and_os_specific_repos(self):
        """Repositories are looked up by target architecture, then OS, falling back to the defaults."""
        repos = {None: ['default'],
                 X86_64: {LINUX: ['x86_64-linux'], None: ['x86_64-any']}}
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=LINUX).src, 'x86_64-linux')
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=DARWIN).src, 'x86_64-any')
        self.assertEqual(_widget('download', repos=repos, arch=PPC64LE, target_os=LINUX).src, 'default')
        self.assertEqual(_widget('download', repos=repos, arch=X86_64, target_os=LINUX).srcs_avail,
                         ['x86_64-linux'])

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
        self.assertEqual(inst.srcs, [])
        self.assertEqual(inst.srcs_avail, ['/no/such/widget.tgz'])

    def test_failed_download_names_source(self):
        """A source that can't be acquired is named in the error and its hint, whatever kind of source it is."""
        url = 'http://example.com/no-such-widget.tgz'
        inst = _widget(url)
        with mock.patch.object(Installation, '_acquire_source', side_effect=OSError):
            with self.assertRaises(ConfigurationError) as ctx:
                inst.acquire_source(reuse_archive=False)
        self.assertIn(url, ctx.exception.value)
        self.assertIn(url, ctx.exception.hints[0])
