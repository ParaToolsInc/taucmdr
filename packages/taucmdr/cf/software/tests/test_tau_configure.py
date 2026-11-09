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

Functions used for unit tests of how tau_installation.py configures, selects, and runs TAU.
Nothing is built: subprocesses, installation prefixes, and makefile lookups are mocked.
"""

import os
from types import SimpleNamespace
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError, InternalError
from taucmdr.cf.compiler.host import CC, CXX
from taucmdr.cf.compiler.python import PY
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, SHARED_LIBRARY_SUFFIX
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software import tau_installation
from taucmdr.cf.software.installation import Installation
from taucmdr.cf.software.tau_installation import TauInstallation
from taucmdr.cf.software.tests import test_tau_installation


def _tau(**kwargs):
    """Return a TauInstallation for the host built with the minimal compilers."""
    return TauInstallation({'tau': 'download', 'ompt': 'download'}, HOST_ARCH, HOST_OS,
                           TauInstallation.get_minimal().compilers, **kwargs)


def _makefile(*tags):
    """Return a TAU makefile path whose name carries `tags`."""
    return os.path.join(os.sep, 'tau', 'lib', '-'.join(['Makefile.tau', *tags]))


def _base_config(opts=None, env=None):
    """Stand-in for Installation's compile-time and runtime configuration, which needs an install prefix."""
    return list(opts or []), dict(env or {})


class _FakeCompiler:
    """Just enough of InstalledCompiler for configure() to build its flag list."""
    # pylint: disable=too-few-public-methods

    def __init__(self, command, family, version=None):
        self.absolute_path = '/opt/compilers/bin/' + command
        self.version = version
        self.uid = command
        self.info = SimpleNamespace(command=command, family=SimpleNamespace(name=family))

    def unwrap(self):
        """Fake compilers never wrap anything."""
        return self


