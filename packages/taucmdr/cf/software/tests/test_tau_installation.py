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

Functions used for unit tests of tau_installation.py.
"""

import datetime
import glob
import os
import subprocess
import sys
import tempfile
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, ARM64, DARWIN, LINUX
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.software.installation import Installation
from taucmdr.cf.software.tau_installation import TauInstallation, complete_nightly_names, python_build_paths


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


def _has_headers(python_path):
    """Return True if the Python interpreter at `python_path` has its C headers installed."""
    check = 'import os, sysconfig; print(os.path.exists(os.path.join(sysconfig.get_path("include"), "Python.h")))'
    proc = subprocess.run([python_path, '-c', check], stdout=subprocess.PIPE, text=True, check=False)
    return proc.stdout.strip() == 'True'


class CompleteNightlyNamesTest(tests.TestCase):
    """Tests for :any:`complete_nightly_names`."""

    @staticmethod
    def _src(**files):
        src = tempfile.mkdtemp(dir=tests.get_test_workdir())
        for name, data in files.items():
            with open(os.path.join(src, name), 'w', encoding='utf-8') as fout:
                fout.write(data)
        return src

    @staticmethod
    def _contents(src):
        result = {}
        for name in sorted(os.listdir(src)):
            with open(os.path.join(src, name), encoding='utf-8') as fin:
                result[name] = fin.read()
        return result

    def test_complete_nightly_names(self):
        today = datetime.datetime.now().strftime('tau-nightly-%Y-%m-%d.tgz')
        src = self._src(**{'tau-nightly.tgz': 'new'})
        self.assertEqual(complete_nightly_names(src), [today])
        self.assertEqual(self._contents(src), {'tau-nightly.tgz': 'new', today: 'new'})

        src = self._src(**{'tau-nightly-2026-01-02.tgz': 'older', 'tau-nightly-2026-03-04.tgz': 'newer'})
        self.assertEqual(complete_nightly_names(src), ['tau-nightly.tgz'])
        self.assertEqual(self._contents(src)['tau-nightly.tgz'], 'newer')

        files = {'tau-nightly.tgz': 'a', 'tau-nightly-2026-01-02.tgz': 'a'}
        src = self._src(**files)
        self.assertEqual(complete_nightly_names(src), [])
        self.assertEqual(self._contents(src), files)

        src = self._src()
        self.assertEqual(complete_nightly_names(src), [])
        self.assertEqual(complete_nightly_names(os.path.join(src, 'missing')), [])


class PythonBuildPathsTest(tests.TestCase):
    """Tests for :any:`python_build_paths`."""

    def test_python_build_paths(self):
        """The header and library directories of the running Python and of /usr/bin/python3 are found."""
        interpreters = [sys.executable]
        system_python = '/usr/bin/python3'
        # A system Python without its development package can't be used to build TAU, so skip it.
        if (os.path.exists(system_python) and os.path.realpath(system_python) != os.path.realpath(sys.executable)
                and _has_headers(system_python)):
            interpreters.append(system_python)
        for interpreter in interpreters:
            with self.subTest(interpreter=interpreter):
                include_dir, lib_dir = python_build_paths(interpreter)
                self.assertEqual(include_dir, include_dir.strip())
                self.assertEqual(lib_dir, lib_dir.strip())
                self.assertTrue(os.path.isfile(os.path.join(include_dir, 'Python.h')), include_dir)
                self.assertTrue(glob.glob(os.path.join(lib_dir, 'libpython*')), lib_dir)

    def test_python_build_paths_no_headers(self):
        """A Python without C headers, such as a distro Python without the corresponding development package, is refused."""
        # Create a fake Python interpreter and demonstrate that it produces a ConfigurationError
        # because it has no correspinding C headers.
        root = tempfile.mkdtemp(dir=os.getcwd())
        stdlib = os.path.join(root, 'lib', 'python3.99')
        include_dir = os.path.join(root, 'include', 'python3.99')
        os.makedirs(stdlib)
        os.makedirs(include_dir)
        with open(os.path.join(stdlib, 'libpython3.99.so'), 'w', encoding='utf-8'):
            pass
        interpreter = os.path.join(root, 'python3')
        with open(interpreter, 'w', encoding='utf-8') as fout:
            fout.write('#!/bin/sh\n'
                       f'case "$2" in *stdlib*) echo "{stdlib}" ;; *) echo "{include_dir}" ;; esac\n')
        os.chmod(interpreter, 0o755)
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn('Python.h', str(context.exception))


def _target_arch(target_os):
    """Return the target architecture for `target_os`: Apple silicon for macOS, which has no ppc64le TauMagic."""
    return ARM64 if target_os is DARWIN else HOST_ARCH


def _metrics(count):
    return ['TIME'] + [f'M{i}' for i in range(1, count)]


class PdtUseTest(tests.TestCase):
    """Tests for when a TAU configuration uses PDT."""

    @staticmethod
    def _tau(target_os, **kwargs):
        return TauInstallation({'tau': 'download', 'pdt': 'download'}, _target_arch(target_os), target_os,
                               TauInstallation.get_minimal().compilers, **kwargs)

    def test_source_inst_on_linux(self):
        self.assertTrue(self._tau(LINUX, source_inst='automatic').uses_pdt)

    def test_source_inst_on_darwin(self):
        self.assertFalse(self._tau(DARWIN, source_inst='automatic').uses_pdt)

    def test_shmem_on_darwin(self):
        self.assertFalse(self._tau(DARWIN, shmem_support=True).uses_pdt)


class OmptConfigurationTest(tests.TestCase):
    """Tests for the TAU configuration that measures OpenMP with OMPT."""

    @staticmethod
    def _tau(**kwargs):
        return TauInstallation({'tau': 'download', 'ompt': 'download'}, HOST_ARCH, HOST_OS,
                               TauInstallation.get_minimal().compilers, **kwargs)

    def test_ompt_tags(self):
        """An OMPT configuration asks only for the tags TAU puts in its makefile name."""
        tags = self._tau(openmp_support=True, measure_openmp='ompt').get_tags()
        self.assertTrue({'ompt', 'openmp'} <= tags)
        self.assertFalse({'v5', 'tr4', 'tr6'} & tags)

    def test_ompt_tags_match_makefile(self):
        """The OMPT makefile TAU writes is the one an OMPT configuration selects."""
        tau = self._tau(openmp_support=True, measure_openmp='ompt')
        lib_path = os.path.join(os.getcwd(), 'x86_64', 'lib')
        makefile = os.path.join(lib_path, f'Makefile.tau-{tau.uid}-ompt-openmp')
        decoy = os.path.join(lib_path, f'Makefile.tau-{tau.uid}-openmp-opari')
        with mock.patch.object(TauInstallation, 'lib_path', new_callable=mock.PropertyMock, return_value=lib_path), \
             mock.patch('glob.glob', return_value=[decoy, makefile]):
            self.assertEqual(tau._match_makefile(tau.get_tags()), makefile)

    @staticmethod
    def _src_with_configure(name, text):
        src = os.path.join(os.getcwd(), name)
        os.makedirs(src)
        with open(os.path.join(src, 'configure'), 'w', encoding='utf-8') as fout:
            fout.write(text)
        return src

    def test_useropts_ompt_include(self):
        """TAU is given the OMPT header directory only when its configure won't copy the header itself."""
        copy = 'cp ${omptlib}/../include/${ompt_header} ${START_DIR}/include/.\n'
        ompt = self._tau(openmp_support=True, measure_openmp='ompt')
        include = '-I' + os.path.join(ompt.dependencies['ompt'].install_prefix, 'include')
        ompt._src_prefix = self._src_with_configure('unset', 'ompt_version_selected=no\n' + copy)
        self.assertIn(include, ompt._useropts())
        ompt._src_prefix = self._src_with_configure('set', 'ompt_version_selected=no\nompt_header=omp-tools.h\n' + copy)
        self.assertNotIn(include, ompt._useropts())
        ignore = self._tau(openmp_support=True, measure_openmp='ignore')
        ignore._src_prefix = ompt._src_prefix
        self.assertFalse([opt for opt in ignore._useropts() if opt.startswith('-I')])
        self.assertEqual(self._tau()._useropts(), ['-O2', '-g'])


