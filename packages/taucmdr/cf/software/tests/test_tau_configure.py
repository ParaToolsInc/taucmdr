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

Functions used for unit tests of tau_installation.py against a configured TAU installation.
"""

import os
import multiprocessing
from types import SimpleNamespace
from unittest import mock
from taucmdr import tests
from taucmdr.error import InternalError
from taucmdr.cf.compiler.host import CC, CXX
from taucmdr.cf.compiler.python import PY
from taucmdr.cf.platforms import DARWIN, LINUX, X86_64, INTEL_KNL
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software import tau_installation
from taucmdr.cf.software.tau_installation import TauInstallation
from taucmdr.model.project import Project


class _FakeCompiler:
    """Just enough of InstalledCompiler for configure() to build its flag list."""
    # pylint: disable=too-few-public-methods

    def __init__(self, command, family, version=None):
        self.absolute_path = '/opt/compilers/bin/' + command
        self.version = version
        self.info = SimpleNamespace(command=command, family=SimpleNamespace(name=family))

    def unwrap(self):
        """Fake compilers never wrap anything."""
        return self


class ConfiguredTauTest(tests.TestCase):
    """Tests against the TauInstallation of the selected experiment.

    TAU is already installed by the time these run, so each test flips attributes on a fresh
    TauInstallation and inspects the configure flags, makefile tags, TAU_OPTIONS, or runtime
    environment that TAU Commander derives from them.  Nothing is built.
    """
    # pylint: disable=protected-access,too-many-public-methods

    _initialized = False

    def setUp(self):
        super().setUp()
        if not type(self)._initialized:
            self.reset_project_storage()
            type(self)._initialized = True

    @classmethod
    def tearDownClass(cls):
        cls._initialized = False
        super().tearDownClass()

    @staticmethod
    def _tau():
        return Project.selected().experiment().configure()

    def _configure_flags(self, tau):
        with mock.patch('taucmdr.util.create_subprocess', return_value=0) as run:
            tau.configure()
        run.assert_called_once()
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[0], './configure')
        return cmd[1:]

    def _useropts(self, flags):
        useropts = [flag for flag in flags if flag.startswith('-useropt=')]
        self.assertEqual(len(useropts), 1)
        return useropts[0][len('-useropt='):].split('#')

    # runtime_config

    def test_runtime_config_sqlite_plugin_suffix(self):
        """The SQLite plugin is a .so on Linux and a .dylib on Darwin, and disables regular profiles."""
        tau = self._tau()
        tau.profile = 'sqlite'
        tau.target_os = LINUX
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_PROFILE'], '0')
        self.assertEqual(env['TAU_PLUGINS'], 'libTAU-sqlite3-plugin.so')
        tau.target_os = DARWIN
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_PLUGINS'], 'libTAU-sqlite3-plugin.dylib')

    def test_runtime_config_profile_formats(self):
        """Each profile format sets exactly the TAU and Score-P variables it needs."""
        tau = self._tau()
        tau.profile = 'tau'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_PROFILE'], '1')
        self.assertNotIn('TAU_PROFILE_FORMAT', env)
        self.assertNotIn('TAU_PLUGINS', env)
        tau.profile = 'merged'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_PROFILE'], '1')
        self.assertEqual(env['TAU_PROFILE_FORMAT'], 'merged')
        tau.profile = 'cubex'
        _, env = tau.runtime_config()
        self.assertEqual(env['SCOREP_ENABLE_PROFILING'], '1')
        tau.profile = 'none'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_PROFILE'], '0')
        self.assertEqual(env['SCOREP_ENABLE_PROFILING'], 'false')

    def test_runtime_config_trace_formats(self):
        """Each trace format sets exactly the TAU and Score-P variables it needs."""
        tau = self._tau()
        tau.trace = 'slog2'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_TRACE'], '1')
        self.assertNotIn('TAU_TRACE_FORMAT', env)
        tau.trace = 'otf2'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_TRACE'], '1')
        self.assertEqual(env['TAU_TRACE_FORMAT'], 'otf2')
        tau.trace = 'none'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_TRACE'], '0')
        self.assertEqual(env['SCOREP_ENABLE_TRACING'], 'false')

    def test_runtime_config_openmp(self):
        """OMPT measurement adds -ompt and the OMPT environment; ignoring OpenMP adds neither."""
        tau = self._tau()
        tau.measure_openmp = 'ignore'
        tau.uses_ompt = False
        opts, env = tau.runtime_config()
        self.assertNotIn('-ompt', opts)
        self.assertNotIn('TAU_OMPT_SUPPORT_LEVEL', env)
        tau.measure_openmp = 'ompt'
        tau.uses_ompt = True
        opts, env = tau.runtime_config()
        self.assertIn('-ompt', opts)
        self.assertEqual(env['TAU_OMPT_SUPPORT_LEVEL'], 'full')
        self.assertEqual(env['TAU_OMPT_RESOLVE_ADDRESS_EAGERLY'], '1')

    def test_runtime_config_sampling(self):
        """Sampling enables -ebs and picks a per-architecture period unless one was given."""
        tau = self._tau()
        tau.sample = True
        tau.sample_resolution = 'line'
        tau.sampling_period = 0
        tau.target_arch = X86_64
        opts, env = tau.runtime_config()
        self.assertIn('-ebs', opts)
        self.assertEqual(env['TAU_SAMPLING'], '1')
        self.assertEqual(env['TAU_EBS_RESOLUTION'], 'line')
        self.assertEqual(env['TAU_EBS_PERIOD'], '10000')
        tau.target_arch = INTEL_KNL
        tau.sampling_period = 0
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_EBS_PERIOD'], '100000')
        tau.sampling_period = 5000
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_EBS_PERIOD'], '5000')
        tau.sample = False
        opts, env = tau.runtime_config()
        self.assertNotIn('-ebs', opts)
        self.assertEqual(env['TAU_SAMPLING'], '0')
        self.assertNotIn('TAU_EBS_PERIOD', env)

    def test_runtime_config_unwinding_and_select_file(self):
        """Unwind depth and selective instrumentation files are exported only when they apply."""
        tau = self._tau()
        tau.unwind_depth = 0
        tau.select_file = None
        _, env = tau.runtime_config()
        self.assertNotIn('TAU_EBS_UNWIND', env)
        self.assertNotIn('TAU_SELECT_FILE', env)
        tau.unwind_depth = 3
        tau.select_file = 'select.tau'
        tau.application_linkage = 'dynamic'
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_EBS_UNWIND'], '1')
        self.assertEqual(env['TAU_EBS_UNWIND_DEPTH'], '3')
        self.assertEqual(env['TAU_SELECT_FILE'], os.path.realpath(os.path.abspath('select.tau')))
        # Statically linked applications had the select file applied at link time.
        tau.application_linkage = 'static'
        _, env = tau.runtime_config()
        self.assertNotIn('TAU_SELECT_FILE', env)

    def test_runtime_config_throttle_and_callpath(self):
        """Throttle limits and callpath depth are exported only when enabled."""
        tau = self._tau()
        tau.throttle = True
        tau.throttle_per_call = 10
        tau.throttle_num_calls = 100000
        tau.callpath_depth = 2
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_THROTTLE'], '1')
        self.assertEqual(env['TAU_THROTTLE_PERCALL'], '10')
        self.assertEqual(env['TAU_THROTTLE_NUMCALLS'], '100000')
        self.assertEqual(env['TAU_CALLPATH'], '1')
        self.assertEqual(env['TAU_CALLPATH_DEPTH'], '2')
        tau.throttle = False
        tau.callpath_depth = 0
        _, env = tau.runtime_config()
        self.assertEqual(env['TAU_THROTTLE'], '0')
        self.assertNotIn('TAU_THROTTLE_PERCALL', env)
        self.assertNotIn('TAU_CALLPATH', env)

    def test_runtime_config_feature_options(self):
        """Every runtime feature maps to its tau_exec option."""
        tau = self._tau()
        tau.verbose = True
        tau.measure_cuda = True
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        tau.openacc_support = True
        tau.measure_level_zero = True
        tau.measure_opencl = True
        tau.measure_io = True
        tau.measure_memory_alloc = True
        tau.measure_shmem = True
        tau.ptts = True
        tau.ptts_post = True
        tau.ptts_sample_flags = '-x'
        tau.ptts_report_flags = '-y'
        opts, env = tau.runtime_config()
        for opt in ('-v', '-cupti', '-openacc', '-l0', '-opencl', '-io', '-memory', '-shmem',
                    '-ptts', '-ptts-post', '-ptts-sample-flags=-x', '-ptts-report-flags=-y'):
            self.assertIn(opt, opts)
        self.assertEqual(env['TAU_VERBOSE'], '1')
        self.assertEqual(env['TAU_SHOW_MEMORY_FUNCTIONS'], '1')

    def test_runtime_config_cuda_without_cupti(self):
        """CUDA measurement without CUPTI headers cannot ask tau_exec for -cupti."""
        tau = self._tau()
        tau.measure_cuda = True
        tau.cupti_prefix = None
        opts, _ = tau.runtime_config()
        self.assertNotIn('-cupti', opts)

    def test_runtime_config_defaults_are_minimal(self):
        """With no features enabled tau_exec gets no options and TAU sees only the wall clock."""
        tau = self._tau()
        tau.verbose = False
        tau.sample = False
        tau.metrics = ['TIME']
        opts, env = tau.runtime_config()
        self.assertEqual(opts, [])
        self.assertEqual(env['TAU_METRICS'], 'TIME,')
        self.assertEqual(env['TAU_VERBOSE'], '0')

    # compiletime_config

    def test_compiletime_config_baseline_returns_early(self):
        """Baseline builds get no TAU_OPTIONS or TAU_MAKEFILE at all."""
        tau = self._tau()
        tau.baseline = True
        opts, env = tau.compiletime_config(tau.compilers[CC])
        self.assertEqual(opts, [])
        self.assertNotIn('TAU_OPTIONS', env)
        self.assertNotIn('TAU_MAKEFILE', env)

    def test_compiletime_config_runtime_only_instrumentation(self):
        """No source or compiler instrumentation: link only, no compiler options, real makefile exported."""
        tau = self._tau()
        tau.source_inst = 'never'
        tau.compiler_inst = 'never'
        tau.sample = False
        opts, env = tau.compiletime_config(tau.compilers[CC])
        tau_opts = env['TAU_OPTIONS'].split()
        self.assertIn('-optLinkOnly', tau_opts)
        self.assertIn('-optNoCompInst', tau_opts)
        self.assertNotIn('-optRevert', tau_opts)
        self.assertFalse(any(opt.startswith('-optAppCC=') for opt in tau_opts))
        self.assertNotIn('-g', opts)
        self.assertNotIn('-DTAU_ENABLED=1', opts)
        self.assertEqual(env['TAU_MAKEFILE'], tau.get_makefile())

    def test_compiletime_config_full_instrumentation(self):
        """Source plus compiler instrumentation turns on every matching TAU compiler option."""
        tau = self._tau()
        tau.source_inst = 'automatic'
        tau.compiler_inst = 'always'
        tau.keep_inst_files = True
        tau.reuse_inst_files = True
        tau.select_file = 'select.tau'
        tau.measure_io = True
        tau.measure_memory_alloc = True
        tau.openmp_support = True
        tau.verbose = True
        compiler = tau.compilers[CC]
        opts, env = tau.compiletime_config(compiler)
        tau_opts = env['TAU_OPTIONS'].split()
        for opt in ('-optRevert', '-optVerbose', '-optCompInst', '-optKeepFiles', '-optReuseFiles',
                    '-optTrackIO', '-optMemDbg', '-optContinueBeforeOMP',
                    '-optAppCC=' + compiler.absolute_path,
                    '-optAppCXX=' + compiler.absolute_path,
                    '-optAppF90=' + compiler.absolute_path,
                    '-optTauSelectFile=' + os.path.realpath(os.path.abspath('select.tau'))):
            self.assertIn(opt, tau_opts)
        self.assertNotIn('-optLinkOnly', tau_opts)
        self.assertNotIn('-optNoCompInst', tau_opts)
        self.assertIn('-g', opts)
        self.assertIn('-DTAU_ENABLED=1', opts)

    def test_compiletime_config_fallback_instrumentation(self):
        """Fallback compiler instrumentation reverts to the plain compiler when TAU's wrapper fails."""
        tau = self._tau()
        tau.source_inst = 'never'
        tau.compiler_inst = 'fallback'
        opts, env = tau.compiletime_config(tau.compilers[CC])
        tau_opts = env['TAU_OPTIONS'].split()
        self.assertIn('-optRevert', tau_opts)
        self.assertNotIn('-optCompInst', tau_opts)
        self.assertNotIn('-optNoCompInst', tau_opts)
        self.assertIn('-g', opts)

    def test_compiletime_config_manual_source_instrumentation(self):
        """Manual source instrumentation links only but still defines TAU_ENABLED for the user's macros."""
        tau = self._tau()
        tau.source_inst = 'manual'
        tau.compiler_inst = 'never'
        compiler = tau.compilers[CC]
        opts, env = tau.compiletime_config(compiler)
        tau_opts = env['TAU_OPTIONS'].split()
        self.assertIn('-optLinkOnly', tau_opts)
        self.assertIn('-optNoCompInst', tau_opts)
        self.assertIn('-optAppCC=' + compiler.absolute_path, tau_opts)
        self.assertIn('-DTAU_ENABLED=1', opts)

    def test_compiletime_config_forced_options_replace_defaults(self):
        """Forced TAU options are used verbatim instead of the derived set."""
        tau = self._tau()
        tau.force_tau_options = ['-optForced']
        _, env = tau.compiletime_config(tau.compilers[CC])
        self.assertEqual(env['TAU_OPTIONS'], '-optForced')

    def test_compiletime_config_extra_options_are_added(self):
        """Extra TAU options are merged with the derived set."""
        tau = self._tau()
        tau.extra_tau_options = ['-optExtra']
        tau.source_inst = 'never'
        tau.compiler_inst = 'never'
        _, env = tau.compiletime_config(tau.compilers[CC])
        tau_opts = env['TAU_OPTIONS'].split()
        self.assertIn('-optExtra', tau_opts)
        self.assertIn('-optLinkOnly', tau_opts)

    def test_compiletime_config_warns_on_foreign_makefile(self):
        """A makefile that does not carry our UID is used, with a warning."""
        tau = self._tau()
        tau._tau_makefile = '/opt/tau/x86_64/lib/Makefile.tau-foreign-mpi'
        with self.assertLogs(tau_installation.LOGGER, level='WARNING') as logs:
            _, env = tau.compiletime_config(tau.compilers[CC])
        self.assertIn('compiler compatibility', logs.output[0])
        self.assertEqual(env['TAU_MAKEFILE'], tau._tau_makefile)

    # get_tags / _incompatible_tags

    def test_tags_ompt(self):
        """OMPT measurement is tagged openmp+ompt; the old TR4/TR6/v5 tags are gone."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'ompt'
        tags = tau.get_tags()
        self.assertIn(tau.uid, tags)
        self.assertTrue({'openmp', 'ompt'} <= tags)
        self.assertFalse({'tr4', 'tr6', 'v5', 'opari', 'pthread'} & tags)

    def test_tags_opari(self):
        """OPARI measurement is tagged openmp+opari."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'opari'
        tags = tau.get_tags()
        self.assertTrue({'openmp', 'opari'} <= tags)
        self.assertNotIn('ompt', tags)

    def test_tags_openmp_ignored_uses_pthread(self):
        """An OpenMP application whose directives are not measured only needs thread support."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'ignore'
        tags = tau.get_tags()
        self.assertIn('pthread', tags)
        self.assertNotIn('openmp', tags)

    def test_tags_pthreads_take_precedence(self):
        """Explicit pthread support wins over OpenMP tagging."""
        tau = self._tau()
        tau.pthreads_support = True
        tau.openmp_support = True
        tau.measure_openmp = 'ompt'
        tags = tau.get_tags()
        self.assertIn('pthread', tags)
        self.assertFalse({'openmp', 'ompt'} & tags)

    def test_tags_invalid_openmp_measurement(self):
        """An unknown OpenMP measurement method is an internal error."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'bogus'
        with self.assertRaises(InternalError):
            tau.get_tags()

    def test_tags_features(self):
        """Every application feature and user tag appears in the tag set."""
        tau = self._tau()
        tau.tbb_support = True
        tau.mpi_support = True
        tau.openacc_support = True
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        tau.shmem_support = True
        tau.mpc_support = True
        tau.uses_python = True
        tau.mpit = True
        tau.measure_level_zero = True
        tau.tags = ['custom']
        tags = tau.get_tags()
        self.assertTrue({'tbb', 'mpi', 'acc', 'cupti', 'shmem', 'mpc', 'python', 'mpit',
                         'level_zero', 'custom'} <= tags)

    def test_tags_dependencies(self):
        """PDT, PAPI, and Score-P are tagged only when the configuration uses them."""
        tau = self._tau()
        tau.uses_pdt = True
        tau.uses_papi = True
        tau.uses_scorep = True
        self.assertTrue({'pdt', 'papi', 'scorep'} <= tau.get_tags())
        tau.uses_pdt = False
        tau.uses_papi = False
        tau.uses_scorep = False
        self.assertFalse({'pdt', 'papi', 'scorep'} & tau.get_tags())

    def test_incompatible_tags_without_features(self):
        """Makefiles for features the configuration lacks must never be approximated."""
        tau = self._tau()
        tau.mpi_support = False
        tau.measure_openmp = 'ignore'
        tau.uses_scorep = False
        tau.shmem_support = False
        tags = tau._incompatible_tags()
        self.assertTrue({'mpi', 'openmp', 'opari', 'ompt', 'gomp', 'scorep', 'shmem'} <= tags)
        self.assertNotIn('tr6', tags)

    def test_incompatible_tags_with_features(self):
        """Features the configuration uses are never incompatible."""
        tau = self._tau()
        tau.mpi_support = True
        tau.measure_openmp = 'ompt'
        tau.uses_scorep = True
        tau.shmem_support = True
        self.assertFalse({'mpi', 'openmp', 'opari', 'ompt', 'scorep', 'shmem'} & tau._incompatible_tags())

    # configure

    def test_configure_default_flags(self):
        """A serial, single-threaded configuration passes tag, arch, compilers, and TAU's limits."""
        tau = self._tau()
        tau.openmp_support = False
        tau.pthreads_support = False
        tau.mpi_support = False
        tau.max_threads = None
        flags = self._configure_flags(tau)
        self.assertIn(f'-tag={tau.uid}', flags)
        self.assertIn(f'-arch={tau.tau_magic.name}', flags)
        self.assertTrue(any(flag.startswith('-cc=') for flag in flags))
        self.assertTrue(any(flag.startswith('-c++=') for flag in flags))
        self.assertIn(f'-unwinder={tau.unwinder}', flags)
        for flag in ('-openmp', '-pthread', '-opari', '-ompt-tr4', '-ompt-tr6', '-ompt-v5', '-python', '-mpi'):
            self.assertNotIn(flag, flags)
        useropts = self._useropts(flags)
        self.assertIn('-DTAU_MAX_THREADS=25', useropts)
        self.assertIn(f'-DTAU_MAX_METRICS={len(tau.metrics)}', useropts)
        self.assertFalse(any(opt.startswith('-I') for opt in useropts))

    def test_configure_ompt_flags(self):
        """OMPT points TAU at the OMPT runtime and adds its include path so omp-tools.h resolves."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'ompt'
        tau.max_threads = None
        tau.dependencies['ompt'] = SimpleNamespace(install_prefix='/fake/ompt', include_path='/fake/ompt/include')
        flags = self._configure_flags(tau)
        self.assertIn('-openmp', flags)
        self.assertIn('-ompt=/fake/ompt', flags)
        self.assertNotIn('-ompt-v5', flags)
        self.assertNotIn('-pthread', flags)
        self.assertFalse(any(flag.startswith('-ompt-tr') for flag in flags))
        useropts = self._useropts(flags)
        self.assertIn('-I/fake/ompt/include', useropts)
        self.assertIn(f'-DTAU_MAX_THREADS={max(64, 2 * multiprocessing.cpu_count())}', useropts)

    def test_configure_ompt_v5_for_intel_19(self):
        """Intel 19 and later ship their own OMPT runtime, so TAU is configured with -ompt-v5 instead."""
        tau = self._tau()
        uid = tau.uid
        tau.compilers = {CC: _FakeCompiler('icc', 'Intel', version=(19, 1, 0)),
                         CXX: _FakeCompiler('icpc', 'Intel', version=(19, 1, 0))}
        tau.openmp_support = True
        tau.measure_openmp = 'ompt'
        tau.dependencies = {'ompt': SimpleNamespace(install_prefix='/fake/ompt', include_path='/fake/ompt/include')}
        flags = self._configure_flags(tau)
        self.assertIn(f'-tag={uid}', flags)
        self.assertIn('-cc=icc', flags)
        self.assertIn('-c++=icpc', flags)
        self.assertIn('-ompt-v5', flags)
        self.assertNotIn('-ompt=/fake/ompt', flags)
        self.assertFalse(any(flag.startswith('-fortran=') for flag in flags))
        self.assertIn('-I/fake/ompt/include', self._useropts(flags))

    def test_configure_ompt_prefix_for_older_intel(self):
        """Intel before 19, or an unknown version, still needs the downloaded OMPT runtime."""
        for version in ((18, 0, 3), None):
            tau = self._tau()
            tau.compilers = {CC: _FakeCompiler('icc', 'Intel', version=version),
                             CXX: _FakeCompiler('icpc', 'Intel', version=version)}
            tau.openmp_support = True
            tau.measure_openmp = 'ompt'
            tau.dependencies = {'ompt': SimpleNamespace(install_prefix='/fake/ompt', include_path='/fake/ompt/include')}
            flags = self._configure_flags(tau)
            self.assertIn('-ompt=/fake/ompt', flags)
            self.assertNotIn('-ompt-v5', flags)

    def test_configure_ompt_without_dependency(self):
        """OMPT without a managed OMPT runtime enables OpenMP but passes no OMPT flags."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'ompt'
        tau.dependencies.pop('ompt', None)
        flags = self._configure_flags(tau)
        self.assertIn('-openmp', flags)
        self.assertFalse(any(flag.startswith('-ompt') for flag in flags))
        self.assertFalse(any(opt.startswith('-I') for opt in self._useropts(flags)))

    def test_configure_opari_flags(self):
        """OPARI measurement configures TAU with -openmp -opari."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'opari'
        flags = self._configure_flags(tau)
        self.assertIn('-openmp', flags)
        self.assertIn('-opari', flags)
        self.assertFalse(any(flag.startswith('-ompt') for flag in flags))

    def test_configure_threading_flags(self):
        """Ignored OpenMP and explicit pthreads both configure TAU with -pthread only."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'ignore'
        flags = self._configure_flags(tau)
        self.assertIn('-pthread', flags)
        self.assertNotIn('-openmp', flags)
        tau = self._tau()
        tau.pthreads_support = True
        tau.openmp_support = False
        flags = self._configure_flags(tau)
        self.assertIn('-pthread', flags)
        self.assertNotIn('-openmp', flags)

    def test_configure_invalid_openmp_measurement(self):
        """An unknown OpenMP measurement method is caught before configure runs."""
        tau = self._tau()
        tau.openmp_support = True
        tau.measure_openmp = 'bogus'
        with mock.patch('taucmdr.util.create_subprocess', return_value=0) as run:
            with self.assertRaises(InternalError):
                tau.configure()
        run.assert_not_called()

    def test_configure_feature_flags(self):
        """Each measurement or application feature maps to its configure flag."""
        tau = self._tau()
        tau.measure_io = True
        tau.dyninst = True
        tau.mpit = True
        tau.measure_level_zero = True
        tau.dependencies.pop('level_zero', None)
        tau.tbb_support = True
        tau.openacc_support = True
        tau.uses_cuda = True
        tau.cuda_prefix = '/opt/cuda'
        tau.cupti_prefix = '/opt/cuda/extras/CUPTI'
        tau.opencl_prefix = '/opt/opencl'
        flags = self._configure_flags(tau)
        for flag in ('-iowrapper', '-dyninst=download', '-mpit', '-level_zero', '-tbb', '-openacc',
                     '-cuda=/opt/cuda', '-cupti=/opt/cuda/extras/CUPTI', '-opencl=/opt/opencl'):
            self.assertIn(flag, flags)

    def test_configure_level_zero_dependency_prefix(self):
        """A managed Level Zero runtime is passed by prefix instead of the bare -level_zero flag."""
        tau = self._tau()
        tau.measure_level_zero = True
        tau.dependencies['level_zero'] = SimpleNamespace(install_prefix='/fake/level_zero')
        flags = self._configure_flags(tau)
        self.assertIn('-level_zero=/fake/level_zero', flags)
        self.assertNotIn('-level_zero', flags)

    def _configure_python(self, target_os, library_name):
        tau = self._tau()
        tau.target_os = target_os
        tau.compilers = {CC: _FakeCompiler('gcc', 'GNU'),
                         CXX: _FakeCompiler('g++', 'GNU'),
                         PY: _FakeCompiler('python3', 'Python')}
        tau.uses_python = True

        def python_output(cmd):
            return '/py/lib/python3.12' if 'stdlib' in cmd[-1] else '/py/include/python3.12'

        with mock.patch.object(tau_installation, 'get_command_output', side_effect=python_output), \
                mock.patch.object(TauInstallation, '_find_python_library',
                                  return_value=('/py/lib', library_name)) as find:
            flags = self._configure_flags(tau)
        return flags, find

    def test_configure_python_flags(self):
        """Python support passes the interpreter's include, lib directory, and unversioned library name."""
        flags, find = self._configure_python(LINUX, 'libpython3.12.so')
        find.assert_called_once_with('/py/lib/python3.12', 'so')
        self.assertIn('-python', flags)
        self.assertIn('-pythoninc=/py/include/python3.12', flags)
        self.assertIn('-pythonlib=/py/lib', flags)
        self.assertIn('-pythonlibrary=libpython3.12.so', flags)

    def test_configure_python_without_unversioned_library(self):
        """Only a versioned libpython (e.g. .so.1.0) available: leave -pythonlibrary to TAU's default."""
        flags, _ = self._configure_python(LINUX, None)
        self.assertIn('-pythonlib=/py/lib', flags)
        self.assertFalse(any(flag.startswith('-pythonlibrary=') for flag in flags))

    def test_configure_python_darwin_looks_for_dylib(self):
        """Darwin targets search for libpython*.dylib."""
        flags, find = self._configure_python(DARWIN, 'libpython3.12.dylib')
        find.assert_called_once_with('/py/lib/python3.12', 'dylib')
        self.assertIn('-pythonlibrary=libpython3.12.dylib', flags)

    def test_configure_minimal(self):
        """The minimal (baseline) configuration only names the tag, arch, and unwinder."""
        tau = self._tau()
        tau.minimal = True
        flags = self._configure_flags(tau)
        self.assertIn(f'-tag={tau.uid}', flags)
        self.assertIn(f'-arch={tau.tau_magic.name}', flags)
        self.assertIn(f'-unwinder={tau.unwinder}', flags)
        self.assertFalse(any(flag.startswith('-cc=') for flag in flags))
        self.assertFalse(any(flag.startswith('-useropt=') for flag in flags))

    def test_configure_failure_raises(self):
        """A nonzero exit from TAU's configure script is a package error for full and minimal builds."""
        tau = self._tau()
        with mock.patch('taucmdr.util.create_subprocess', return_value=1):
            with self.assertRaises(SoftwarePackageError):
                tau.configure()
            tau.minimal = True
            with self.assertRaises(SoftwarePackageError):
                tau.configure()

    # limits and makefiles

    def test_max_threads(self):
        """TAU_MAX_THREADS follows the application's explicit limit, then the arch, then TAU's default."""
        tau = self._tau()
        tau.max_threads = None
        tau.pthreads_support = tau.openmp_support = tau.tbb_support = tau.mpc_support = False
        self.assertEqual(tau._get_max_threads(), 25)
        tau.max_threads = 128
        self.assertEqual(tau._get_max_threads(), 128)
        tau.max_threads = None
        tau.tbb_support = True
        tau.target_arch = X86_64
        self.assertEqual(tau._get_max_threads(), max(64, 2 * multiprocessing.cpu_count()))
        tau.target_arch = INTEL_KNL
        self.assertEqual(tau._get_max_threads(), 72)

    def test_get_makefile_forced(self):
        """A forced makefile is returned as-is and cached."""
        tau = self._tau()
        tau._tau_makefile = None
        tau.forced_makefile = '/opt/tau/x86_64/lib/Makefile.tau-forced'
        self.assertEqual(tau.get_makefile(), tau.forced_makefile)
        self.assertEqual(tau._tau_makefile, tau.forced_makefile)

    def test_get_makefile_matches_installed_configuration(self):
        """The installed makefile is found again from the configuration tags alone."""
        tau = self._tau()
        expected = tau.get_makefile()
        tau._tau_makefile = None
        makefile = tau.get_makefile()
        self.assertEqual(makefile, expected)
        self.assertIn(tau.uid, tau._makefile_tags(makefile))

    def test_get_makefile_unknown_tags_raise(self):
        """No installed makefile carries an unknown tag, managed or not."""
        tau = self._tau()
        tau._tau_makefile = None
        tau.tags = ['no-such-tag']
        with self.assertRaises(SoftwarePackageError):
            tau.get_makefile()
        tau.unmanaged = True
        with self.assertRaises(SoftwarePackageError):
            tau.get_makefile()
