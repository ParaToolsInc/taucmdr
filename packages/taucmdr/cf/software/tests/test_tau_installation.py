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
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock
from taucmdr import tests, util
from taucmdr.error import ConfigurationError, InternalError
from taucmdr.cf.platforms import (HOST_ARCH, HOST_OS, ARM64, PPC64LE, X86_64, CRAY_CNL, DARWIN, LINUX,
                                  SHARED_LIBRARY_SUFFIX, HOST_TAU_MAGIC)
from taucmdr.cf.compiler.caf import CAF_FC
from taucmdr.cf.compiler.host import CC, CXX, FC
from taucmdr.cf.software import installation
from taucmdr.cf.software.installation import Installation
from taucmdr.cf.software.tau_installation import (NIGHTLY, TauInstallation, complete_nightly_names, python_build_paths,
                                                  tau_makefile_target)
from taucmdr.cli.commands.system.tests.test_fetch import make_archive
from taucmdr.cli.commands.target.tests.test_create import _tau_tree


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

    def _assert_links_to(self, src, name):
        plain = os.path.join(src, 'tau-nightly.tgz')
        self.assertTrue(os.path.islink(plain), plain)
        self.assertEqual(os.readlink(plain), name)

    def test_download(self):
        """A download under the plain name is dated by its modification time, and the plain name links to it."""
        src = self._src(**{'tau-nightly.tgz': 'new'})
        _set_mtime(os.path.join(src, 'tau-nightly.tgz'), '2026-03-04')
        self.assertEqual(complete_nightly_names(src), ['tau-nightly-2026-03-04.tgz', 'tau-nightly.tgz'])
        self.assertEqual(self._contents(src), {'tau-nightly-2026-03-04.tgz': 'new', 'tau-nightly.tgz': 'new'})
        self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_link_to_newest(self):
        src = self._src(**{'tau-nightly-2026-01-02.tgz': 'older', 'tau-nightly-2026-03-04.tgz': 'newer'})
        self.assertEqual(complete_nightly_names(src), ['tau-nightly.tgz'])
        self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_copy_replaced(self):
        """A copy of a dated archive under the plain name is replaced by a link to the newest."""
        src = self._src(**{'tau-nightly.tgz': 'a',
                           'tau-nightly-2026-01-02.tgz': 'a',
                           'tau-nightly-2026-03-04.tgz': 'b'})
        _set_mtime(os.path.join(src, 'tau-nightly.tgz'), '2026-05-06')
        self.assertEqual(complete_nightly_names(src), ['tau-nightly.tgz'])
        self.assertEqual(sorted(os.listdir(src)),
                         ['tau-nightly-2026-01-02.tgz', 'tau-nightly-2026-03-04.tgz', 'tau-nightly.tgz'])
        self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_older_download(self):
        """An archive under the plain name that's older than the newest dated archive keeps its own date."""
        src = self._src(**{'tau-nightly.tgz': 'old', 'tau-nightly-2026-03-04.tgz': 'newer'})
        _set_mtime(os.path.join(src, 'tau-nightly.tgz'), '2026-01-02')
        self.assertEqual(complete_nightly_names(src), ['tau-nightly-2026-01-02.tgz', 'tau-nightly.tgz'])
        self.assertEqual(self._contents(src), {'tau-nightly-2026-01-02.tgz': 'old',
                                               'tau-nightly-2026-03-04.tgz': 'newer',
                                               'tau-nightly.tgz': 'newer'})
        self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_stale_link(self):
        for target in 'tau-nightly-2026-01-02.tgz', 'tau-nightly-2025-01-01.tgz':
            with self.subTest(target=target):
                src = self._src(**{'tau-nightly-2026-01-02.tgz': 'older', 'tau-nightly-2026-03-04.tgz': 'newer'})
                os.symlink(target, os.path.join(src, 'tau-nightly.tgz'))
                self.assertEqual(complete_nightly_names(src), ['tau-nightly.tgz'])
                self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_current_link(self):
        src = self._src(**{'tau-nightly-2026-03-04.tgz': 'newer'})
        os.symlink('tau-nightly-2026-03-04.tgz', os.path.join(src, 'tau-nightly.tgz'))
        self.assertEqual(complete_nightly_names(src), [])
        self._assert_links_to(src, 'tau-nightly-2026-03-04.tgz')

    def test_no_nightly(self):
        src = self._src()
        self.assertEqual(complete_nightly_names(src), [])
        self.assertEqual(complete_nightly_names(os.path.join(src, 'missing')), [])


