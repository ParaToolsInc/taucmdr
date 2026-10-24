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

Functions used for unit tests of :any:`taucmdr.cf.software.all_sources`.
"""

import importlib
import os
import pkgutil
from taucmdr import tests
from taucmdr.cf import software


def _repos_urls(repos):
    """Yield every URL in an installer's nested ``REPOS`` dictionary."""
    for value in repos.values():
        if isinstance(value, dict):
            yield from _repos_urls(value)
        else:
            yield from value


class AllSourcesTest(tests.TestCase):
    """Tests for :any:`taucmdr.cf.software.all_sources`."""

    def test_every_installer_covered(self):
        urls = {url for mirrors in software.all_sources().values() for url in mirrors}
        names = [info.name for info in pkgutil.iter_modules(software.__path__) if info.name.endswith('_installation')]
        self.assertGreaterEqual(len(names), 12)
        for name in names:
            module = importlib.import_module(f'{software.__name__}.{name}')
            for url in _repos_urls(getattr(module, 'REPOS', None) or {}):
                with self.subTest(installer=name, url=url):
                    self.assertIn(url, urls)

    def test_no_obsolete_ompt(self):
        """Archives for OMPT versions TAU no longer supports are not listed."""
        sources = software.all_sources()
        for name in ('LLVM-openmp-ompt-tr6.tar.gz', 'LLVM-openmp-0.2.tar.gz'):
            with self.subTest(name=name):
                self.assertNotIn(name, sources)

    def test_platform_variants(self):
        """Archives used only on some platforms are included, and each name's URLs all end in that name."""
        sources = software.all_sources()
        for name in ('pdt.tgz', 'pdt_lite.tgz', 'libunwind-1.8.1.tar.gz', 'libunwind-1.3-rc1.tar.gz',
                     'LLVM-openmp-8.0.tar.gz', 'tau.tgz', 'tau-nightly.tgz'):
            with self.subTest(name=name):
                self.assertIn(name, sources)
        for name, mirrors in sources.items():
            with self.subTest(name=name):
                self.assertTrue(mirrors)
                self.assertEqual(len(mirrors), len(set(mirrors)))
                self.assertTrue(all(os.path.basename(url) == name for url in mirrors))
