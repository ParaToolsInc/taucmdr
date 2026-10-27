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

# Output of `<wrapper> -craype-verbose --version -E` from craype 2.7.32.
CRAYPE_GNU_CC = """gcc (GCC) 13.3.1 20240611 (Red Hat 13.3.1-2)
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

gcc -march=znver2 --version -E
"""
CRAYPE_GNU_FTN = """GNU Fortran (GCC) 13.3.1 20240611 (Red Hat 13.3.1-2)
Copyright (C) 2023 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

gfortran -march=znver2 --version -E
"""
CRAYPE_CRAY_FTN = """Cray Fortran : Version 20.0.0 (20250827170814_8a1c0a28f36ae0bf2fce3f49eb977f008b7bbf87)
Cray Fortran : Target is x86-64 : x86-rome : none
ftn_driver.exe -hcpu=x86-rome -hnetwork=ofi -hdynamic --version -E
"""
# Output of `cc -craype-verbose --version -E` when cc is GCC, which ignores -craype-verbose.
PLAIN_GCC = """cc (GCC) 8.5.0 20210514 (Red Hat 8.5.0-29)
Copyright (C) 2018 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""


def _probe_family(path, output, candidates):
    with mock.patch.dict(compiler._CompilerFamily._probe_cache, clear=True), \
         mock.patch.object(util, 'get_command_output', return_value=output):
        return compiler._CompilerFamily.probe(path, candidates)


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


class CrayFamilyTest(tests.TestCase):
    """Tests for recognizing the Cray Programming Environment's compiler wrappers."""

    def test_craype_wrappers(self):
        """craype's cc and ftn wrappers are Cray compilers, whichever compiler they wrap."""
        for path, output in (('/opt/cray/pe/craype/2.7.32/bin/cc', CRAYPE_GNU_CC),
                             ('/opt/cray/pe/craype/2.7.32/bin/ftn', CRAYPE_GNU_FTN),
                             ('/opt/cray/pe/craype/2.7.32/bin/ftn', CRAYPE_CRAY_FTN)):
            with self.subTest(path=path, output=output.splitlines()[0]):
                self.assertIs(_probe_family(path, output, [host.CRAY, host.SYSTEM]), host.CRAY)

    def test_plain_cc(self):
        """A cc that isn't a craype wrapper isn't a Cray compiler."""
        self.assertIsNot(_probe_family('/usr/bin/cc', PLAIN_GCC, [host.CRAY, host.SYSTEM]), host.CRAY)

    def test_craype_mpi_wrappers(self):
        """craype's wrappers are Cray MPI compilers."""
        self.assertIs(_probe_family('/opt/cray/pe/craype/2.7.32/bin/cc', CRAYPE_GNU_CC, [mpi.CRAY]), mpi.CRAY)
