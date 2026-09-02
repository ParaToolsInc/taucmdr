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

Functions used for unit tests of tau_installation.py.
"""

import os
import shutil
import tempfile
from types import SimpleNamespace
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.platforms import DARWIN, LINUX
from taucmdr.cf.software.tau_installation import TauInstallation


class TauInstallationTest(tests.TestCase):
    """Tests for TauInstallation CUPTI detection and tagging."""

    def setUp(self):
        super().setUp()
        # Give each test its own isolated temp directory so tests don't
        # pollute each other's filesystem state.
        self._cuda_tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._cuda_tmpdir, ignore_errors=True)
        super().tearDown()

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _make_cupti_header(self, *path_parts):
        """Create a fake cupti_events.h under the per-test cuda tmpdir."""
        inc = os.path.join(self._cuda_tmpdir, *path_parts, 'include')
        os.makedirs(inc, exist_ok=True)
        open(os.path.join(inc, 'cupti_events.h'), 'w').close()

    def _fake_self(self, cuda_prefix):
        class _FakeSelf:
            pass
        fs = _FakeSelf()
        fs.cuda_prefix = cuda_prefix
        return fs

    # ------------------------------------------------------------------ #
    # _find_cupti_prefix                                                   #
    # ------------------------------------------------------------------ #

    def test_find_cupti_standard_sdk_layout(self):
        """extras/CUPTI/include/cupti_events.h — first candidate."""
        self._make_cupti_header('extras', 'CUPTI')
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, os.path.join(self._cuda_tmpdir, 'extras', 'CUPTI'))

    def test_find_cupti_system_packaged_layout(self):
        """<cuda>/include/cupti_events.h — third candidate (e.g. /usr)."""
        self._make_cupti_header()
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, self._cuda_tmpdir)

    def test_find_cupti_orig_layout(self):
        """extras/CUPTI.orig/include/cupti_events.h — fourth candidate."""
        self._make_cupti_header('extras', 'CUPTI.orig')
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertEqual(result, os.path.join(self._cuda_tmpdir, 'extras', 'CUPTI.orig'))

    def test_find_cupti_returns_none_when_missing(self):
        """No headers present: returns None."""
        result = TauInstallation._find_cupti_prefix(self._fake_self(self._cuda_tmpdir))
        self.assertIsNone(result)

    def test_find_cupti_returns_none_when_no_cuda_prefix(self):
        """No cuda_prefix: returns None without touching filesystem."""
        result = TauInstallation._find_cupti_prefix(self._fake_self(None))
        self.assertIsNone(result)


class TauVersionTest(tests.TestCase):
    """Tests for TauInstallation.get_tau_version() header parsing."""

    def setUp(self):
        super().setUp()
        self._prefix = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._prefix, ignore_errors=True)
        super().tearDown()

    def _write_header(self, *lines):
        """Write include/TAU.h.default under the per-test install prefix."""
        inc = os.path.join(self._prefix, 'include')
        os.makedirs(inc, exist_ok=True)
        with open(os.path.join(inc, 'TAU.h.default'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

    def _fake_self(self):
        class _FakeSelf:
            pass
        fs = _FakeSelf()
        fs.install_prefix = self._prefix
        return fs

    def test_release_version(self):
        """Plain release string parses to a tuple of ints."""
        self._write_header('#ifndef TAU_H_DEFAULT', '#define TAU_VERSION "2.33.2"', '#endif')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 33, 2))

    def test_git_suffix_stripped(self):
        """Nightly builds carry a -git suffix that must not break parsing."""
        self._write_header('#define TAU_VERSION "2.35.1-git"')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 35, 1))

    def test_two_component_version(self):
        """Major.minor only is a valid, comparable tuple."""
        self._write_header('#define TAU_VERSION "2.32"')
        self.assertEqual(TauInstallation.get_tau_version(self._fake_self()), (2, 32))

    def test_missing_header_returns_none(self):
        """No TAU.h.default under the prefix: returns None instead of raising."""
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_header_without_version_returns_none(self):
        """Header present but no TAU_VERSION define: returns None."""
        self._write_header('#define TAU_MAX_THREADS 128')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_malformed_version_returns_none(self):
        """Non-numeric version string is swallowed and reported as None."""
        self._write_header('#define TAU_VERSION "unknown"')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))

    def test_unquoted_version_returns_none(self):
        """Define without quotes cannot be split on '"' and is reported as None."""
        self._write_header('#define TAU_VERSION 2.33.2')
        self.assertIsNone(TauInstallation.get_tau_version(self._fake_self()))


class _FakeRuntimeInstallation:
    """Stand-in for TauInstallation exposing only what the wrapper and launch gates read.

    The real predicate is borrowed so the gates and the rule they share are tested together.
    """
    # pylint: disable=too-few-public-methods,protected-access

    _links_tau_on_darwin = TauInstallation._links_tau_on_darwin

    def __init__(self, target_os, mpi_support):
        self.target_os = target_os
        self.mpi_support = mpi_support
        self.baseline = False
        self.uses_python = False
        self.unmanaged = False
        self.uid = 'deadbeef'
        self.application_linkage = 'dynamic'
        self.source_inst = 'never'
        self.compiler_inst = 'never'
        self.measure_openmp = 'ignore'
        self.measure_opencl = False
        self.tbb_support = False
        self.pthreads_support = False
        self.profile = 'tau'
        self.trace = 'none'

    def install(self):
        """No-op: nothing to install for a fake."""

    @staticmethod
    def runtime_config():
        """No tau_exec options and no environment changes."""
        return [], {}

    @staticmethod
    def get_makefile():
        """Any makefile name; tags are supplied by _makefile_tags()."""
        return 'Makefile.tau-deadbeef-mpi'

    def _makefile_tags(self, _makefile):
        return {'deadbeef', 'mpi'} if self.mpi_support else {'deadbeef'}


class RuntimeInstrumentationOnDarwinTest(tests.TestCase):
    """MPI with runtime-only instrumentation on Darwin must link TAU in, not inject it with tau_exec.

    dyld on macOS 12 and later ignores DYLD_FORCE_FLAT_NAMESPACE, so tau_exec never intercepts MPI
    calls in a two-level-namespace binary. Linking with tau_cc.sh -optLinkOnly sidesteps dyld.
    """

    _COMPILER = SimpleNamespace(info=SimpleNamespace(role=MPI_CC), absolute_path='/opt/mpi/bin/mpicc')

    def _compiler_command(self, fake):
        return TauInstallation.get_compiler_command(fake, self._COMPILER)

    @staticmethod
    def _launch_command(fake):
        cmd, _ = TauInstallation.get_application_command(fake, ['mpirun', '-np', '4'], [['./a.out']])
        return cmd

    def test_darwin_mpi_links_with_wrapper(self):
        """Darwin + MPI + no source/compiler instrumentation compiles through tau_cc.sh."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=True)
        self.assertEqual(self._compiler_command(fake), 'tau_cc.sh')

    def test_linux_mpi_uses_plain_compiler(self):
        """Same configuration on Linux keeps the plain compiler; tau_exec works there."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        self.assertEqual(self._compiler_command(fake), self._COMPILER.absolute_path)

    def test_darwin_serial_uses_plain_compiler(self):
        """Darwin without MPI keeps the plain compiler; nothing to interpose."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=False)
        self.assertEqual(self._compiler_command(fake), self._COMPILER.absolute_path)

    def test_darwin_mpi_static_linkage_still_uses_wrapper(self):
        """Static linkage already forced the wrapper; the Darwin rule must not undo that."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=True)
        fake.application_linkage = 'static'
        self.assertEqual(self._compiler_command(fake), 'tau_cc.sh')

    def test_darwin_mpi_launches_without_tau_exec(self):
        """Darwin + MPI + no source/compiler instrumentation runs the linked binary directly."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=True)
        self.assertEqual(self._launch_command(fake), ['mpirun', '-np', '4', './a.out'])

    def test_linux_mpi_launches_with_tau_exec(self):
        """Same configuration on Linux still wraps the application in tau_exec."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        cmd = self._launch_command(fake)
        self.assertEqual(cmd[:3], ['mpirun', '-np', '4'])
        self.assertEqual(cmd[3], 'tau_exec')
        self.assertEqual(cmd[-1], './a.out')

    def test_darwin_serial_launches_with_tau_exec(self):
        """Darwin without MPI still uses tau_exec; no MPI symbols need interposing."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=False)
        cmd = self._launch_command(fake)
        self.assertEqual(cmd[3], 'tau_exec')
        self.assertIn('serial', cmd[5])