class RuntimeConfigTest(tests.TestCase):
    """Tests for the tau_exec options and environment from :any:`TauInstallation.runtime_config`."""

    @staticmethod
    def _runtime_config(tau):
        with mock.patch.object(Installation, 'runtime_config', side_effect=_base_config), \
             mock.patch.object(TauInstallation, 'get_makefile', return_value=_makefile(tau.uid)):
            return tau.runtime_config()

    def test_profile_formats(self):
        """Each profile format sets exactly the TAU and Score-P variables it needs."""
        tau = _tau()
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_PROFILE'], '1')
        self.assertNotIn('TAU_PROFILE_FORMAT', env)
        self.assertNotIn('TAU_PLUGINS', env)
        tau.profile = 'merged'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_PROFILE'], '1')
        self.assertEqual(env['TAU_PROFILE_FORMAT'], 'merged')
        tau.profile = 'cubex'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['SCOREP_ENABLE_PROFILING'], '1')
        tau.profile = 'sqlite'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_PROFILE'], '0')
        self.assertEqual(env['TAU_PLUGINS'], f'libTAU-sqlite3-plugin.{SHARED_LIBRARY_SUFFIX}')
        tau.profile = 'none'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_PROFILE'], '0')
        self.assertEqual(env['SCOREP_ENABLE_PROFILING'], 'false')

    def test_trace_formats(self):
        """Each trace format sets exactly the TAU and Score-P variables it needs."""
        tau = _tau(trace='slog2')
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_TRACE'], '1')
        self.assertNotIn('TAU_TRACE_FORMAT', env)
        tau.trace = 'otf2'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_TRACE'], '1')
        self.assertEqual(env['TAU_TRACE_FORMAT'], 'otf2')
        tau.trace = 'none'
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_TRACE'], '0')
        self.assertEqual(env['SCOREP_ENABLE_TRACING'], 'false')

    def test_openmp(self):
        """OMPT measurement adds -ompt and the OMPT environment; ignoring OpenMP adds neither."""
        opts, env = self._runtime_config(_tau(openmp_support=True, measure_openmp='ignore'))
        self.assertNotIn('-ompt', opts)
        self.assertNotIn('TAU_OMPT_SUPPORT_LEVEL', env)
        opts, env = self._runtime_config(_tau(openmp_support=True, measure_openmp='ompt'))
        self.assertIn('-ompt', opts)
        self.assertEqual(env['TAU_OMPT_SUPPORT_LEVEL'], 'full')
        self.assertEqual(env['TAU_OMPT_RESOLVE_ADDRESS_EAGERLY'], '1')

    def test_sampling(self):
        """Sampling enables -ebs and uses TAU's default period unless one was given."""
        tau = _tau(sample=True, sample_resolution='line')
        opts, env = self._runtime_config(tau)
        self.assertIn('-ebs', opts)
        self.assertEqual(env['TAU_SAMPLING'], '1')
        self.assertEqual(env['TAU_EBS_RESOLUTION'], 'line')
        self.assertEqual(env['TAU_EBS_PERIOD'], '10000')
        tau.sampling_period = 5000
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_EBS_PERIOD'], '5000')
        tau.sample = False
        opts, env = self._runtime_config(tau)
        self.assertNotIn('-ebs', opts)
        self.assertEqual(env['TAU_SAMPLING'], '0')
        self.assertNotIn('TAU_EBS_PERIOD', env)

    def test_unwinding(self):
        """Unwind depth is exported only when it is set."""
        _, env = self._runtime_config(_tau())
        self.assertNotIn('TAU_EBS_UNWIND', env)
        self.assertNotIn('TAU_EBS_UNWIND_DEPTH', env)
        _, env = self._runtime_config(_tau(unwind_depth=3))
        self.assertEqual(env['TAU_EBS_UNWIND'], '1')
        self.assertEqual(env['TAU_EBS_UNWIND_DEPTH'], '3')

    def test_throttle_and_callpath(self):
        """Throttle limits and callpath depth are exported only when enabled."""
        tau = _tau(throttle=True, throttle_per_call=10, throttle_num_calls=100000, callpath_depth=2)
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_THROTTLE'], '1')
        self.assertEqual(env['TAU_THROTTLE_PERCALL'], '10')
        self.assertEqual(env['TAU_THROTTLE_NUMCALLS'], '100000')
        self.assertEqual(env['TAU_CALLPATH'], '1')
        self.assertEqual(env['TAU_CALLPATH_DEPTH'], '2')
        tau.throttle = False
        tau.callpath_depth = 0
        _, env = self._runtime_config(tau)
        self.assertEqual(env['TAU_THROTTLE'], '0')
        self.assertNotIn('TAU_THROTTLE_PERCALL', env)
        self.assertNotIn('TAU_CALLPATH', env)

    def test_feature_options(self):
        """Every runtime feature maps to its tau_exec option."""
        tau = _tau(openacc_support=True, measure_cuda=True, measure_level_zero=True, measure_opencl=True,
                   measure_io=True, measure_memory_alloc=True, measure_shmem=True, ptts=True, ptts_post=True,
                   ptts_sample_flags='-x', ptts_report_flags='-y')
        tau.verbose = True
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        opts, env = self._runtime_config(tau)
        for opt in ('-v', '-cupti', '-openacc', '-l0', '-opencl', '-io', '-memory', '-shmem',
                    '-ptts', '-ptts-post', '-ptts-sample-flags=-x', '-ptts-report-flags=-y'):
            self.assertIn(opt, opts)
        self.assertEqual(env['TAU_VERBOSE'], '1')
        self.assertEqual(env['TAU_SHOW_MEMORY_FUNCTIONS'], '1')

    def test_cuda_without_cupti(self):
        """CUDA measurement without CUPTI headers cannot ask tau_exec for -cupti."""
        tau = _tau(measure_cuda=True)
        self.assertIsNone(tau.cupti_prefix)
        opts, _ = self._runtime_config(tau)
        self.assertNotIn('-cupti', opts)

    def test_defaults_are_minimal(self):
        """With no features enabled tau_exec gets no options and TAU sees only the wall clock."""
        tau = _tau()
        tau.verbose = False
        opts, env = self._runtime_config(tau)
        self.assertEqual(opts, [])
        self.assertEqual(env['TAU_METRICS'], 'TIME,')
        self.assertEqual(env['TAU_VERBOSE'], '0')