class NightlyInstallTagTest(tests.TestCase):
    """Tests for the installation tag and source archive of a TAU nightly build."""

    def setUp(self):
        super().setUp()
        self.system = tempfile.mkdtemp(dir=tests.get_test_workdir())
        self.src = os.path.join(self.system, 'src')
        os.mkdir(self.src)
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')

    def tearDown(self):
        os.chmod(self.src, stat.S_IRWXU)
        super().tearDown()

    def _nightly(self, name, toplevel, date=None):
        path = make_archive(os.path.join(self.src, name), toplevel=toplevel)
        if date:
            _set_mtime(path, date)
        return path

    def _tag_and_source(self, update_nightly=False):
        tau = TauInstallation.__new__(TauInstallation)
        tau.name, tau.title, tau.src, tau.srcs, tau.srcs_avail = 'tau', 'TAU', NIGHTLY, [], [NIGHTLY]
        tau.unmanaged, tau.update_nightly, tau._install_tag = False, update_nightly, None  # pylint: disable=protected-access
        level = SimpleNamespace(prefix=self.system)
        with mock.patch.object(installation, 'search_levels', return_value=[level]), \
             mock.patch.object(installation, 'highest_writable_storage', return_value=level):
            return tau._get_install_tag(), tau.src  # pylint: disable=protected-access

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from writing")
    def test_tag_from_built_archive(self):
        """The tag has the TAU version of the archive that is built, not of an outdated archive under the plain name."""
        older = self._nightly('tau-nightly-2026-01-02.tgz', 'tau-2.35')
        shutil.copy(older, os.path.join(self.src, 'tau-nightly.tgz'))
        newer = self._nightly('tau-nightly-2026-03-04.tgz', 'tau-2.36')
        os.chmod(self.src, 0o555)
        self.assertEqual(self._tag_and_source(), ('tau-2.36-2026-03-04', newer))

    def test_new_download(self):
        """An archive just downloaded under the plain name is built instead of an older dated one."""
        self._nightly('tau-nightly-2026-01-02.tgz', 'tau-2.35')
        self._nightly('tau-nightly.tgz', 'tau-2.36')
        dated = os.path.join(self.src, f'tau-nightly-{self.today}.tgz')
        self.assertEqual(self._tag_and_source(), (f'tau-2.36-{self.today}', dated))
        self.assertEqual(os.readlink(os.path.join(self.src, 'tau-nightly.tgz')), os.path.basename(dated))

    def test_update_nightly(self):
        """Updating downloads a new archive without overwriting the one the plain name links to."""
        older = self._nightly('tau-nightly-2026-01-02.tgz', 'tau-2.35')
        os.symlink(os.path.basename(older), os.path.join(self.src, 'tau-nightly.tgz'))
        with mock.patch.object(installation.util, 'download',
                               side_effect=lambda src, dest: make_archive(dest, toplevel='tau-2.36')) as download:
            tag, source = self._tag_and_source(update_nightly=True)
        download.assert_called_once()
        self.assertEqual(tag, f'tau-2.36-{self.today}')
        self.assertEqual(source, os.path.join(self.src, f'tau-nightly-{self.today}.tgz'))
        self.assertEqual(util.archive_toplevel(older), 'tau-2.35')

    def test_update_nightly_daily(self):
        """Updating doesn't download again on the day of the last download."""
        dated = self._nightly(f'tau-nightly-{self.today}.tgz', 'tau-2.36')
        os.symlink(os.path.basename(dated), os.path.join(self.src, 'tau-nightly.tgz'))
        with mock.patch.object(installation.util, 'download') as download:
            self.assertEqual(self._tag_and_source(update_nightly=True), (f'tau-2.36-{self.today}', dated))
        download.assert_not_called()

    @tests.skipIf(os.geteuid() == 0, "File permissions don't stop root from writing")
    def test_undated_readonly(self):
        """An archive only under the plain name in a read-only directory is dated by its modification time."""
        plain = self._nightly('tau-nightly.tgz', 'tau-2.35', date='2026-03-04')
        os.chmod(self.src, 0o555)
        self.assertEqual(self._tag_and_source(), ('tau-2.35-2026-03-04', plain))