class PythonLibraryTest(tests.TestCase):
    """Tests for TauInstallation._find_python_library() shared-library discovery.

    TAU's configure derives the Python library file name from sysconfig LDLIBRARY. On
    Homebrew's framework Python that is ``Python.framework/Versions/3.X/Python``, which
    does not exist under the lib directory, so configure aborts. Passing
    ``-pythonlibrary=libpython3.X.dylib`` explicitly sidesteps that lookup.
    """
    # pylint: disable=protected-access

    def setUp(self):
        super().setUp()
        self._prefix = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._prefix, ignore_errors=True)
        super().tearDown()

    def _layout(self, stdlib, *libs):
        """Create <prefix>/<stdlib>/ and touch each lib path given relative to <prefix>.

        Returns the absolute stdlib path, as sysconfig.get_path("stdlib") would report it.
        """
        os.makedirs(os.path.join(self._prefix, stdlib), exist_ok=True)
        for lib in libs:
            path = os.path.join(self._prefix, lib)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8'):
                pass
        return os.path.join(self._prefix, stdlib)

    def _lib(self, *parts):
        return os.path.join(self._prefix, *parts)

    def test_homebrew_framework_layout(self):
        """libpython beside the stdlib dir (Homebrew framework): lib dir plus unversioned name."""
        stdlib = self._layout('lib/python3.14', 'lib/libpython3.14.dylib')
        self.assertEqual(TauInstallation._find_python_library(stdlib, 'dylib'),
                         (self._lib('lib'), 'libpython3.14.dylib'))

    def test_library_inside_stdlib_tree(self):
        """libpython under the stdlib tree (config-* dir) wins over the parent directory."""
        config = 'lib/python3.12/config-3.12-x86_64-linux-gnu'
        stdlib = self._layout('lib/python3.12', config + '/libpython3.12.so', 'lib/libpython3.12.so')
        self.assertEqual(TauInstallation._find_python_library(stdlib, 'so'),
                         (self._lib(config), 'libpython3.12.so'))

    def test_versioned_only_no_name(self):
        """Only libpython3.12.so.1.0 present: the dir is usable, but no name is reported.

        FixMakefile strips one extension from -pythonlibrary to build the -l flag, so a
        versioned name would link against a nonexistent 'python3.12.so.1'.
        """
        stdlib = self._layout('lib/python3.12', 'lib/libpython3.12.so.1.0')
        self.assertEqual(TauInstallation._find_python_library(stdlib, 'so'),
                         (self._lib('lib'), None))

    def test_prefers_unversioned_name(self):
        """Both versioned and unversioned present: the unversioned name is reported."""
        stdlib = self._layout('lib/python3.12', 'lib/libpython3.12.so.1.0', 'lib/libpython3.12.so')
        self.assertEqual(TauInstallation._find_python_library(stdlib, 'so'),
                         (self._lib('lib'), 'libpython3.12.so'))

    def test_wrong_suffix_not_matched(self):
        """A .so is not a candidate when the target wants .dylib."""
        stdlib = self._layout('lib/python3.14', 'lib/libpython3.14.so')
        with self.assertRaises(ConfigurationError):
            TauInstallation._find_python_library(stdlib, 'dylib')

    def test_missing_library_raises(self):
        """No libpython anywhere near the stdlib: ConfigurationError."""
        stdlib = self._layout('lib/python3.14')
        with self.assertRaises(ConfigurationError):
            TauInstallation._find_python_library(stdlib, 'dylib')
