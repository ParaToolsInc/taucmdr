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

Functions used for unit tests of host.py.
"""


from unittest import mock
from taucmdr import tests, util
from taucmdr.cf import compiler
from taucmdr.cf.compiler import host, mpi
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.platforms import TAU_PPC64LE_LINUX


class FamilyOrderTest(tests.TestCase):
    """Tests for the order in which host compiler families are searched."""

    def test_system_family_last(self):
        """The generic System family is searched after every named family, but the preferred family is first."""
        with mock.patch('taucmdr.cf.platforms.HOST_TAU_MAGIC', TAU_PPC64LE_LINUX):
            families = list(host.HOST_COMPILERS.iterfamilies())
        self.assertIs(families[0], host.IBM)
        self.assertIs(families[-1], host.SYSTEM)
        self.assertEqual(len(families), len(host.HOST_COMPILERS.families))

    def test_mpi_family_order(self):
        """MPI compiler families are searched in definition order after the preferred family."""
        with mock.patch('taucmdr.cf.platforms.HOST_TAU_MAGIC', TAU_PPC64LE_LINUX):
            families = list(mpi.MPI_COMPILERS.iterfamilies())
        expected = [family for family in mpi.MPI_COMPILERS.families.values() if family is not mpi.IBM]
        self.assertEqual(families, [mpi.IBM] + expected)

    @tests.skipUnless(util.which('cc') and util.which('gcc'), "cc and gcc required for this test")
    def test_find_any_without_preferred_family(self):
        """Without the preferred family installed, a named family's C compiler is found before the System family's."""
        with mock.patch('taucmdr.cf.platforms.HOST_TAU_MAGIC', TAU_PPC64LE_LINUX):
            host_cc = compiler.InstalledCompiler.find_any(CC)
        self.assertIsNot(host_cc.info.family, host.SYSTEM)