def _set_mtime(path, date):
    timestamp = datetime.datetime.fromisoformat(date).timestamp()
    os.utime(path, (timestamp, timestamp), follow_symlinks=False)


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
        root, interpreter = _fake_python(headers=False)
        _touch(root, 'lib', _LIBPYTHON)
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn('Python.h', str(context.exception))

    def test_libdir(self):
        """The library is found in the LIBDIR that the Python interpreter reports."""
        root, interpreter = _fake_python()
        _touch(root, 'lib', _LIBPYTHON)
        self.assertEqual(python_build_paths(interpreter), (os.path.join(root, 'include', 'python3.99'),
                                                           os.path.join(root, 'lib')))

    def test_relocated(self):
        """A relocated Python, whose LIBDIR still has its build prefix, is found beside its standard library."""
        root, interpreter = _fake_python(LIBDIR='/nonexistent-build-prefix/lib',
                                         LIBDEST='/nonexistent-build-prefix/lib/python3.99')
        _touch(root, 'lib', _LIBPYTHON)
        self.assertEqual(python_build_paths(interpreter)[1], os.path.join(root, 'lib'))

    def test_other_version(self):
        """Another Python version's library isn't used."""
        root, interpreter = _fake_python()
        _touch(root, 'lib', f'libpython3.98.{SHARED_LIBRARY_SUFFIX}')
        _touch(root, 'lib', f'libpython3.{SHARED_LIBRARY_SUFFIX}')
        _touch(root, 'lib', 'python3.99', 'config-3.99', f'libpython3.98.{SHARED_LIBRARY_SUFFIX}')
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn(_LIBPYTHON, str(context.exception))

    def test_free_threaded(self):
        """For a free-threaded Python interpreter the library with ABI flags is chosen."""
        root, interpreter = _fake_python(LDVERSION='3.99t')
        _touch(root, 'lib', _LIBPYTHON)
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn(f'libpython3.99t.{SHARED_LIBRARY_SUFFIX}', str(context.exception))
        _touch(root, 'lib', f'libpython3.99t.{SHARED_LIBRARY_SUFFIX}')
        self.assertEqual(python_build_paths(interpreter)[1], os.path.join(root, 'lib'))

    def test_static_interpreter(self):
        """A Python whose interpreter links libpython statically but still provides a shared one is detected."""
        root, interpreter = _fake_python()
        _touch(root, 'lib', 'libpython3.99.a')
        with self.assertRaises(ConfigurationError) as context:
            python_build_paths(interpreter)
        self.assertIn(_LIBPYTHON, str(context.exception))
        _touch(root, 'lib', _LIBPYTHON)
        self.assertEqual(python_build_paths(interpreter)[1], os.path.join(root, 'lib'))


_LIBPYTHON = f'libpython3.99.{SHARED_LIBRARY_SUFFIX}'


def _touch(*parts):
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8'):
        pass


def _fake_python(headers=True, **config):
    """Make a fake Python 3.99 installed in a new directory for testing purposes.

    Args:
        headers (bool): If True then the installation has ``Python.h``.
        **config: ``sysconfig`` configuration variables to override.

    Returns:
        tuple: (installation root, path to the interpreter).
    """
    root = tempfile.mkdtemp(dir=os.getcwd())
    stdlib = os.path.join(root, 'lib', 'python3.99')
    include_dir = os.path.join(root, 'include', 'python3.99')
    os.makedirs(stdlib)
    os.makedirs(include_dir)
    if headers:
        _touch(include_dir, 'Python.h')
    values = {'stdlib': stdlib, 'include': include_dir, 'LIBDIR': os.path.join(root, 'lib'), 'LIBDEST': stdlib,
              'LDVERSION': '3.99'}
    values.update(config)
    with open(os.path.join(root, 'config.json'), 'w', encoding='utf-8') as fout:
        json.dump(values, fout)
    interpreter = os.path.join(root, 'python3')
    with open(interpreter, 'w', encoding='utf-8') as fout:
        fout.write(f'#!/bin/sh\ncat "{root}/config.json"\n')
    os.chmod(interpreter, 0o755)
    return root, interpreter


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


