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
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError, InternalError
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.python import PY
from taucmdr.cf.platforms import DARWIN, LINUX
from taucmdr.cf.software import tau_installation
from taucmdr.cf.software.tau_installation import TauInstallation


class TauInstallationTest(tests.TestCase):
    """Tests for TauInstallation CUPTI detection and tagging."""

    def setUp(self):
        super().setUp()
        # Give each test its own isolated temp directory so tests don't
        # pollute each other's filesystem state.
        self._cuda_tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._cuda_tmpdir, ignore_errors=True)
        super().tearDown()

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _make_cupti_header(self, *path_parts):
        """Create a fake cupti_events.h under the per-test cuda tmpdir."""
        inc = os.path.join(self._cuda_tmpdir, *path_parts, 'include')
        os.makedirs(inc, exist_ok=True)
        with open(os.path.join(inc, 'cupti_events.h'), 'w', encoding='utf-8'):
            pass

    @staticmethod
    def _fake_self(cuda_prefix):
        return SimpleNamespace(cuda_prefix=cuda_prefix)

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
        shutil.rmtree(self._prefix, ignore_errors=True)
        super().tearDown()

    def _write_header(self, *lines):
        """Write include/TAU.h.default under the per-test install prefix."""
        inc = os.path.join(self._prefix, 'include')
        os.makedirs(inc, exist_ok=True)
        with open(os.path.join(inc, 'TAU.h.default'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')

    def _fake_self(self):
        return SimpleNamespace(install_prefix=self._prefix)

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

    The real predicates are borrowed so the gates and the rules they share are tested together.
    """
    # pylint: disable=too-few-public-methods,protected-access

    _tau_exec_applies = TauInstallation._tau_exec_applies
    _links_tau_on_darwin = TauInstallation._links_tau_on_darwin
    _rewrite_launcher_appfile_cmd = TauInstallation._rewrite_launcher_appfile_cmd

    def __init__(self, target_os, mpi_support):
        self.target_os = target_os
        self.mpi_support = mpi_support
        self.baseline = False
        self.uses_python = False
        self.unmanaged = False
        self.uid = 'deadbeef'
        self.compilers = {}
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

    def test_darwin_mpi_measuring_nothing_uses_plain_compiler(self):
        """No profile and no trace means tau_exec would not run, so nothing needs linking in either."""
        fake = _FakeRuntimeInstallation(DARWIN, mpi_support=True)
        fake.profile = 'none'
        fake.trace = 'none'
        self.assertEqual(self._compiler_command(fake), self._COMPILER.absolute_path)
        self.assertEqual(self._launch_command(fake), ['mpirun', '-np', '4', './a.out'])

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


class TauExecAppliesTest(tests.TestCase):
    """Tests for the platform-independent tau_exec rule that the Darwin link rule builds on."""
    # pylint: disable=protected-access

    @staticmethod
    def _fake(**overrides):
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        for name, value in overrides.items():
            setattr(fake, name, value)
        return fake

    def test_runtime_only_applies(self):
        """Dynamic linkage, some output, no source or compiler instrumentation: tau_exec."""
        self.assertTrue(self._fake()._tau_exec_applies())

    def test_static_linkage_excluded(self):
        """A static binary cannot be preloaded."""
        self.assertFalse(self._fake(application_linkage='static')._tau_exec_applies())

    def test_no_output_excluded(self):
        """Neither profiles nor traces requested: nothing to measure."""
        self.assertFalse(self._fake(profile='none', trace='none')._tau_exec_applies())
        self.assertTrue(self._fake(profile='none', trace='otf2')._tau_exec_applies())

    def test_python_excluded(self):
        """Python applications go through tau_python instead."""
        self.assertFalse(self._fake(uses_python=True)._tau_exec_applies())

    def test_compile_time_inst_alone_excluded(self):
        """Compiler instrumentation links TAU in; tau_exec is only added for runtime wrappers."""
        self.assertFalse(self._fake(compiler_inst='always')._tau_exec_applies())
        for wrapper in ('measure_opencl', 'tbb_support', 'pthreads_support'):
            with self.subTest(wrapper=wrapper):
                self.assertTrue(self._fake(compiler_inst='always', **{wrapper: True})._tau_exec_applies())


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


class EnvironmentTest(tests.TestCase):
    """Tests for environment sanitizing and environment compatibility checks."""
    # pylint: disable=protected-access

    def test_sanitize_environment_strips_tau_variables(self):
        """TAU_*, SCOREP_*, PROFILEDIR and TRACEDIR are dropped and reported; everything else survives."""
        env = {'TAU_METRICS': 'TIME', 'SCOREP_TOTAL_MEMORY': '1G', 'PROFILEDIR': '/p',
               'TRACEDIR': '/t', 'PATH': '/bin', 'HOME': '/h'}
        with self.assertLogs(tau_installation.LOGGER, level='INFO') as logs:
            clean = TauInstallation._sanitize_environment(env)
        self.assertEqual(clean, {'PATH': '/bin', 'HOME': '/h'})
        self.assertIn('TAU_METRICS=TIME', logs.output[0])
        self.assertIn('TRACEDIR=/t', logs.output[0])

    def test_sanitize_environment_is_silent_when_clean(self):
        """Nothing to strip means nothing is logged; a TAU prefix without underscore is not a TAU variable."""
        env = {'PATH': '/bin', 'TAUCMDR_HOME': '/x'}
        with mock.patch.object(tau_installation.LOGGER, 'info') as info:
            self.assertEqual(TauInstallation._sanitize_environment(env), env)
        info.assert_not_called()

    def test_check_env_compat_rejects_darshan(self):
        """Darshan preloaded or loaded as a module is incompatible with TAU."""
        with mock.patch.dict(os.environ, {'DARSHAN_PRELOAD': '/opt/darshan/lib/libdarshan.so'}):
            with self.assertRaises(ConfigurationError):
                TauInstallation.check_env_compat()
        with mock.patch.dict(os.environ, {'LOADEDMODULES': 'gcc/12.2:Darshan/3.4.0'}):
            with self.assertRaises(ConfigurationError):
                TauInstallation.check_env_compat()

    def test_check_env_compat_rejects_cray_compilers(self):
        """PrgEnv-cray is rejected regardless of case."""
        with mock.patch.dict(os.environ, {'PE_ENV': 'CRAY'}):
            with self.assertRaises(ConfigurationError) as ctx:
                TauInstallation.check_env_compat()
        self.assertIn('Cray', str(ctx.exception))

    def test_check_env_compat_accepts_clean_environment(self):
        """No darshan and a non-Cray programming environment pass."""
        env = {key: val for key, val in os.environ.items()
               if key not in ('DARSHAN_PRELOAD', 'LOADEDMODULES', 'PE_ENV')}
        env['PE_ENV'] = 'GNU'
        with mock.patch.dict(os.environ, env, clear=True):
            TauInstallation.check_env_compat()


class LauncherAppfileTest(tests.TestCase):
    """Tests for rewriting launcher application files (mpirun --app, srun --multi-prog) to use tau_exec."""
    # pylint: disable=protected-access

    _TAU_EXEC = ['tau_exec', '-T', 'mpi']

    @staticmethod
    def _write_appfile(*lines):
        path = os.path.abspath('app.cfg')
        with open(path, 'w', encoding='utf-8') as fout:
            fout.write('\n'.join(lines) + '\n')
        return path

    @staticmethod
    def _read_lines(path):
        with open(path, encoding='utf-8') as fin:
            return [line.split() for line in fin if line.strip()]

    def test_mpirun_appfile_rewritten(self):
        """Each command line gets tau_exec in front of its executable; comments and blank lines are dropped."""
        appfile = self._write_appfile('# rank layout', '', '-np 2 ls -l', '-np 1 hostname')
        cmd = TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '--app', appfile], self._TAU_EXEC)
        self.assertEqual(cmd[:2], ['mpirun', '--app'])
        self.assertEqual(len(cmd), 3)
        self.assertNotEqual(cmd[2], appfile)
        self.assertTrue(cmd[2].endswith('.tau'))
        self.assertEqual(self._read_lines(cmd[2]),
                         [['-np', '2'] + self._TAU_EXEC + ['ls', '-l'],
                          ['-np', '1'] + self._TAU_EXEC + ['hostname']])

    def test_srun_multi_prog_inserts_after_rank_spec(self):
        """Slurm multi-prog lines start with a task range, so tau_exec always goes in second position."""
        appfile = self._write_appfile('0 ls', '1-3 hostname -s')
        cmd = TauInstallation._rewrite_launcher_appfile_cmd(
            None, ['srun', '-n', '4', '--multi-prog', appfile, '--label'], self._TAU_EXEC)
        self.assertEqual(cmd[:4], ['srun', '-n', '4', '--multi-prog'])
        self.assertEqual(cmd[5:], ['--label'])
        self.assertEqual(self._read_lines(cmd[4]),
                         [['0'] + self._TAU_EXEC + ['ls'],
                          ['1-3'] + self._TAU_EXEC + ['hostname', '-s']])

    def test_appfile_flag_with_equals(self):
        """The --flag=file spelling is rewritten in place, keeping the equals form."""
        appfile = self._write_appfile('-np 2 ls')
        cmd = TauInstallation._rewrite_launcher_appfile_cmd(
            None, ['mpirun', '-np', '2', '--app=' + appfile, '--verbose'], self._TAU_EXEC)
        self.assertEqual(cmd[:3], ['mpirun', '-np', '2'])
        self.assertEqual(cmd[4:], ['--verbose'])
        self.assertTrue(cmd[3].startswith('--app='))
        self.assertTrue(cmd[3].endswith('.tau'))
        self.assertEqual(self._read_lines(cmd[3][len('--app='):]), [['-np', '2'] + self._TAU_EXEC + ['ls']])
        cmd = TauInstallation._rewrite_launcher_appfile_cmd(
            None, ['srun', '--multi-prog=' + appfile], self._TAU_EXEC)
        self.assertEqual(len(cmd), 2)
        self.assertTrue(cmd[1].startswith('--multi-prog='))
        self.assertTrue(cmd[1].endswith('.tau'))

    def test_other_flags_with_equals_ignored(self):
        """A --key=value flag that is not the application-file flag is skipped, not mistaken for it."""
        appfile = self._write_appfile('-np 2 ls')
        cmd = TauInstallation._rewrite_launcher_appfile_cmd(
            None, ['mpirun', '--mca=btl=tcp', '--app', appfile], self._TAU_EXEC)
        self.assertEqual(cmd[:3], ['mpirun', '--mca=btl=tcp', '--app'])
        self.assertTrue(cmd[3].endswith('.tau'))
        with self.assertRaises(InternalError):
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '--mca=btl=tcp'], self._TAU_EXEC)

    def test_unknown_launcher_rejected(self):
        """Launchers without a known application-file flag cannot be rewritten."""
        appfile = self._write_appfile('-np 2 ls')
        for launcher in ('aprun', 'my_launcher'):
            with self.assertRaises(InternalError):
                TauInstallation._rewrite_launcher_appfile_cmd(None, [launcher, '--app', appfile], self._TAU_EXEC)

    def test_missing_appfile_flag_rejected(self):
        """A launcher command with no application-file flag cannot be rewritten."""
        with self.assertRaises(InternalError):
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '-np', '4'], self._TAU_EXEC)

    def test_line_without_executable_rejected(self):
        """A command line that names no executable is a configuration error, not silently passed through."""
        appfile = self._write_appfile('-np 2 no_such_program_for_taucmdr_tests')
        with self.assertRaises(ConfigurationError):
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '-app', appfile], self._TAU_EXEC)


class ApplicationCommandTest(tests.TestCase):
    """Tests for get_application_command() paths that need no real TAU installation."""
    # pylint: disable=protected-access

    _LAUNCHER = ['mpirun', '-np', '4']

    @staticmethod
    def _launch(fake, launcher, apps):
        cmd, _ = TauInstallation.get_application_command(fake, list(launcher), apps)
        return cmd

    def test_baseline_uses_tau_baseline(self):
        """Baseline measurements run everything under tau_baseline without touching the makefile."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        fake.baseline = True
        cmd = self._launch(fake, self._LAUNCHER, [['./a.out', '-x'], [':', '-np', '2', './b.out']])
        self.assertEqual(cmd, ['tau_baseline', 'mpirun', '-np', '4', './a.out', '-x', ':', '-np', '2', './b.out'])

    def test_site_launcher_args_appended(self):
        """Site-specific launcher arguments from the environment follow the launcher, ahead of tau_exec."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        with mock.patch.dict(os.environ, {'__TAUCMDR_LAUNCHER_ARGS__': '--bind-to core'}):
            cmd = self._launch(fake, self._LAUNCHER, [['./a.out']])
        self.assertEqual(cmd[:5], ['mpirun', '-np', '4', '--bind-to', 'core'])
        self.assertEqual(cmd[5], 'tau_exec')

    def test_mpmd_wraps_each_executable(self):
        """Every MPMD command gets its own tau_exec; launcher flags between commands are untouched."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        cmd = self._launch(fake, self._LAUNCHER, [['ls', '-l'], [':', '-np', '2', 'hostname']])
        tags = cmd[5]
        self.assertEqual(set(tags.split(',')), {'deadbeef', 'mpi'})
        self.assertEqual(cmd, ['mpirun', '-np', '4', 'tau_exec', '-T', tags, 'ls', '-l',
                               ':', '-np', '2', 'tau_exec', '-T', tags, 'hostname'])

    def test_mpmd_command_without_executable_rejected(self):
        """An MPMD command that names no executable cannot be wrapped."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        with self.assertRaises(InternalError):
            self._launch(fake, self._LAUNCHER, [['./a.out'], [':', '-np', '2', 'no_such_program_for_taucmdr_tests']])

    def test_appfile_launch_rewrites_appfile(self):
        """With no application command the launcher's application file is rewritten instead."""
        appfile = os.path.abspath('app.cfg')
        with open(appfile, 'w', encoding='utf-8') as fout:
            fout.write('-np 2 ls\n')
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        cmd = self._launch(fake, ['mpirun', '--app', appfile], [])
        self.assertEqual(cmd[:2], ['mpirun', '--app'])
        self.assertTrue(cmd[2].endswith('.tau'))
        with open(cmd[2], encoding='utf-8') as fin:
            self.assertIn('tau_exec -T', fin.read())

    def test_unmanaged_makefile_without_uid_warns(self):
        """A hand-built TAU whose makefile lacks our UID is used, with a warning."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        fake.unmanaged = True
        fake._makefile_tags = lambda _: {'mpi'}
        with self.assertLogs(tau_installation.LOGGER, level='WARNING') as logs:
            cmd = self._launch(fake, self._LAUNCHER, [['./a.out']])
        self.assertIn('runtime compatibility', logs.output[0])
        self.assertEqual(cmd[3:5], ['tau_exec', '-T'])

    def test_managed_makefile_without_uid_is_silent(self):
        """The compatibility warning is reserved for unmanaged installations."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        fake._makefile_tags = lambda _: {'mpi'}
        with mock.patch.object(tau_installation.LOGGER, 'warning') as warn:
            cmd = self._launch(fake, self._LAUNCHER, [['./a.out']])
        warn.assert_not_called()
        self.assertEqual(cmd[3:5], ['tau_exec', '-T'])

    def test_python_uses_tau_python(self):
        """Python applications run under tau_python with the target interpreter and the python tag stripped."""
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=False)
        fake.uses_python = True
        fake.compilers = {PY: SimpleNamespace(absolute_path='/opt/py/bin/python3')}
        fake._makefile_tags = lambda _: {'deadbeef', 'python'}
        cmd = self._launch(fake, [], [['script.py', '--flag']])
        self.assertEqual(cmd[:2], ['tau_python', '-T'])
        self.assertEqual(set(cmd[2].split(',')), {'deadbeef', 'serial'})
        self.assertEqual(cmd[3], '-tau-python-interpreter=/opt/py/bin/python3')
        self.assertEqual(cmd[4:], ['script.py', '--flag'])

    def test_instrumented_binary_runs_directly(self):
        """Source instrumentation, static linkage, or no measurement at all: tau_exec is not needed."""
        for attr, value in (('source_inst', 'automatic'), ('compiler_inst', 'always'),
                            ('application_linkage', 'static')):
            fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
            setattr(fake, attr, value)
            self.assertEqual(self._launch(fake, self._LAUNCHER, [['./a.out']]), ['mpirun', '-np', '4', './a.out'])
        fake = _FakeRuntimeInstallation(LINUX, mpi_support=True)
        fake.profile = 'none'
        fake.trace = 'none'
        self.assertEqual(self._launch(fake, self._LAUNCHER, [['./a.out']]), ['mpirun', '-np', '4', './a.out'])


class DataFormatTest(tests.TestCase):
    """Tests for guessing performance data formats from file names."""

    def test_directory_is_tau_profile(self):
        """A directory of profile.* files is TAU's native profile format."""
        self.assertEqual(TauInstallation.get_data_format(os.getcwd()), 'tau')

    def test_extensions(self):
        """Known extensions map to their formats, including gzipped merged profiles."""
        for ext, fmt in (('.ppk', 'ppk'), ('.xml', 'merged'), ('.cubex', 'cubex'), ('.slog2', 'slog2'),
                         ('.otf2', 'otf2'), ('.xml.gz', 'merged'), ('.db', 'sqlite')):
            self.assertEqual(TauInstallation.get_data_format('trial' + ext), fmt)

    def test_unknown_extension_rejected(self):
        """Unknown extensions, gzipped or not, are configuration errors."""
        for name in ('trial.txt', 'trial.tar.gz', 'trial'):
            with self.assertRaises(ConfigurationError):
                TauInstallation.get_data_format(name)

    def test_format_classification(self):
        """Every format is either a profile or a trace, never both."""
        for fmt in ('tau', 'ppk', 'merged', 'cubex', 'sqlite'):
            self.assertTrue(TauInstallation.is_profile_format(fmt))
            self.assertFalse(TauInstallation.is_trace_format(fmt))
        for fmt in ('slog2', 'otf2'):
            self.assertFalse(TauInstallation.is_profile_format(fmt))
            self.assertTrue(TauInstallation.is_trace_format(fmt))
