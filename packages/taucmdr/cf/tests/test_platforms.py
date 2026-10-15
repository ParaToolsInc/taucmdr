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
"""Unit tests for taucmdr.cf.platforms"""

from taucmdr.tests import TestCase
from taucmdr.cf.platforms import Architecture, OperatingSystem, TauMagic

class PlatformsTest(TestCase):
    """Unit tests for taucmdr.cf.platforms"""

    def test_architecture_detect(self):
        self.assertTrue(Architecture.detect())

    def test_operating_system_detect(self):
        self.assertTrue(OperatingSystem.detect())

    def test_tau_magic_detect(self):
        self.assertTrue(TauMagic.detect())

    def test_supported_platforms(self):
        """Each supported host platform maps to the expected TAU magic word."""
        expected = {('x86_64', 'Linux'): 'x86_64',
                    ('x86_64', 'CNL'): 'craycnl',
                    ('x86_64', 'Darwin'): 'apple',
                    ('aarch64', 'Linux'): 'arm64_linux',
                    ('ppc64le', 'Linux'): 'ibm64linux'}
        for (arch, opsys), magic in expected.items():
            found = TauMagic.find((Architecture.find(arch), OperatingSystem.find(opsys)))
            self.assertEqual(found.name, magic, f"({arch}, {opsys})")

    def test_removed_platforms(self):
        """Architectures and operating systems that TAU Commander doesn't support aren't defined."""
        for arch in ('KNC', 'KNL', 'BGL', 'BGP', 'BGQ', 'ibm64', 'ppc64', 'aarch32'):
            with self.assertRaises(KeyError, msg=arch):
                Architecture.find(arch)
        for opsys in ('CNK', 'Android'):
            with self.assertRaises(KeyError, msg=opsys):
                OperatingSystem.find(opsys)