class ExportDynamicConfigureTest(tests.TestCase):
    """Tests for exporting TAU's symbols from statically linked applications, which TAU's plugins call."""

    @staticmethod
    def _argv(target_arch, target_os):
        tau = TauInstallation({'tau': 'download'}, target_arch, target_os, TauInstallation.get_minimal().compilers)
        return UnwinderConfigureTest._configure_argv(tau)  # pylint: disable=protected-access

    def test_export_dynamic_requested(self):
        """TAU is asked to export its symbols where its configure doesn't by default."""
        for target_arch, target_os in (ARM64, LINUX), (ARM64, CRAY_CNL), (X86_64, CRAY_CNL):
            self.assertIn('-ENABLE_EXPORT_DYNAMIC', self._argv(target_arch, target_os), (target_arch, target_os))

    def test_export_dynamic_default(self):
        """TAU's configure is left to its own choice where it already exports TAU's symbols, or can't."""
        for target_arch, target_os in (X86_64, LINUX), (PPC64LE, LINUX), (ARM64, DARWIN):
            self.assertNotIn('-ENABLE_EXPORT_DYNAMIC', self._argv(target_arch, target_os), (target_arch, target_os))


class RuntimeSelectFileTest(tests.TestCase):
    """Tests for applying a select file when a dynamically linked application runs."""

    def _env(self, select_file, **kwargs):
        compilers = TauInstallation.get_minimal().compilers
        sources = {'tau': 'download', 'sqlite3': 'download'}
        tau = TauInstallation(sources, HOST_ARCH, HOST_OS, compilers, select_file=select_file, **kwargs)
        with mock.patch.object(Installation, 'runtime_config',
                               side_effect=lambda opts=None, env=None: (list(opts or []), dict(env or {}))), \
             mock.patch.object(TauInstallation, 'get_makefile', return_value=f'Makefile.tau-{tau.uid}'):
            return tau.runtime_config()[1]

    def _select_file(self, name):
        path = os.path.join(os.path.realpath(os.getcwd()), name)
        with open(path, 'w', encoding='utf-8') as fout:
            fout.write('BEGIN_EXCLUDE_LIST\nfoo\nEND_EXCLUDE_LIST\n')
        return path

    def test_filter_plugin(self):
        """TAU's filter plugin is loaded with the select file, alongside any other plugin."""
        path = self._select_file('select.tau')
        env = self._env(path, profile='sqlite')
        self.assertEqual(env['TAU_PLUGINS'].split(':'),
                         [f'libTAU-sqlite3-plugin.{SHARED_LIBRARY_SUFFIX}',
                          f'libTAU-filter-plugin.{SHARED_LIBRARY_SUFFIX}({path})'])
        self.assertNotIn('TAU_SELECT_FILE', env)

    def test_static_linkage(self):
        """A statically linked application's select file is applied when it's built, not when it runs."""
        env = self._env(self._select_file('select.tau'), application_linkage='static')
        self.assertNotIn('TAU_PLUGINS', env)

    def test_path_separators(self):
        """A select file whose path holds a character that separates TAU_PLUGINS entries is refused."""
        for name in 'a:b.tau', 'a,b.tau', 'a)b.tau':
            with self.assertRaises(ConfigurationError, msg=name):
                self._env(self._select_file(name))

    def test_long_path(self):
        """A select file whose path makes TAU_PLUGINS too long for TAU is refused."""
        # The path isn't created: it's longer than macOS allows.
        path = os.path.join(os.path.realpath(os.getcwd()), *['d' * 200] * 5, 'select.tau')
        with self.assertRaises(ConfigurationError):
            self._env(path)


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