class CompiletimeConfigTest(tests.TestCase):
    """Tests for the TAU_OPTIONS and compiler options from :any:`TauInstallation.compiletime_config`."""

    @staticmethod
    def _compiletime_config(tau, makefile=None):
        with mock.patch.object(Installation, 'compiletime_config', side_effect=_base_config), \
             mock.patch.object(TauInstallation, 'get_makefile', return_value=makefile or _makefile(tau.uid)):
            opts, env = tau.compiletime_config(tau.compilers[CC])
        return opts, env, env.get('TAU_OPTIONS', '').split()

    def test_baseline_returns_early(self):
        """Baseline builds get no TAU_OPTIONS or TAU_MAKEFILE at all."""
        opts, env, _ = self._compiletime_config(_tau(baseline=True))
        self.assertEqual(opts, [])
        self.assertNotIn('TAU_OPTIONS', env)
        self.assertNotIn('TAU_MAKEFILE', env)

    def test_runtime_only_instrumentation(self):
        """No source or compiler instrumentation: link only, no compiler options, real makefile exported."""
        tau = _tau(source_inst='never', compiler_inst='never')
        opts, env, tau_opts = self._compiletime_config(tau)
        self.assertIn('-optLinkOnly', tau_opts)
        self.assertIn('-optNoCompInst', tau_opts)
        self.assertNotIn('-optRevert', tau_opts)
        self.assertFalse(any(opt.startswith('-optAppCC=') for opt in tau_opts))
        self.assertNotIn('-g', opts)
        self.assertNotIn('-DTAU_ENABLED=1', opts)
        self.assertEqual(env['TAU_MAKEFILE'], _makefile(tau.uid))

    def test_full_instrumentation(self):
        """Source plus compiler instrumentation turns on every matching TAU compiler option."""
        tau = _tau(source_inst='automatic', compiler_inst='always', keep_inst_files=True, reuse_inst_files=True,
                   select_file='select.tau', measure_memory_alloc=True, openmp_support=True)
        tau.verbose = True
        compiler = tau.compilers[CC]
        opts, _, tau_opts = self._compiletime_config(tau)
        for opt in ('-optRevert', '-optVerbose', '-optCompInst', '-optKeepFiles', '-optReuseFiles',
                    '-optMemDbg', '-optContinueBeforeOMP',
                    '-optAppCC=' + compiler.absolute_path,
                    '-optAppCXX=' + compiler.absolute_path,
                    '-optAppF90=' + compiler.absolute_path,
                    '-optTauSelectFile=' + os.path.realpath(os.path.abspath('select.tau'))):
            self.assertIn(opt, tau_opts)
        self.assertNotIn('-optLinkOnly', tau_opts)
        self.assertNotIn('-optNoCompInst', tau_opts)
        self.assertIn('-g', opts)
        self.assertIn('-DTAU_ENABLED=1', opts)

    def test_fallback_instrumentation(self):
        """Fallback compiler instrumentation reverts to the plain compiler when TAU's wrapper fails."""
        opts, _, tau_opts = self._compiletime_config(_tau(source_inst='never', compiler_inst='fallback'))
        self.assertIn('-optRevert', tau_opts)
        self.assertNotIn('-optCompInst', tau_opts)
        self.assertNotIn('-optNoCompInst', tau_opts)
        self.assertIn('-g', opts)

    def test_manual_source_instrumentation(self):
        """Manual source instrumentation links only but still defines TAU_ENABLED for the user's macros."""
        tau = _tau(source_inst='manual', compiler_inst='never')
        opts, _, tau_opts = self._compiletime_config(tau)
        self.assertIn('-optLinkOnly', tau_opts)
        self.assertIn('-optNoCompInst', tau_opts)
        self.assertIn('-optAppCC=' + tau.compilers[CC].absolute_path, tau_opts)
        self.assertIn('-DTAU_ENABLED=1', opts)

    def test_forced_options_replace_defaults(self):
        """Forced TAU options are used verbatim instead of the derived set."""
        tau = _tau()
        tau.force_tau_options = ['-optForced']
        _, env, _ = self._compiletime_config(tau)
        self.assertEqual(env['TAU_OPTIONS'], '-optForced')

    def test_extra_options_are_added(self):
        """Extra TAU options are merged with the derived set."""
        tau = _tau(source_inst='never', compiler_inst='never')
        tau.extra_tau_options = ['-optExtra']
        _, _, tau_opts = self._compiletime_config(tau)
        self.assertIn('-optExtra', tau_opts)
        self.assertIn('-optLinkOnly', tau_opts)

    def test_warns_on_foreign_makefile(self):
        """A makefile that does not carry our UID is used, with a warning."""
        foreign = _makefile('foreign', 'mpi')
        with self.assertLogs(tau_installation.LOGGER, level='WARNING') as logs:
            _, env, _ = self._compiletime_config(_tau(), makefile=foreign)
        self.assertIn('compiler compatibility', logs.output[0])
        self.assertEqual(env['TAU_MAKEFILE'], foreign)


