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

Functions used for unit tests of ompt_installation.py.
"""

import shutil
import tempfile
from types import SimpleNamespace
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompilerSet
from taucmdr.cf.compiler.host import CC, CXX
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS
from taucmdr.cf.software.installation import MakeInstallation, CMakeInstallation
from taucmdr.cf.software import ompt_installation
from taucmdr.cf.software.ompt_installation import OmptInstallation


def _ompt(src):
    return OmptInstallation({'ompt': src}, HOST_ARCH, HOST_OS, InstalledCompilerSet('test-compilers'))


class OmptInstallationTest(tests.TestCase):
    """Tests for the OMPT (LLVM OpenMP runtime) package description."""

    def test_tr4_tr6_rejected(self):
        """The retired TR4/TR6 runtimes name the replacement in their error."""
        for src in ('download-tr4', 'download-tr6'):
            with self.assertRaises(ConfigurationError) as ctx:
                _ompt(src)
            self.assertIn(src, str(ctx.exception))
            self.assertIn('--ompt download', str(ctx.exception))

    def test_download_uses_llvm_openmp(self):
        """'download' fetches LLVM OpenMP and verifies the OMPT 5.0 header set."""
        inst = _ompt('download')
        self.assertEqual(inst.name, 'ompt')
        self.assertEqual(inst.src, ompt_installation.REPOS[None][0])
        self.assertEqual(inst.srcs_avail, ompt_installation.REPOS[None])
        self.assertFalse(inst.unmanaged)
        self.assertEqual(inst.verify_libraries, ['libomp.so'])
        self.assertTrue({'omp.h', 'ompt.h', 'omp-tools.h'} <= set(inst.verify_headers))

    def test_existing_prefix_is_unmanaged(self):
        """An installed runtime directory is used in place."""
        prefix = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, prefix, ignore_errors=True)
        inst = _ompt(prefix)
        self.assertTrue(inst.unmanaged)
        self.assertEqual(inst.install_prefix, prefix)

    def test_cmake_uses_target_compilers(self):
        """CMake is pointed at the unwrapped target compilers and told to build a PIC release without CUDA."""
        inst = _ompt('download')
        inst.compilers = {CC: SimpleNamespace(unwrap=lambda: SimpleNamespace(absolute_path='/opt/bin/gcc')),
                          CXX: SimpleNamespace(unwrap=lambda: SimpleNamespace(absolute_path='/opt/bin/g++'))}
        with mock.patch.object(CMakeInstallation, 'cmake', return_value=0) as cmake:
            self.assertEqual(inst.cmake(['-DFOO=1']), 0)
        flags = cmake.call_args[0][0]
        self.assertEqual(flags[0], '-DFOO=1')
        for flag in ('-DCMAKE_C_COMPILER=/opt/bin/gcc', '-DCMAKE_CXX_COMPILER=/opt/bin/g++',
                     '-DCMAKE_C_FLAGS=-fPIC', '-DCMAKE_CXX_FLAGS=-fPIC', '-DCMAKE_BUILD_TYPE=Release',
                     '-DCMAKE_DISABLE_FIND_PACKAGE_CUDA:BOOL=TRUE'):
            self.assertIn(flag, flags)

    def test_make_generates_headers_first(self):
        """The generated OMPT headers are built before the runtime itself."""
        inst = _ompt('download')
        with mock.patch.object(MakeInstallation, 'make', return_value=0) as make:
            self.assertEqual(inst.make(['-j', '2']), 0)
        self.assertEqual([call[0][0] for call in make.call_args_list],
                         [['-j', '2', 'libomp-needed-headers'], ['-j', '2']])