class TauNightlySourceTest(tests.TestCase):
    """Tests for the sources of a TAU installation given the 'nightly' keyword."""

    def test_nightly_resolves_to_url(self):
        """'nightly' downloads the nightly archive, and error messages name its URL rather than the keyword."""
        tau = TauInstallation({'tau': 'nightly'}, HOST_ARCH, HOST_OS, TauInstallation.get_minimal().compilers)
        self.assertEqual(tau.src, NIGHTLY)
        self.assertEqual(tau.srcs, [])
        self.assertEqual(tau.srcs_avail, [NIGHTLY])


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

    def test_rewritten_appfile_in_temporary_directory(self):
        """The rewritten file goes to a new directory, never beside or over the user's file, for any path form."""
        absolute = self._write_appfile('-np 2 ls')
        os.makedirs('cfg', exist_ok=True)
        relative = os.path.join('cfg', 'app.cfg')
        shutil.copy(absolute, relative)
        for appfile in (absolute, relative):
            with self.subTest(appfile=appfile):
                cmd = TauInstallation._rewrite_launcher_appfile_cmd(
                    None, ['mpirun', '--app=' + appfile], self._TAU_EXEC)
                rewritten = cmd[1][len('--app='):]
                self.assertEqual(os.path.basename(rewritten), 'app.cfg.tau')
                self.assertNotEqual(os.path.dirname(rewritten), os.path.dirname(os.path.abspath(appfile)))
                self.assertEqual(self._read_lines(rewritten), [['-np', '2'] + self._TAU_EXEC + ['ls']])

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
        with self.assertRaises(InternalError) as ctx:
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '--mca=btl=tcp'], self._TAU_EXEC)
        self.assertIn('None of', ctx.exception.value)

    def test_unknown_launcher_rejected(self):
        """Launchers without a known application-file flag cannot be rewritten."""
        appfile = self._write_appfile('-np 2 ls')
        for launcher in ('aprun', 'my_launcher'):
            with self.assertRaises(InternalError):
                TauInstallation._rewrite_launcher_appfile_cmd(None, [launcher, '--app', appfile], self._TAU_EXEC)

    def test_missing_appfile_flag_rejected(self):
        """A space-separated flag at the end of the command has no value, so the command cannot be parsed."""
        with self.assertRaises(InternalError) as ctx:
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '-np', '4'], self._TAU_EXEC)
        self.assertIn('Unable to parse', ctx.exception.value)

    def test_line_without_executable_rejected(self):
        """A command line that names no executable is a configuration error, not silently passed through."""
        appfile = self._write_appfile('-np 2 no_such_program_for_taucmdr_tests')
        with self.assertRaises(ConfigurationError):
            TauInstallation._rewrite_launcher_appfile_cmd(None, ['mpirun', '-app', appfile], self._TAU_EXEC)


def _script(path: str, body: str) -> str:
    """Write an executable shell script to `path` that runs `body`, and return `path`."""
    with open(path, 'w') as fout:
        fout.write(f'#!/bin/sh\n{body}\n')
    os.chmod(path, 0o755)
    return path


# What GNU gcc prints for --version, which identifies it as a GNU compiler.
_GCC_VERSION = 'echo "gcc (GCC) 14.2.0"; echo "Copyright (C) 2024 Free Software Foundation, Inc."'