class TagsTest(tests.TestCase):
    """Tests for :any:`TauInstallation.get_tags` and the tags a configuration must not approximate."""
    # pylint: disable=protected-access

    def test_opari(self):
        """OPARI measurement is tagged openmp+opari."""
        tags = _tau(openmp_support=True, measure_openmp='opari').get_tags()
        self.assertTrue({'openmp', 'opari'} <= tags)
        self.assertNotIn('ompt', tags)

    def test_openmp_ignored_uses_pthread(self):
        """An OpenMP application whose directives are not measured only needs thread support."""
        tags = _tau(openmp_support=True, measure_openmp='ignore').get_tags()
        self.assertIn('pthread', tags)
        self.assertNotIn('openmp', tags)

    def test_pthreads_take_precedence(self):
        """Explicit pthread support wins over OpenMP tagging."""
        tags = _tau(pthreads_support=True, openmp_support=True, measure_openmp='ompt').get_tags()
        self.assertIn('pthread', tags)
        self.assertFalse({'openmp', 'ompt'} & tags)

    def test_invalid_openmp_measurement(self):
        """An unknown OpenMP measurement method is an internal error."""
        tau = _tau(openmp_support=True)
        tau.measure_openmp = 'bogus'
        with self.assertRaises(InternalError):
            tau.get_tags()

    def test_features(self):
        """Every application feature and user tag appears in the tag set."""
        tau = _tau(tbb_support=True, mpi_support=True, openacc_support=True, shmem_support=True, mpc_support=True,
                   mpit=True, measure_level_zero=True, tags=['custom'])
        uid = tau.uid
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        tau.uses_python = True
        tags = tau.get_tags()
        self.assertIn(uid, tags)
        self.assertTrue({'tbb', 'mpi', 'acc', 'cupti', 'shmem', 'mpc', 'python', 'mpit',
                         'level_zero', 'custom'} <= tags)

    def test_dependencies(self):
        """PDT, PAPI, and Score-P are tagged only when the configuration uses them."""
        tau = _tau()
        self.assertFalse({'pdt', 'papi', 'scorep'} & tau.get_tags())
        tau.uses_pdt = tau.uses_papi = tau.uses_scorep = True
        self.assertTrue({'pdt', 'papi', 'scorep'} <= tau.get_tags())

    def test_incompatible_tags_without_features(self):
        """Makefiles for features the configuration lacks must never be approximated."""
        tags = _tau()._incompatible_tags()
        self.assertTrue({'mpi', 'openmp', 'opari', 'ompt', 'gomp', 'scorep', 'shmem'} <= tags)

    def test_incompatible_tags_with_features(self):
        """Features the configuration uses are never incompatible."""
        tau = _tau(mpi_support=True, openmp_support=True, measure_openmp='ompt', shmem_support=True)
        tau.uses_scorep = True
        self.assertFalse({'mpi', 'openmp', 'opari', 'ompt', 'scorep', 'shmem'} & tau._incompatible_tags())