class UnwinderConfigureTest(tests.TestCase):
    """Tests for the stack unwinder options given to TAU's configure."""

    _CONFIGURE = ('    if [ "x$unwinder" = "xlibunwind" ] ; then\n'
                  '          if [ %s ] ; then\n'
                  '            unwind_lib_flag="-framework#System"\n')

    @staticmethod
    def _configure_argv(tau, configure=None):
        src = tempfile.mkdtemp(dir=os.getcwd())
        if configure is not None:
            with open(os.path.join(src, 'configure'), 'w', encoding='utf-8') as fout:
                fout.write(configure)
        tau._src_prefix = src  # pylint: disable=protected-access
        with mock.patch('taucmdr.util.create_subprocess', return_value=0) as create_subprocess:
            tau.configure()
        return create_subprocess.call_args.args[0]

    @staticmethod
    def _tau(target_os, target_arch=None):
        return TauInstallation({'tau': 'download', 'libunwind': 'download'}, target_arch or _target_arch(target_os),
                               target_os, TauInstallation.get_minimal().compilers)

    def test_darwin_configure_maps_unwinder(self):
        """On Apple silicon, TAU uses macOS's own libunwind when its configure knows how to link it."""
        configure = self._CONFIGURE % '$machine = apple -o $machine = arm64_apple'
        argv = self._configure_argv(self._tau(DARWIN, ARM64), configure)
        self.assertIn('-unwinder=libunwind', argv)
        self.assertFalse([arg for arg in argv if arg.startswith('-unwind=')], argv)

    def test_darwin_configure_without_unwinder_mapping(self):
        """On Apple silicon, TAU isn't asked for libunwind when its configure would link a bare -lunwind."""
        argv = self._configure_argv(self._tau(DARWIN, ARM64), self._CONFIGURE % '$machine = apple')
        self.assertFalse([arg for arg in argv if arg.startswith('-unwind')], argv)

    def test_darwin_without_libunwind(self):
        """On macOS, where TAU Commander provides no libunwind, TAU isn't asked to link one."""
        argv = self._configure_argv(self._tau(DARWIN))
        self.assertFalse([arg for arg in argv if arg.startswith('-unwind')], argv)

    def test_minimal_without_libunwind(self):
        """Minimal TAU, which has no libunwind, isn't asked to link one."""
        argv = self._configure_argv(TauInstallation.get_minimal())
        self.assertFalse([arg for arg in argv if arg.startswith('-unwind')], argv)

    def test_linux_with_libunwind(self):
        """With its own libunwind, TAU gets both the unwinder and libunwind's location."""
        tau = self._tau(LINUX)
        argv = self._configure_argv(tau)
        self.assertIn('-unwinder=libunwind', argv)
        self.assertIn('-unwind=%s' % tau.dependencies['libunwind'].install_prefix, argv)