class TauMakefileTargetTest(tests.TestCase):
    """Tests for :any:`tau_makefile_target`."""

    def test_cray_cc(self):
        """A Cray ``cc`` in ``FULL_CC`` is the host C compiler, though Cray's UPC compiler is also ``cc``.

        The ``cc`` wraps a GNU ``gcc``, which is also a host C compiler, but the wrapper stays the C compiler.
        """
        bindir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        gcc = _script(os.path.join(bindir, 'gcc'), _GCC_VERSION)
        # With -craype-verbose, craype's wrappers print the command they run.
        cray_cc = _script(os.path.join(bindir, 'cc'), f'echo "{gcc} --version -E"')
        _, makefile = _tau_tree(HOST_TAU_MAGIC.name, HOST_TAU_MAGIC.name, extra=f'FULL_CC={cray_cc}\n')
        self.assertEqual(tau_makefile_target(makefile)[CC.keyword], cray_cc)

    def test_caf(self):
        """``TAU_F90=caf`` sets the coarray Fortran compiler to ``caf`` and the Fortran compiler to its ``gfortran``."""
        bindir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        gfortran = _script(os.path.join(bindir, 'gfortran'),
                           'echo "GNU Fortran (GCC) 14.2.0"; echo "Copyright (C) 2024 Free Software Foundation, Inc."')
        caf = _script(os.path.join(bindir, 'caf'), f'echo "{gfortran} -fcoarray=lib -lcaf_mpi"')
        _, makefile = _tau_tree(HOST_TAU_MAGIC.name, HOST_TAU_MAGIC.name, extra=f'TAU_F90={caf}\n')
        found = tau_makefile_target(makefile)
        self.assertEqual(found[CAF_FC.keyword], caf)
        self.assertEqual(found[FC.keyword], gfortran)

    def test_skipped_compilers(self):
        """A compiler that isn't there, or that TAU Commander doesn't know, is left out with no error."""
        bindir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        unknown = _script(os.path.join(bindir, 'notacompiler'), 'exit 0')
        extra = f'FULL_CC={bindir}/missing-cc\nFULL_CXX={unknown}\n'
        _, makefile = _tau_tree(HOST_TAU_MAGIC.name, HOST_TAU_MAGIC.name, extra=extra)
        with self.assertLogs('taucmdr.cf.software.tau_installation', 'WARNING') as logs:
            found = tau_makefile_target(makefile)
        self.assertNotIn(CC.keyword, found)
        self.assertNotIn(CXX.keyword, found)
        self.assertIn('Failed to parse FULL_CC', logs.output[0])

    def test_makefile_syntax(self):
        """Lines without ``=`` are skipped, and ``$(TAU_R)`` in a compiler path is expanded."""
        bindir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        gcc = _script(os.path.join(bindir, 'gcc'), _GCC_VERSION)
        lines = ['include other.mk', f'TAU_R={bindir}', 'FULL_CC=$(TAU_R)/gcc -O2']
        _, makefile = _tau_tree(HOST_TAU_MAGIC.name, HOST_TAU_MAGIC.name,
                                extra=''.join(f'{line}\n' for line in lines))
        self.assertEqual(tau_makefile_target(makefile)[CC.keyword], gcc)

    def test_packages(self):
        """Package directories in the makefile are used if they exist, and an empty one means no package."""
        pkgdir = tempfile.mkdtemp(dir=tests.get_test_workdir())
        missing = os.path.join(pkgdir, 'missing')
        lines = [f'PDTDIR={pkgdir}', f'PAPIDIR={missing}', f'BFDINCLUDE=-I{pkgdir}/include', 'UNWIND_INC=']
        _, makefile = _tau_tree(HOST_TAU_MAGIC.name, HOST_TAU_MAGIC.name,
                                extra=''.join(f'{line}\n' for line in lines))
        with self.assertLogs('taucmdr.cf.software.tau_installation', 'WARNING') as logs:
            found = tau_makefile_target(makefile)
        self.assertEqual(found['pdt_source'], pkgdir)
        self.assertEqual(found['binutils_source'], pkgdir)
        self.assertIsNone(found['libunwind_source'])
        self.assertNotIn('papi_source', found)
        self.assertIn(f"'{missing}' referenced by TAU Makefile", logs.output[0])

    def test_shared_arch(self):
        """A ``TAU_ARCH`` that several platforms share is the host's; on another host the error lists them."""
        _, makefile = _tau_tree('craycnl', 'craycnl')
        module = 'taucmdr.cf.software.tau_installation'
        with mock.patch.multiple(module, HOST_ARCH=X86_64, HOST_OS=CRAY_CNL):
            found = tau_makefile_target(makefile)
        self.assertEqual((found['host_arch'], found['host_os']), (X86_64.name, CRAY_CNL.name))
        with mock.patch.multiple(module, HOST_ARCH=X86_64, HOST_OS=LINUX), \
             self.assertRaises(ConfigurationError) as ctx:
            tau_makefile_target(makefile)
        self.assertIn('ambiguous TAU architecture: craycnl', ctx.exception.value)
        self.assertIn('CNL on x86_64', ctx.exception.value)
        self.assertIn('CNL on aarch64', ctx.exception.value)