class ConfigureTest(tests.TestCase):
    """Tests for the flags :any:`TauInstallation.configure` gives TAU's configure script."""

    def _flags(self, tau):
        argv = test_tau_installation.UnwinderConfigureTest._configure_argv(tau)  # pylint: disable=protected-access
        self.assertEqual(argv[0], './configure')
        return argv[1:]

    def _useropts(self, flags):
        useropts = [flag for flag in flags if flag.startswith('-useropt=')]
        self.assertEqual(len(useropts), 1)
        return useropts[0][len('-useropt='):].split('#')

    @staticmethod
    def _ompt_tau(compilers=None):
        """An OMPT configuration whose OMPT runtime is installed at /fake/ompt."""
        tau = _tau(openmp_support=True, measure_openmp='ompt')
        if compilers:
            tau.compilers = compilers
        tau.dependencies = {'ompt': SimpleNamespace(install_prefix='/fake/ompt', uid='ompt')}
        return tau

    @staticmethod
    def _intel(version):
        return {CC: _FakeCompiler('icc', 'Intel', version=version),
                CXX: _FakeCompiler('icpc', 'Intel', version=version)}

    def test_default_flags(self):
        """A serial, single-threaded configuration passes tag, arch, compilers, and the default useropts."""
        tau = _tau()
        flags = self._flags(tau)
        self.assertIn(f'-tag={tau.uid}', flags)
        self.assertIn(f'-arch={tau.tau_magic.name}', flags)
        self.assertTrue(any(flag.startswith('-cc=') for flag in flags))
        self.assertTrue(any(flag.startswith('-c++=') for flag in flags))
        for flag in ('-openmp', '-pthread', '-opari', '-mpi'):
            self.assertNotIn(flag, flags)
        self.assertFalse([flag for flag in flags if flag.startswith(('-ompt', '-python'))], flags)
        self.assertIn('-useropt=-O2#-g', flags)

    def test_ompt_flags(self):
        """OMPT points TAU at the OMPT runtime and adds its include path for omp-tools.h."""
        flags = self._flags(self._ompt_tau())
        self.assertIn('-openmp', flags)
        self.assertIn('-ompt=/fake/ompt', flags)
        self.assertNotIn('-pthread', flags)
        self.assertIn('-I/fake/ompt/include', self._useropts(flags))

    def test_ompt_for_intel_19(self):
        """Intel 19 and later ship their own OMPT runtime, so TAU is configured with a bare -ompt."""
        tau = self._ompt_tau(self._intel((19, 1, 0)))
        flags = self._flags(tau)
        self.assertIn(f'-tag={tau.uid}', flags)
        self.assertIn('-cc=icc', flags)
        self.assertIn('-c++=icpc', flags)
        self.assertIn('-ompt', flags)
        self.assertNotIn('-ompt=/fake/ompt', flags)
        self.assertFalse(any(flag.startswith('-fortran=') for flag in flags))
        self.assertFalse([opt for opt in self._useropts(flags) if opt.startswith('-I')])

    def test_ompt_prefix_for_older_intel(self):
        """Intel before 19, or an unknown version, still needs the downloaded OMPT runtime."""
        for version in (18, 0, 3), None:
            with self.subTest(version=version):
                flags = self._flags(self._ompt_tau(self._intel(version)))
                self.assertIn('-ompt=/fake/ompt', flags)
                self.assertNotIn('-ompt', flags)

    def test_ompt_without_dependency(self):
        """OMPT without a managed OMPT runtime enables OpenMP but passes no OMPT flags."""
        tau = _tau(openmp_support=True, measure_openmp='ompt')
        uid = tau.uid
        tau.dependencies.pop('ompt')
        flags = self._flags(tau)
        self.assertIn(f'-tag={uid}', flags)
        self.assertIn('-openmp', flags)
        self.assertFalse(any(flag.startswith('-ompt') for flag in flags))
        self.assertFalse(any(opt.startswith('-I') for opt in self._useropts(flags)))

    def test_opari_flags(self):
        """OPARI measurement configures TAU with -openmp -opari."""
        flags = self._flags(_tau(openmp_support=True, measure_openmp='opari'))
        self.assertIn('-openmp', flags)
        self.assertIn('-opari', flags)
        self.assertFalse(any(flag.startswith('-ompt') for flag in flags))

    def test_threading_flags(self):
        """Ignored OpenMP and explicit pthreads both configure TAU with -pthread only."""
        for kwargs in {'openmp_support': True, 'measure_openmp': 'ignore'}, {'pthreads_support': True}:
            with self.subTest(**kwargs):
                flags = self._flags(_tau(**kwargs))
                self.assertIn('-pthread', flags)
                self.assertNotIn('-openmp', flags)

    def test_invalid_openmp_measurement(self):
        """An unknown OpenMP measurement method is caught before configure runs."""
        tau = _tau(openmp_support=True)
        tau.measure_openmp = 'bogus'
        tau._src_prefix = os.getcwd()  # pylint: disable=protected-access
        with mock.patch('taucmdr.util.create_subprocess', return_value=0) as run:
            with self.assertRaises(InternalError):
                tau.configure()
        run.assert_not_called()

    def test_feature_flags(self):
        """Each measurement or application feature maps to its configure flag."""
        tau = _tau(measure_io=True, dyninst=True, mpit=True, measure_level_zero=True, tbb_support=True,
                   openacc_support=True, opencl_prefix='/opt/opencl')
        tau.uses_cuda = True
        tau.cuda_prefix = '/opt/cuda'
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        flags = self._flags(tau)
        for flag in ('-iowrapper', '-dyninst=download', '-mpit', '-level_zero', '-tbb', '-openacc',
                     '-cuda=/opt/cuda', '-cupti=/opt/cuda/extras/CUPTI', '-opencl=/opt/opencl'):
            self.assertIn(flag, flags)

    def test_level_zero_dependency_prefix(self):
        """A managed Level Zero runtime is passed by prefix instead of the bare -level_zero flag."""
        tau = _tau(measure_level_zero=True)
        tau.dependencies['level_zero'] = SimpleNamespace(install_prefix='/fake/level_zero', uid='level_zero')
        flags = self._flags(tau)
        self.assertIn('-level_zero=/fake/level_zero', flags)
        self.assertNotIn('-level_zero', flags)

    def test_python_flags(self):
        """Python support passes the interpreter's real path and its header and library directories."""
        tau = _tau()
        uid = tau.uid
        python = _FakeCompiler('python3', 'Python')
        tau.compilers = {CC: tau.compilers[CC], CXX: tau.compilers[CXX], PY: python}
        tau.uses_python = True
        with mock.patch.object(tau_installation, 'python_build_paths',
                               return_value=('/py/include/python3.99', '/py/lib')) as build_paths:
            flags = self._flags(tau)
        build_paths.assert_called_once_with(python.absolute_path)
        self.assertIn(f'-tag={uid}', flags)
        self.assertIn('-python=' + os.path.realpath(python.absolute_path), flags)
        self.assertIn('-pythoninc=/py/include/python3.99', flags)
        self.assertIn('-pythonlib=/py/lib', flags)
        self.assertFalse(any(flag.startswith('-pythonlibrary') for flag in flags))

    def test_minimal(self):
        """The minimal configuration names only the tag, the arch, and the unwinder."""
        tau = TauInstallation.get_minimal()
        flags = self._flags(tau)
        self.assertIn(f'-tag={tau.uid}', flags)
        self.assertIn(f'-arch={tau.tau_magic.name}', flags)
        self.assertFalse(any(flag.startswith('-cc=') for flag in flags))
        self.assertFalse(any(flag.startswith('-useropt=') for flag in flags))

    def test_failure_raises(self):
        """A nonzero exit from TAU's configure script is a package error for full and minimal builds."""
        for tau in _tau(), TauInstallation.get_minimal():
            tau._src_prefix = os.getcwd()  # pylint: disable=protected-access
            with self.subTest(minimal=tau.minimal), \
                 mock.patch('taucmdr.util.create_subprocess', return_value=1), \
                 self.assertRaises(SoftwarePackageError):
                tau.configure()


