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

Functions used for unit tests of pdt_installation.py.
"""

from taucmdr.tests import TestCase, not_implemented
from taucmdr.cf.platforms import ARM64, X86_64, DARWIN, LINUX, CRAY_CNL
from taucmdr.cf.software import pdt_installation
from taucmdr.cf.software.pdt_installation import PdtInstallation
from taucmdr.cf.software.tau_installation import TauInstallation

@not_implemented
class PdtInstallationTest(TestCase):
    pass


class PdtCommandsTest(TestCase):
    """Tests for the PDT command lists of each platform."""

    def _verify_commands(self, arch, opsys):
        compilers = TauInstallation.get_minimal().compilers
        return PdtInstallation({'pdt': 'download'}, arch, opsys, compilers).verify_commands

    def test_commands_new_platforms(self):
        self.assertEqual(self._verify_commands(ARM64, DARWIN), pdt_installation.COMMANDS[X86_64][DARWIN])
        self.assertEqual(self._verify_commands(ARM64, CRAY_CNL), pdt_installation.COMMANDS[ARM64][LINUX])

    def test_commands_edg4101_wrappers(self):
        """Platforms with PDT's EDG 4.10.1 front end expect the x4101 wrapper names."""
        # PDT's configure installs cparse4101 and cxxparse4101 wherever it ships edgcpfe4101.
        for arch, by_os in pdt_installation.COMMANDS.items():
            if arch is None:
                continue
            for opsys, commands in by_os.items():
                if 'edgcpfe4101' in commands:
                    self.assertLessEqual({'cparse4101', 'cxxparse4101'}, set(commands), (arch.name, opsys.name))