class CompilerOptionsTest(tests.TestCase):
    """Tests for the TAU_OPTIONS given to TAU's compiler wrappers."""

    @staticmethod
    def _tau_options(target_os, **kwargs):
        compilers = TauInstallation.get_minimal().compilers
        tau = TauInstallation({'tau': 'download'}, _target_arch(target_os), target_os, compilers, **kwargs)
        with mock.patch.object(Installation, 'compiletime_config',
                               side_effect=lambda opts=None, env=None: (list(opts or []), dict(env or {}))), \
             mock.patch.object(TauInstallation, 'get_makefile', return_value=f'Makefile.tau-{tau.uid}'):
            _, env = tau.compiletime_config(compilers[CC])
        return env['TAU_OPTIONS'].split()

    def test_io_link_wrapper(self):
        """On Linux, I/O is also measured by wrapping I/O calls when the application is linked."""
        self.assertIn('-optTrackIO', self._tau_options(LINUX, measure_io=True, compiler_inst='always'))

    def test_no_io_link_wrapper_on_darwin(self):
        """Apple's linker can't wrap I/O calls, so on macOS I/O is measured only under tau_exec."""
        self.assertNotIn('-optTrackIO', self._tau_options(DARWIN, measure_io=True))


class TauConfigurationHashTest(tests.TestCase):
    """Tests for what makes TAU configurations share a hash."""

    @staticmethod
    def _tau(**kwargs):
        return TauInstallation({'tau': 'download'}, HOST_ARCH, HOST_OS, TauInstallation.get_minimal().compilers,
                               **kwargs)

    def test_uid_separates_threading(self):
        """A non-threaded configuration never shares a hash with one that asks TAU for pthreads."""
        plain = self._tau().uid
        pthreads = self._tau(pthreads_support=True).uid
        openmp_ignore = self._tau(openmp_support=True, measure_openmp='ignore').uid
        self.assertNotEqual(plain, pthreads)
        self.assertNotEqual(plain, openmp_ignore)
        self.assertEqual(pthreads, openmp_ignore)

    def test_uid_ignores_cpu_count(self):
        """A TAU configured on one host matches the same configuration on a host with a different core count."""
        uids = set()
        for count in 4, 512:
            with mock.patch('multiprocessing.cpu_count', return_value=count):
                uids.add(self._tau(openmp_support=True).uid)
        self.assertEqual(len(uids), 1)

    def test_uid_metrics_clamped(self):
        self.assertEqual(self._tau(metrics=_metrics(1)).uid, self._tau(metrics=_metrics(25)).uid)
        self.assertNotEqual(self._tau(metrics=_metrics(25)).uid, self._tau(metrics=_metrics(26)).uid)

    def test_useropts_metrics(self):
        self.assertEqual(self._tau()._useropts(), ['-O2', '-g'])
        self.assertEqual(self._tau(metrics=_metrics(25))._useropts(), ['-O2', '-g'])
        useropts = self._tau(metrics=_metrics(26))._useropts()
        self.assertIn('-DTAU_MAX_METRICS=26', useropts)
        self.assertIn('-DTAU_MAX_COUNTERS=26', useropts)
        for count in 1, 25, 26:
            self.assertFalse([opt for opt in self._tau(metrics=_metrics(count))._useropts() if 'TAU_MAX_THREADS' in opt])