class GetMakefileTest(tests.TestCase):
    """Tests for :any:`TauInstallation.get_makefile`."""
    # pylint: disable=protected-access

    _LIB_PATH = os.path.join(os.sep, 'tau', 'lib')

    def _get_makefile(self, tau, *makefiles):
        with mock.patch.object(TauInstallation, 'lib_path', new_callable=mock.PropertyMock,
                               return_value=self._LIB_PATH), \
             mock.patch.object(TauInstallation, 'install_prefix', new_callable=mock.PropertyMock,
                               return_value=os.path.dirname(self._LIB_PATH)), \
             mock.patch('glob.glob', return_value=list(makefiles)):
            return tau.get_makefile()

    def test_forced(self):
        """A forced makefile is returned as-is and cached."""
        forced = _makefile('forced')
        tau = _tau(forced_makefile=forced)
        self.assertEqual(self._get_makefile(tau), forced)
        self.assertEqual(tau._tau_makefile, forced)

    def test_matches_configuration(self):
        """The makefile is found from the configuration tags alone, cached, and carries the configuration's UID."""
        tau = _tau()
        exact = _makefile(tau.uid)
        self.assertEqual(self._get_makefile(tau, _makefile(tau.uid, 'mpi'), exact), exact)
        self.assertEqual(tau._tau_makefile, exact)
        self.assertEqual(self._get_makefile(tau), exact)
        self.assertIn(tau.uid, tau._makefile_tags(exact))

    def test_unknown_tags_raise(self):
        """No installed makefile carries an unknown tag, managed or not."""
        tau = _tau(tags=['no-such-tag'])
        with self.assertRaises(SoftwarePackageError):
            self._get_makefile(tau, _makefile(tau.uid))
        tau.unmanaged = True
        with self.assertRaises(SoftwarePackageError):
            self._get_makefile(tau, _makefile(tau.uid))


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
        with mock.patch.dict(os.environ, {'PE_ENV': 'GNU'}):
            for var in 'DARSHAN_PRELOAD', 'LOADEDMODULES':
                os.environ.pop(var, None)
            TauInstallation.check_env_compat()


