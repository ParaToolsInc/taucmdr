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

Functions used for unit tests of shmem.py.
"""

import os
import unittest
from taucmdr import tests, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompiler
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import SYSTEM, MPI_CC
from taucmdr.cf.compiler.shmem import OPENSHMEM, SHMEM_CC

_GCC = util.which('gcc')


class OpenSHMEMWrapperTest(tests.TestCase):
    """Tests for probing OpenSHMEM compiler wrappers."""

    def _make_compiler(self, name, script):
        dirname = os.path.join(tests.get_test_workdir(), self.id())
        os.makedirs(dirname)
        path = os.path.join(dirname, name)
        with open(path, 'w', encoding='utf-8') as fout:
            fout.write('#!/bin/sh\n' + script)
        os.chmod(path, 0o755)
        return path

    @unittest.skipUnless(_GCC, "gcc not found")
    def test_showme_wrapper(self):
        """An Open MPI style wrapper that accepts -showme reports its include and library paths."""
        path = self._make_compiler('oshcc', (
            'if [ "$1" = "-showme" ]; then\n'
            '  echo "%s -I/fake/openmpi/include -L/fake/openmpi/lib -loshmem -lmpi"\n'
            '  exit 0\n'
            'fi\n'
            'exit 1\n') % _GCC)
        comp = InstalledCompiler(path, OPENSHMEM.members[SHMEM_CC][0])
        self.assertIsNotNone(comp.wrapped)
        self.assertEqual(comp.wrapped.absolute_path, _GCC)
        self.assertIs(comp.wrapped.info.role, CC)
        self.assertListEqual(comp.include_path, ['/fake/openmpi/include'])
        self.assertListEqual(comp.library_path, ['/fake/openmpi/lib'])
        self.assertListEqual(comp.libraries, ['oshmem', 'mpi'])

    def test_no_showme_wrapper(self):
        """A reference OpenSHMEM style compiler that rejects -showme isn't an error."""
        path = self._make_compiler('oshcc', 'echo "unrecognized command-line option" >&2\nexit 1\n')
        comp = InstalledCompiler(path, OPENSHMEM.members[SHMEM_CC][0])
        self.assertIsNone(comp.wrapped)
        self.assertListEqual(comp.include_path, [])
        self.assertListEqual(comp.library_path, [])

    def test_required_wrapper(self):
        """Families that don't set optional_wrapper still reject commands that don't accept the show flags."""
        path = self._make_compiler('mpicc', 'echo "unrecognized command-line option" >&2\nexit 1\n')
        info = next(info for info in SYSTEM.members[MPI_CC] if info.command == 'mpicc')
        with self.assertRaises(ConfigurationError):
            InstalledCompiler(path, info)