class ApplicationCommandTest(tests.TestCase):
    """Tests for :any:`TauInstallation.get_application_command` without a TAU installation."""
    # pylint: disable=protected-access

    _LAUNCHER = ['mpirun', '-np', '4']

    @staticmethod
    def _launch(tau, launcher, apps, makefile=None):
        with mock.patch.object(TauInstallation, 'install'), \
             mock.patch.object(TauInstallation, 'runtime_config', return_value=([], {})), \
             mock.patch.object(TauInstallation, 'get_makefile', return_value=makefile or _makefile(tau.uid, 'mpi')):
            cmd, _ = tau.get_application_command(list(launcher), apps)
        return cmd

    def test_baseline_uses_tau_baseline(self):
        """Baseline measurements run everything under tau_baseline without touching the makefile."""
        tau = _tau(mpi_support=True, baseline=True)
        cmd = self._launch(tau, self._LAUNCHER, [['./a.out', '-x'], [':', '-np', '2', './b.out']])
        self.assertEqual(cmd, ['tau_baseline', 'mpirun', '-np', '4', './a.out', '-x', ':', '-np', '2', './b.out'])

    def test_site_launcher_args_appended(self):
        """Site-specific launcher arguments from the environment follow the launcher, ahead of tau_exec."""
        with mock.patch.dict(os.environ, {'__TAUCMDR_LAUNCHER_ARGS__': '--bind-to core'}):
            cmd = self._launch(_tau(mpi_support=True), self._LAUNCHER, [['./a.out']])
        self.assertEqual(cmd[:5], ['mpirun', '-np', '4', '--bind-to', 'core'])
        self.assertEqual(cmd[5], 'tau_exec')

    def test_mpmd_wraps_each_executable(self):
        """Every MPMD command gets its own tau_exec; launcher flags between commands are untouched."""
        tau = _tau(mpi_support=True)
        cmd = self._launch(tau, self._LAUNCHER, [['ls', '-l'], [':', '-np', '2', 'hostname']])
        tags = cmd[5]
        self.assertEqual(set(tags.split(',')), {tau.uid, 'mpi'})
        self.assertEqual(cmd, ['mpirun', '-np', '4', 'tau_exec', '-T', tags, 'ls', '-l',
                               ':', '-np', '2', 'tau_exec', '-T', tags, 'hostname'])

    def test_mpmd_command_without_executable_rejected(self):
        """An MPMD command that names no executable cannot be wrapped."""
        with self.assertRaises(InternalError):
            self._launch(_tau(mpi_support=True), self._LAUNCHER,
                         [['./a.out'], [':', '-np', '2', 'no_such_program_for_taucmdr_tests']])

    def test_appfile_launch_rewrites_appfile(self):
        """With no application command the launcher's application file is rewritten instead."""
        appfile = os.path.abspath('app.cfg')
        with open(appfile, 'w', encoding='utf-8') as fout:
            fout.write('-np 2 ls\n')
        cmd = self._launch(_tau(mpi_support=True), ['mpirun', '--app', appfile], [])
        self.assertEqual(cmd[:2], ['mpirun', '--app'])
        self.assertTrue(cmd[2].endswith('.tau'))
        with open(cmd[2], encoding='utf-8') as fin:
            self.assertIn('tau_exec -T', fin.read())

    def test_unmanaged_makefile_without_uid_warns(self):
        """A hand-built TAU whose makefile lacks our UID is used, with a warning."""
        tau = _tau(mpi_support=True)
        tau.unmanaged = True
        with self.assertLogs(tau_installation.LOGGER, level='WARNING') as logs:
            cmd = self._launch(tau, self._LAUNCHER, [['./a.out']], makefile=_makefile('mpi'))
        self.assertIn('runtime compatibility', logs.output[0])
        self.assertEqual(cmd[3:5], ['tau_exec', '-T'])

    def test_managed_makefile_without_uid_is_silent(self):
        """The compatibility warning is reserved for unmanaged installations."""
        tau = _tau(mpi_support=True)
        with mock.patch.object(tau_installation.LOGGER, 'warning') as warn:
            cmd = self._launch(tau, self._LAUNCHER, [['./a.out']], makefile=_makefile('mpi'))
        warn.assert_not_called()
        self.assertEqual(cmd[3:5], ['tau_exec', '-T'])

    def test_python_uses_tau_python(self):
        """Python applications run under tau_python with the target interpreter and the python tag stripped."""
        tau = _tau()
        makefile = _makefile(tau.uid, 'python')
        tau.uses_python = True
        tau.compilers = {PY: SimpleNamespace(absolute_path='/opt/py/bin/python3')}
        cmd = self._launch(tau, [], [['script.py', '--flag']], makefile=makefile)
        self.assertEqual(cmd[:2], ['tau_python', '-T'])
        self.assertEqual(set(cmd[2].split(',')), {tau.uid, 'serial'})
        self.assertEqual(cmd[3], '-tau-python-interpreter=/opt/py/bin/python3')
        self.assertEqual(cmd[4:], ['script.py', '--flag'])

    def test_instrumented_binary_runs_directly(self):
        """Source instrumentation, static linkage, or no measurement at all: tau_exec is not needed."""
        for kwargs in ({'source_inst': 'automatic'}, {'compiler_inst': 'always'}, {'application_linkage': 'static'},
                       {'profile': 'none', 'trace': 'none'}):
            with self.subTest(**kwargs):
                cmd = self._launch(_tau(mpi_support=True, **kwargs), self._LAUNCHER, [['./a.out']])
                self.assertEqual(cmd, ['mpirun', '-np', '4', './a.out'])


class DataFormatTest(tests.TestCase):
    """Tests for guessing performance data formats from file names."""

    def test_tau_profile(self):
        """A directory or a profile.<node>.<context>.<thread> file is TAU's native profile format."""
        self.assertEqual(TauInstallation.get_data_format(os.getcwd()), 'tau')
        # TAU numbers the node -1 when process-level parallelism was never initialized.
        for path in ('profile.0.0.0', 'profile.-1.0.0', os.path.join('trial', 'MULTI__TIME', 'profile.12.0.3')):
            with self.subTest(path=path):
                self.assertEqual(TauInstallation.get_data_format(path), 'tau')
        self.assertEqual(TauInstallation.get_data_format('profile.xml'), 'merged')

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
