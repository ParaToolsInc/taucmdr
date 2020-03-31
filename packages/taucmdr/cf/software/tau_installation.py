# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
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
"""TAU software installation management.

TAU is the core software package of TAU Commander.
"""
# Settle down pylint.  This is a big, ugly file and there's not much we can do about it.
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=too-many-lines
# pylint: disable=too-many-branches

import os
import re
import sys
import ast
import glob
import shutil
import datetime
import shlex
import resource
import tempfile
import multiprocessing
from subprocess import CalledProcessError
from taucmdr import logger, util
from taucmdr.util import get_command_output
from taucmdr.error import ConfigurationError, InternalError
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software.installation import Installation, parallel_make_flags, new_os_environ
from taucmdr.cf.compiler import host as host_compilers, InstalledCompilerSet
from taucmdr.cf.compiler.host import CC, CXX, FC, UPC, GNU, APPLE_LLVM, IBM
from taucmdr.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
from taucmdr.cf.compiler.shmem import SHMEM_CC, SHMEM_CXX, SHMEM_FC
from taucmdr.cf.compiler.cuda import CUDA_CXX, CUDA_FC
from taucmdr.cf.compiler.caf import CAF_FC
from taucmdr.cf.compiler.python import PY
from taucmdr.cf.platforms import TauMagic, DARWIN, CRAY_CNL, IBM_BGL, IBM_BGP, IBM_BGQ, HOST_ARCH, HOST_OS
from taucmdr.cf.platforms import INTEL_KNL, INTEL_KNC


LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://tau.uoregon.edu/tau.tgz'}

NIGHTLY = 'http://fs.paratools.com/tau-nightly.tgz'

DATA_TOOLS = ['jumpshot',
              'paraprof',
              'perfdmf_configure',
              'perfdmf_createapp',
              'perfdmf_createexp',
              'perfdmfdb.py',
              'perfdmf_loadtrial',
              'perfexplorer',
              'perfexplorer_configure',
              'pprof',
              'slog2print',
              'tau2slog2',
              'taudb_configure',
              'taudb_install_cert',
              'taudb_keygen',
              'taudb_loadtrial',
              'tau_ebs2otf.pl',
              'tau_ebs_process.pl',
              'tau_merge',
              'tau_multimerge',
              'tau_treemerge.pl',
              'tau_treemerge.pl']

COMMANDS = {None:
            DATA_TOOLS +
            ['phaseconvert',
             'ppscript',
             'tau_analyze',
             'taucc',
             'tau_cc.sh',
             'tau_compiler.sh',
             'tau-config',
             'tau_convert',
             'taucxx',
             'tau_cxx.sh',
             'tauex',
             'tau_exec',
             'tau_f77.sh',
             'tauf90',
             'tau_f90.sh',
             'tau_gen_wrapper',
             'tau_header_replace.pl',
             'tauinc.pl',
             'tau_java',
             'tau_javamax.sh',
             'tau_macro.sh',
             'tau_pebil_rewrite',
             'tau_reduce',
             'tau_rewrite',
             'tau_selectfile',
             'tau_show_libs',
             'tau_throttle.sh',
             'tauupc',
             'tau_upc.sh',
             'tau_python',
             'tau_user_setup.sh']}

HEADERS = {None: ['Profile/Profiler.h', 'Profile/TAU.h']}

TAU_COMPILER_WRAPPERS = {CC: 'tau_cc.sh',
                         CXX: 'tau_cxx.sh',
                         FC: 'tau_f90.sh',
                         UPC: 'tau_upc.sh',
                         MPI_CC: 'tau_cc.sh',
                         MPI_CXX: 'tau_cxx.sh',
                         MPI_FC: 'tau_f90.sh',
                         SHMEM_CC: 'tau_cc.sh',
                         SHMEM_CXX: 'tau_cxx.sh',
                         SHMEM_FC: 'tau_f90.sh',
                         CUDA_CXX: 'tau_cxx.sh',
                         CUDA_FC: 'tau_ftn.sh',
                         CAF_FC: 'tau_caf.sh'}

TAU_MINIMAL_COMPILERS = [CC, CXX]

PROFILE_ANALYSIS_TOOLS = 'paraprof', 'pprof'

TRACE_ANALYSIS_TOOLS = 'jumpshot', 'vampir'

PROGRAM_LAUNCHERS = {'mpirun': ['-app', '--app', '-configfile'],
                     'mpiexec': ['-app', '--app', '-configfile'],
                     'mpiexec.hydra': ['-app', '--app', '-configfile'],
                     'mpiexec.mpd': ['-app', '--app', '-configfile'],
                     'orterun': ['-app', '--app', '-configfile'],
                     'mpiexec_mpt': [],
                     'ccc_mprun': [],
                     'mpirun_rsh': [],
                     'ibrun': [],
                     'aprun': [],
                     'qsub': [],
                     'srun': ['--multi-prog'],
                     'oshrun': [],
                     'cafrun': []}


class TauInstallation(Installation):
    """Encapsulates a TAU installation.

    TAU is an enormous, organic, complex piece of software so this class is
    unusually complex to consider all the corner cases.  This is where most
    of the systemization of TAU is actually implemented so it can get ugly.
    """

    def __init__(self, sources, target_arch, target_os, compilers,
                 # Minimal configuration support
                 minimal=False,
                 # TAU feature suppport
                 application_linkage='dynamic',
                 openmp_support=False,
                 pthreads_support=False,
                 tbb_support=False,
                 mpi_support=False,
                 mpi_libraries=None,
                 caf_support=False,
                 cuda_support=False,
                 cuda_prefix=None,
                 opencl_support=False,
                 opencl_prefix=None,
                 shmem_support=False,
                 shmem_libraries=None,
                 mpc_support=False,
                 max_threads=None,
                 python_support=False,
                 # Instrumentation methods and options
                 source_inst="never",
                 compiler_inst="never",
                 keep_inst_files=False,
                 reuse_inst_files=False,
                 select_file=None,
                 # Measurement methods and options
                 baseline=False,
                 profile="tau",
                 trace="none",
                 sample=False,
                 metrics=None,
                 measure_io=False,
                 measure_mpi=False,
                 measure_openmp="ignore",
                 measure_opencl=False,
                 measure_cuda=False,
                 measure_shmem=False,
                 measure_heap_usage=False,
                 measure_system_load=False,
                 measure_memory_alloc=False,
                 measure_comm_matrix=False,
                 measure_callsite=False,
                 callpath_depth=100,
                 throttle=True,
                 metadata_merge=True,
                 throttle_per_call=10,
                 throttle_num_calls=100000,
                 sampling_period=0,
                 track_memory_footprint=False,
                 update_nightly=False,
                 ptts=False,
                 ptts_post=False,
                 ptts_sample_flags=None,
                 ptts_restart=False,
                 ptts_start=None,
                 ptts_stop=None,
                 ptts_report_flags=None,
                 tags=None,
                 forced_makefile=None,
                 dyninst=False,
                 mpit=False,
                 unwind_depth=0):
        """Initialize the TAU installation wrapper class.

        Args:
            sources (dict): Packages sources as strings indexed by package names as strings.  A source may be a
                            path to a directory where the software has already been installed, or a path to a source
                            archive file, or the special keywords 'download' or 'nightly'.
            target_arch (Architecture): Target architecture description.
            target_os (OperatingSystem): Target operating system description.
            compilers (InstalledCompilerSet): Compilers to use if software must be compiled.
            minimal (bool): If True then ignore all other arguments and configure with minimal features.
            application_linkage (str): Either "static" or "dynamic".
            openmp_support (bool): Enable or disable OpenMP support in TAU.
            pthreads_support (bool): Enable or disable pthreads support in TAU.
            tbb_support (bool): Enable or disable tbb support in TAU.
            mpi_support (bool): Enable or disable MPI support in TAU.
            mpi_libraries (list): MPI libraries to include when linking with TAU.
            cuda_support (bool): Enable or disable CUDA support in TAU.
            cuda_prefix (str): Path to CUDA toolkit installation.
            opencl_support (bool): Enable or disable OpenCL support in TAU.
            shmem_support (bool): Enable or disable SHMEM support in TAU.
            shmem_libraries (list): SHMEM libraries to include when linking with TAU.
            mpc_support (bool): Enable or disable MPC support in TAU.
            max_threads (int): Maximum number of threads in TAU.
            source_inst (str): Policy for source-based instrumentation, one of "automatic", "manual", or "never".
            compiler_inst (str): Policy for compiler-based instrumentation, one of "always", "fallback", or "never".
            keep_inst_files (bool): If True then do not remove instrumented source files after compilation.
            reuse_inst_files (bool): If True then reuse instrumented source files for compilation when available.
            select_file (str): Path to selective instrumentation file.
            baseline (bool): If True, only measure wallclock time via `tau_baseline`.
            profile (str): Format for profile files, one of "tau", "merged", "cubex", or "none".
            trace (str): Format for trace files, one of "slog2", "otf2", or "none".
            sample (bool): Enable or disable event-based sampling.
            metrics (list): Metrics to measure, e.g. ['TIME', 'PAPI_FP_INS']
            measure_io (bool): If True then measure time spent in POSIX I/O calls.
            measure_mpi (bool): If True then measure time spent in MPI calls.
            measure_openmp (str): String specifying OpenMP measurement method, one of "ignore", "ompt", or "opari".
            measure_cuda (bool): If True then measure time spent in CUDA calls.
            measure_shmem (bool): If True then measure time spent in SHMEM calls.
            measure_heap_usage (bool): If True then measure memory usage.
            measure_system_load (bool): If True then measure the system load.
            measure_memory_alloc (bool): If True then record memory allocation and deallocation events.
            measure_comm_matrix (bool): If True then record the point-to-point communication matrix.
            measure_callsite (bool): If True then record event callsites.
            callpath_depth (int): Depth of callpath measurement.  0 to disable.
            throttle (bool): If True then throttle lightweight events.
            metadata_merge (bool): If True then merge metadata.
            update_nightly (bool): If True then download latest TAU nightly.
            ptts (bool): If True then enable PTTS support.
            ptts_post (bool): If True then skip application sampling and post-process existing PTTS sample files
            ptts_sample_flags (str): flags to pass to PTTS sample_ts command
            ptts_restart (bool): If true then enable restart suport within PTTS, allowing application to continue running and be reinstrumented after stop
            ptts_start (str): address at which to start a PTTS sampling region
            ptts_stop (str): address at which to stop a PTTS sampling region
            ptts_report_flags (str): flags to pass to PTTS report_ts command
            throttle_per_call (int): Maximum microseconds per call of a lightweight event.
            throttle_num_calls (int): Minimum number of calls for a lightweight event.
            sampling_period (int): Sampling period in microseconds; set to 0 to use architecture specific defaults.
            track_memory_footprint (bool): If True then track memory footprint.
            mpit (bool): If True then enable MPI-T profiling interface.
            forced_makefile (str): Path to external makefile if forcing TAU_MAKEFILE or None.
        """
        assert minimal in (True, False)
        assert application_linkage in ('static', 'dynamic')
        assert openmp_support in (True, False)
        assert pthreads_support in (True, False)
        assert tbb_support in (True, False)
        assert mpi_support in (True, False)
        assert isinstance(mpi_libraries, list) or mpi_libraries is None
        assert cuda_support in (True, False)
        assert isinstance(cuda_prefix, basestring) or cuda_prefix is None
        assert opencl_support in (True, False)
        assert isinstance(opencl_prefix, basestring) or opencl_prefix is None
        assert shmem_support in (True, False)
        assert isinstance(shmem_libraries, list) or shmem_libraries is None
        assert mpc_support in (True, False)
        assert isinstance(max_threads, int) or max_threads is None
        assert source_inst in ("automatic", "manual", "never")
        assert compiler_inst in ("always", "fallback", "never")
        assert keep_inst_files in (True, False)
        assert reuse_inst_files in (True, False)
        assert isinstance(select_file, basestring) or select_file is None
        assert baseline in (True, False)
        assert profile in ("tau", "merged", "cubex", "none")
        assert trace in ("slog2", "otf2", "none")
        assert sample in (True, False)
        assert isinstance(metrics, list) or metrics is None
        assert measure_io in (True, False)
        assert measure_mpi in (True, False)
        assert measure_openmp in ("ignore", "ompt", "opari")
        assert measure_opencl in (True, False)
        assert measure_cuda in (True, False)
        assert measure_shmem in (True, False)
        assert measure_heap_usage in (True, False)
        assert measure_system_load in (True, False)
        assert measure_memory_alloc in (True, False)
        assert measure_comm_matrix in (True, False)
        assert measure_callsite in (True, False)
        assert python_support in (True, False)
        assert isinstance(callpath_depth, int)
        assert throttle in (True, False)
        assert metadata_merge in (True, False)
        assert update_nightly in (True, False)
        assert ptts in (True, False)
        assert ptts_post in (True, False)
        assert ptts_restart in (True, False)
        assert isinstance(throttle_per_call, int)
        assert isinstance(throttle_num_calls, int)
        assert isinstance(sampling_period, int)
        assert track_memory_footprint in (True, False)
        assert isinstance(forced_makefile, basestring) or forced_makefile is None
        super(TauInstallation, self).__init__('tau', 'TAU Performance System',
                                              sources, target_arch, target_os, compilers,
                                              REPOS, COMMANDS, None, None)
        self._tau_makefile = None
        self._install_tag = None
        self._all_sources = sources
        if self.src == 'nightly':
            self.src = NIGHTLY
        self.tau_magic = TauMagic.find((self.target_arch, self.target_os))
        # TAU puts installation files (bin, lib, etc.) in a magically named subfolder
        self._bin_subdir = os.path.join(self.tau_magic.name, 'bin')
        self._lib_subdir = os.path.join(self.tau_magic.name, 'lib')
        self.verbose = (logger.LOG_LEVEL == 'DEBUG')
        self.minimal = minimal
        self.application_linkage = application_linkage
        self.openmp_support = openmp_support
        self.opencl_support = opencl_support
        self.opencl_prefix = opencl_prefix
        self.pthreads_support = pthreads_support
        self.tbb_support = tbb_support
        self.mpi_support = mpi_support
        self.mpi_libraries = mpi_libraries if mpi_libraries is not None else []
        self.caf_support = caf_support
        self.cuda_support = cuda_support
        self.cuda_prefix = cuda_prefix
        self.shmem_support = shmem_support
        self.shmem_libraries = shmem_libraries if shmem_libraries is not None else []
        self.mpc_support = mpc_support
        self.max_threads = max_threads
        self.python_support = python_support
        self.source_inst = source_inst
        self.compiler_inst = compiler_inst
        self.keep_inst_files = keep_inst_files
        self.reuse_inst_files = reuse_inst_files
        self.select_file = select_file
        self.baseline = baseline
        self.profile = profile
        self.trace = trace
        self.sample = sample
        self.metrics = ['TIME'] if metrics is None else metrics
        self.measure_io = measure_io
        self.measure_mpi = measure_mpi
        self.measure_openmp = measure_openmp
        self.measure_opencl = measure_opencl
        self.measure_cuda = measure_cuda
        self.measure_shmem = measure_shmem
        self.measure_heap_usage = measure_heap_usage
        self.measure_system_load = measure_system_load
        self.measure_memory_alloc = measure_memory_alloc
        self.measure_comm_matrix = measure_comm_matrix
        self.measure_callsite = measure_callsite
        self.callpath_depth = callpath_depth
        self.throttle = throttle
        self.metadata_merge = metadata_merge
        self.update_nightly = update_nightly
        self.ptts = ptts
        self.ptts_post = ptts_post
        self.ptts_sample_flags = ptts_sample_flags
        self.ptts_restart = ptts_restart
        self.ptts_start = ptts_start
        self.mpit = mpit
        self.ptts_stop = ptts_stop
        self.ptts_report_flags = ptts_report_flags
        self.throttle_per_call = throttle_per_call
        self.throttle_num_calls = throttle_num_calls
        self.sampling_period = sampling_period
        self.track_memory_footprint = track_memory_footprint
        self.python_path = util.which('python')
        self.tags = tags
        self.forced_makefile = forced_makefile
        self.dyninst = dyninst
        self.unwind_depth = unwind_depth
        self.uses_python = False
        self.uses_pdt = not minimal and (self.source_inst == 'automatic' or self.shmem_support)
        self.uses_binutils = not minimal and (self.target_os is not DARWIN)
        self.uses_libunwind = not minimal and (self.target_os is not DARWIN)
        self.uses_papi = not minimal and bool(len([met for met in self.metrics if 'PAPI' in met]))
        self.uses_scorep = not minimal and (self.profile == 'cubex')
        self.uses_ompt = not minimal and (self.measure_openmp == 'ompt')
        self.uses_ompt_tr6 = self.uses_ompt and sources['ompt'] == 'download-tr6'
        self.uses_opari = not minimal and (self.measure_openmp == 'opari')
        self.uses_libotf2 = not minimal and (self.trace == 'otf2')
        self.uses_cuda = not minimal and (self.cuda_prefix and (self.cuda_support or self.opencl_support))
        if 'TIME' not in self.metrics[0]:
            # TAU assumes the first metric is always some kind of wallclock timer
            # so move the first wallclock metric to the front of the list
            for i, metric in enumerate(self.metrics):
                if 'TIME' in metric and 'TIME' not in self.metrics[0]:
                    self.metrics.insert(0, self.metrics.pop(i))
                    break
            else:
                self.metrics.insert(0, 'TIME')
        # Split comma separated metrics
        mets = []
        for met in self.metrics:
            mets.extend(met.split(','))
        self.metrics = mets
        uses = lambda pkg: sources[pkg] if forced_makefile else getattr(self, 'uses_'+pkg)
        for pkg in 'binutils', 'libunwind', 'papi', 'pdt', 'ompt', 'libotf2':
            if uses(pkg):
                self.add_dependency(pkg, sources)
        if uses('scorep'):
            self.add_dependency('scorep', sources, mpi_support, shmem_support,
                                uses('binutils'), uses('libunwind'), uses('papi'), uses('pdt'))
        self.check_env_compat()

    @classmethod
    def get_minimal(cls):
        """Creates a minimal TAU configuration for working with legacy data analysis tools.

        Returns:
            TauInstallation: Object handle for the TAU installation.
        """
        sources = {'tau': 'download'}
        target_arch = HOST_ARCH
        target_os = HOST_OS
        target_family = APPLE_LLVM if HOST_OS is DARWIN else GNU
        try:
            target_compilers = target_family.installation()
        except ConfigurationError:
            raise SoftwarePackageError("%s compilers (required to build TAU) could not be found." % target_family)
        for role in TAU_MINIMAL_COMPILERS:
            if role not in target_compilers:
                raise SoftwarePackageError("A %s compiler (required to build TAU) could not be found." % role.language)
        compilers = InstalledCompilerSet('minimal', Host_CC=target_compilers[CC], Host_CXX=target_compilers[CXX])
        inst = cls(sources, target_arch, target_os, compilers, minimal=True)
        return inst

    @classmethod
    def check_env_compat(cls):
        """Checks the current shell environment for incompatible libraries or modules.

        Other instrumentation packages like Darshan can conflict with TAU.  This routine
        checks that no conflicting packages are active in the current environment.

        Raises:
            ConfigurationError: TAU cannot be used in the current environment.
        """
        if 'DARSHAN_PRELOAD' in os.environ or 'darshan' in os.environ.get('LOADEDMODULES', '').lower():
            raise ConfigurationError("TAU cannot be used with darshan. ",
                                     "Unload the darshan module and try again.")
        if os.environ.get('PE_ENV', '').lower() == 'cray':
            raise ConfigurationError("TAU Commander cannot be used with Cray compilers. ",
                                     "Replace PrgEnv-cray with PrgEnv-intel, PrgEnv-gnu, or PrgEnv-pgi and try again.")

    def uid_items(self):
        uid_parts = [self.target_arch.name, self.target_os.name]
        # TAU changes if any compiler changes.
        uid_parts.extend(sorted(comp.uid for comp in self.compilers.itervalues()))
        # TAU changes if any dependencies change.
        for pkg in 'binutils', 'libunwind', 'papi', 'pdt', 'ompt', 'libotf2', 'scorep':
            if getattr(self, 'uses_'+pkg):
                uid_parts.append(self.dependencies[pkg].uid)
        # TAU changes if any of its hard-coded limits change
        uid_parts.extend([str(self._get_max_threads()), str(self._get_max_metrics())])
        if self.python_path:
            python_version = self.get_python_version(self.python_path)
            uid_parts.extend([self.python_path, python_version])
        return uid_parts

    def _get_max_threads(self):
        if self.max_threads:
            return self.max_threads
        else:
            if (self.pthreads_support or self.openmp_support or self.tbb_support or self.mpc_support):
                if self.target_arch in (INTEL_KNC, INTEL_KNL):
                    nprocs = 72 # Assume minimum 1 rank per quadrant w/ 4HTs
                    return nprocs
                else:
                    nprocs = multiprocessing.cpu_count()
                    # Assume 2 HTs/core
                    return max(64, 2*nprocs)
            else:
                return 25 # This is currently TAU's default.

    def _get_max_metrics(self):
        return len(self.metrics)

    def _get_install_tag(self):
        # Use `self.uid` as a TAU tag and the source package top-level directory as the installation tag
        # so multiple TAU installations share the large common files.
        if self._install_tag is None:
            source_archive = self.acquire_source()
            self._install_tag = util.archive_toplevel(source_archive)
            # If tau nightly, add current date to tag
            if self.src == NIGHTLY:
                nightlies=glob.glob(os.path.join(os.path.dirname(source_archive), 'tau-nightly-*.tgz'))
                nightlies_downloaded = True if nightlies else False
                if self.update_nightly or not nightlies_downloaded:
                    current_date = datetime.datetime.now().strftime('-%Y-%m-%d')
                    self._install_tag = self._install_tag + current_date
                    # Move to new tgz file
                    new_archive_name = os.path.join(os.path.dirname(source_archive), 'tau-nightly' + current_date + '.tgz')
                    os.rename(source_archive, new_archive_name)
                    self.src = new_archive_name
                else:
                    last_nightly = sorted(nightlies)[-1]
                    nightly_date = os.path.basename(last_nightly)[11:22]
                    self._install_tag = self._install_tag + nightly_date
                    self.src = last_nightly
        return self._install_tag

    def _verify_tau_libs(self, tau_makefile):
        makefile_tags = os.path.basename(tau_makefile).replace("Makefile.tau", "")
        static_lib = "libtau%s.*" % makefile_tags
        shared_lib = "libTAUsh%s.*" % makefile_tags
        for pattern in static_lib, shared_lib:
            if glob.glob(os.path.join(self.lib_path, pattern)):
                break
        else:
            raise SoftwarePackageError("TAU libraries for makefile '%s' not found" % tau_makefile)

    def _verify_dependency_paths(self, tau_makefile):
        LOGGER.debug("Checking dependency paths in '%s'", tau_makefile)
        with open(tau_makefile, 'r') as fin:
            for line in fin:
                if line.startswith('#'):
                    continue
                elif 'BFDINCLUDE=' in line:
                    if self.uses_binutils:
                        binutils = self.dependencies['binutils']
                        bfd_inc = shlex.split(line.split('=')[1])[0].strip('-I')
                        if not os.path.isdir(bfd_inc):
                            raise SoftwarePackageError("BFDINCLUDE in '%s' is not a directory" % tau_makefile)
                        if binutils.include_path != bfd_inc:
                            LOGGER.debug("BFDINCLUDE='%s' != '%s'", bfd_inc, binutils.include_path)
                            raise SoftwarePackageError("BFDINCLUDE in '%s' is not '%s'" %
                                                       (tau_makefile, binutils.include_path))
                elif 'UNWIND_INC=' in line:
                    if self.uses_libunwind:
                        libunwind = self.dependencies['libunwind']
                        libunwind_inc = line.split('=')[1].strip().strip("-I")
                        if not os.path.isdir(libunwind_inc):
                            raise SoftwarePackageError("UNWIND_INC in '%s' is not a directory" % tau_makefile)
                        if libunwind.include_path != libunwind_inc:
                            LOGGER.debug("UNWIND_INC='%s' != '%s'", libunwind_inc, libunwind.include_path)
                            raise SoftwarePackageError("UNWIND_INC in '%s' is not '%s'" %
                                                       (tau_makefile, libunwind.include_path))
                elif 'PAPIDIR=' in line:
                    if self.uses_papi:
                        papi = self.dependencies['papi']
                        papi_dir = line.split('=')[1].strip()
                        if not os.path.isdir(papi_dir):
                            raise SoftwarePackageError("PAPI_DIR in '%s' is not a directory" % tau_makefile)
                        if papi.install_prefix != papi_dir:
                            LOGGER.debug("PAPI_DIR='%s' != '%s'", papi_dir, papi.install_prefix)
                            raise SoftwarePackageError("PAPI_DIR in '%s' is not '%s'" %
                                                       (tau_makefile, papi.install_prefix))
                elif 'SCOREPDIR=' in line:
                    if self.uses_scorep:
                        scorep = self.dependencies['scorep']
                        scorep_dir = line.split('=')[1].strip()
                        if not os.path.isdir(scorep_dir):
                            raise SoftwarePackageError("SCOREPDIR in '%s' is not a directory" % tau_makefile)
                        if scorep.install_prefix != scorep_dir:
                            LOGGER.debug("SCOREPDIR='%s' != '%s'", scorep_dir, scorep.install_prefix)
                            raise SoftwarePackageError("SCOREPDIR in '%s' is not '%s'" %
                                                       (tau_makefile, scorep.install_prefix))
                elif 'OTFINC=' in line:
                    if self.uses_libotf2:
                        libotf2 = self.dependencies['libotf2']
                        libotf2_dir = line.split('=')[1].strip().strip("-I")
                        if not os.path.isdir(libotf2_dir):
                            raise SoftwarePackageError("OTFINC in '%s' is not a directory" % tau_makefile)
                        if libotf2.include_path != libotf2_dir:
                            LOGGER.debug("OTFINC='%s' != '%s'", libotf2_dir, libotf2.include_path)
                            raise SoftwarePackageError("OTFINC in '%s' is not '%s'" %
                                                       (tau_makefile, libotf2.include_path))

    def _verify_iowrapper(self, tau_makefile):
        # Replace right-most occurance of 'Makefile.tau' with 'shared'
        tagged_shared_dir = 'shared'.join(tau_makefile.rsplit('Makefile.tau', 1))
        for shared_dir in tagged_shared_dir, 'shared':
            iowrap_libs = glob.glob(os.path.join(shared_dir, 'libTAU-iowrap*'))
            if iowrap_libs:
                break
        else:
            raise SoftwarePackageError("TAU I/O wrapper libraries not found in '%s'" % shared_dir)
        LOGGER.debug("Found iowrap shared libraries: %s", iowrap_libs)
        io_wrapper_dir = os.path.join(self.lib_path, 'wrappers', 'io_wrapper')
        iowrap_link_options = os.path.join(io_wrapper_dir, 'link_options.tau')
        if not os.path.exists(iowrap_link_options):
            raise SoftwarePackageError("TAU I/O wrapper link options not found in '%s'" % io_wrapper_dir)
        LOGGER.debug("Found iowrap link options: %s", iowrap_link_options)

    def verify(self):
        super(TauInstallation, self).verify()
        if not self.minimal:
            if self.uses_papi and (HOST_ARCH == self.target_arch and HOST_OS == self.target_os):
                try:
                    self.dependencies['papi'].check_metrics(self.metrics)
                except ConfigurationError as err:
                    LOGGER.warning(err)
            tau_makefile = self.get_makefile()
            self._verify_tau_libs(tau_makefile)
            if not self.unmanaged:
                self._verify_dependency_paths(tau_makefile)
            if self.measure_io:
                self._verify_iowrapper(tau_makefile)
        LOGGER.debug("TAU installation at '%s' is valid", self.install_prefix)

    def _select_flags(self, header, libglobs, user_libraries, wrap_cc, wrap_cxx, wrap_fc):
        def unique(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]
        selected_inc, selected_lib, selected_library = None, None, None
        include_path = unique(wrap_cc.include_path + wrap_cxx.include_path + wrap_fc.include_path)
        if include_path:
            # Unfortunately, TAU's configure script can only accept one path on -mpiinc
            # and it expects the compiler's include path argument (e.g. "-I") to be omitted
            for path in include_path:
                if os.path.exists(os.path.join(path, header)):
                    selected_inc = path
                    break
            else:
                if self.tau_magic.operating_system is CRAY_CNL:
                    hints = ("Check that the 'cray-shmem' module is loaded",)
                else:
                    hints = tuple()
                raise ConfigurationError("%s not found on include path: %s" %
                                         (header, os.pathsep.join(include_path)),
                                         *hints)
        library_path = unique(wrap_cc.library_path + wrap_cxx.library_path + wrap_fc.library_path)
        if library_path:
            selected_lib = None
            for libglob in libglobs:
                # Unfortunately, TAU's configure script can only accept one path on -mpilib
                # and it expects the compiler's include path argument (e.g. "-L") to be omitted
                for path in library_path:
                    if glob.glob(os.path.join(path, libglob)):
                        selected_lib = path
                        break
            if not selected_lib:
                raise ConfigurationError("No files matched '%s' on library path: %s" %
                                         (libglobs, os.pathsep.join(library_path)))
        # Don't add autodetected Fortran or C++ libraries; C is probably OK
        libraries = unique(user_libraries + wrap_cc.libraries + wrap_cxx.libraries + wrap_fc.libraries)
        if libraries:
            # TAU's configure script accepts multiple libraries but only if they're separated by a '#' symbol
            # and the compiler's library linking flag (e.g. '-l') must be included
            link_library_flag = wrap_cc.info.family.link_library_flags[0]
            parts = [link_library_flag+lib for lib in libraries]
            # Also jam missing library path's onto this option
            library_path_flag = wrap_cc.info.family.library_path_flags[0]
            parts = [library_path_flag+path for path in library_path if path != selected_lib] + parts
            selected_library = '#'.join(parts)
        return selected_inc, selected_lib, selected_library

    def configure(self):
        """Configures TAU

        Executes TAU's configuration script with appropriate arguments to support the specified configuration.

        Raises:
            SoftwareConfigurationError: TAU's configure script failed.
        """
        binutils = self.dependencies.get('binutils')
        libunwind = self.dependencies.get('libunwind')
        papi = self.dependencies.get('papi')
        pdt = self.dependencies.get('pdt')
        scorep = self.dependencies.get('scorep')
        ompt = self.dependencies.get('ompt')
        libotf2 = self.dependencies.get('libotf2')

        if self.minimal:
            LOGGER.info("Configuring minimal TAU...")
            cmd = [flag for flag in
                   ['./configure',
                    '-tag=%s' % self.uid,
                    '-arch=%s' % self.tau_magic.name,
                    '-bfd=%s' % binutils.install_prefix if binutils else None,
                    '-unwind=%s' % libunwind.install_prefix if libunwind else None,
                   ] if flag]
            if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
                raise SoftwarePackageError('TAU configure failed')
            return

        # TAU's configure script can't cope with compiler absolute paths or compiler names that
        # don't exactly match what it expects.  Use `info.command` instead of `command` to work
        # around these problems e.g. 'gcc-4.9' becomes 'gcc'.
        # Also, TAU's configure script does a really bad job detecting wrapped compiler commands
        # so we unwrap the wrapper here before invoking configure.
        cc_command = self.compilers[CC].unwrap().info.command
        cxx_command = self.compilers[CXX].unwrap().info.command
        fc_comp = self.compilers[FC].unwrap() if FC in self.compilers else None
        # TAU's configure script can't detect Fortran compiler from the compiler
        # command so translate Fortran compiler command into TAU's magic words
        fortran_magic = None
        if fc_comp:
            fc_family = fc_comp.info.family
            fc_magic_map = {host_compilers.GNU: 'gfortran',
                            host_compilers.INTEL: 'intel',
                            host_compilers.PGI: 'pgi',
                            host_compilers.CRAY: 'cray',
                            host_compilers.IBM: 'ibm',
                            host_compilers.ARM: 'armflang',
                            host_compilers.IBM_BG: 'ibm'}
            try:
                fortran_magic = fc_magic_map[fc_family]
                if self.caf_support:
                    fortran_magic=self.compilers[CAF_FC].info.command
            except KeyError:
                LOGGER.warning("Can't determine TAU magic word for %s %s", fc_comp.info.short_descr, fc_comp)
                raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)

        # Set up MPI paths and libraries
        mpiinc, mpilib, mpilibrary = None, None, None
        if self.mpi_support:
            mpiinc, mpilib, mpilibrary = \
                self._select_flags('mpi.h', ('libmpi*',),
                                   self.mpi_libraries,
                                   self.compilers[MPI_CC],
                                   self.compilers[MPI_CXX],
                                   self.compilers[MPI_FC])

        # Set up SHMEM paths and libraries
        shmeminc, shmemlib, shmemlibrary = None, None, None
        if self.shmem_support:
            shmeminc, shmemlib, shmemlibrary = \
                self._select_flags('shmem.h', ('lib*shmem*', 'lib*sma*'),
                                   self.shmem_libraries,
                                   self.compilers[SHMEM_CC],
                                   self.compilers[SHMEM_CXX],
                                   self.compilers[SHMEM_FC])

        if self.python_support:
            # build TAU with --pythoninc and --pythonlib options using python-interpreter from target
            program = '''
import re
import sys
import os

def find_version():
    path = os.path.join(sys.prefix,'lib')
    all = os.listdir(path)
    p = re.compile(r'^(python)([1-9\\.]+)')
    for i in all:
        m = p.match(i)
        if m:
            version = m.group(2)
            break
    return {'version':version,'path':path}

print(find_version())
                    '''
            path = self.compilers[PY].absolute_path
            new_file, name = tempfile.mkstemp(suffix='py',text=True) # make a temporary file
            with os.fdopen(new_file, 'w') as f:
                f.write(program)
            data = get_command_output([path,name])
            # literal_eval converts string of dict to an actual python dict
            # "{'path': '/usr/lib', 'version': '2.7'}" -> {'path': '/usr/lib', 'version': '2.7'}
            data = ast.literal_eval(data)
            # pythonlib = data['path']
            pythoninc = data['path']+data['version']
            pythoninc = os.path.join(os.path.dirname(data['path']),'include')
            pythoninc = os.path.join(pythoninc,'python'+data['version'])

            # run ldd /usr/lib and save output
            out = get_command_output(['ldd',path])
            pattern = re.compile(r'.*=> (.*libpython[23a-z]\.\d.so[0-9\.]+)')
            pythonlib = pattern.search(out,re.MULTILINE)
            if pythonlib is not None:
                pythonlib = pythonlib.group(1) # group 1 is the path plus the file file where python is stored
                pythonlib = os.path.dirname(pythonlib) # pythonlib should just be the directory, not the file
            else:
                print 'output of ldd',out
                raise InternalError('output of ldd %s failed to match regex' % path)
            print 'pythonlib',pythonlib
            print 'pythoninc',pythoninc

        flags = [flag for flag in
                 ['-tag=%s' % self.uid,
                  '-arch=%s' % self.tau_magic.name,
                  '-cc=%s' % cc_command,
                  '-c++=%s' % cxx_command,
                  '-fortran=%s' % fortran_magic if fortran_magic else None,
                  '-bfd=%s' % binutils.install_prefix if binutils else None,
                  '-papi=%s' % papi.install_prefix if papi else None,
                  '-unwind=%s' % libunwind.install_prefix if libunwind else None,
                  '-scorep=%s' % scorep.install_prefix if scorep else None,
                  '-tbb' if self.tbb_support else None,
                  '-mpi' if self.mpi_support else None,
                  '-mpiinc=%s' % mpiinc if mpiinc else None,
                  '-mpilib=%s' % mpilib if mpilib else None,
                  '-mpilibrary=%s' % mpilibrary if mpilibrary else None,
                  '-cuda=%s' % self.cuda_prefix if self.uses_cuda else None,
                  '-opencl=%s' % self.opencl_prefix if self.opencl_prefix else None,
                  '-shmem' if self.shmem_support else None,
                  '-shmeminc=%s' % shmeminc if shmeminc else None,
                  '-shmemlib=%s' % shmemlib if shmemlib else None,
                  '-shmemlibrary=%s' % shmemlibrary if shmemlibrary else None,
                  '-pythoninc=%s' % pythoninc if self.python_support else None,
                  '-pythonlib=%s' % pythonlib if self.python_support else None,
                  '-otf=%s' % libotf2.install_prefix if libotf2 else None,
                 ] if flag]
        if pdt:
            flags.append('-pdt=%s' % pdt.install_prefix)
            flags.append('-pdt_c++=%s' % pdt.compilers[CXX].unwrap().info.command)
        if self.pthreads_support:
            flags.append('-pthread')
        elif self.openmp_support:
            if self.measure_openmp == 'ignore':
                # Configure with -pthread to support multi-threading without instrumenting OpenMP directives
                flags.append('-pthread')
            else:
                flags.append('-openmp')
                if self.measure_openmp == 'ompt':
                    if ompt:
                        comp_version = self.compilers[CC].version
                        if comp_version is not None and self.compilers[CC].info.family.name == 'Intel' and comp_version[0] >= 19:
                            flags.append('-ompt')
                        else:
                            flags.append('-ompt=%s' % ompt.install_prefix)
                    if self.uses_ompt_tr6:
                        flags.append('-ompt-tr6')
                elif self.measure_openmp == 'opari':
                    flags.append('-opari')
                else:
                    raise InternalError("Invalid value for measure_openmp: %s" % self.measure_openmp)
        if self.measure_io:
            flags.append('-iowrapper')
        if self.dyninst:
            flags.append('-dyninst=download')
        if self.uses_python:
            flags.append('-python')
        if self.mpit:
            print 'append mpit'
            flags.append('-mpit')

        # Use -useropt for hacks and workarounds.
        useropts = ['-O2', '-g']
        # Work around TAU's silly hard-coded limits.
        useropts.extend(['-DTAU_MAX_THREADS=%d' % self._get_max_threads(),
                         '-DTAU_MAX_METRICS=%d' % self._get_max_metrics(),
                         '-DTAU_MAX_COUNTERS=%d' % self._get_max_metrics()])
        # -useropt flag uses '#' as an argument separator
        flags.append('-useropt=' + '#'.join(useropts))

        cmd = ['./configure'] + flags
        LOGGER.info("Configuring TAU...")
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('TAU configure failed')

    def make_install_minimal(self):
        cmd = ['make'] + parallel_make_flags()
        LOGGER.info('Compiling trace input library...')
        util.create_subprocess(cmd, cwd=os.path.join(self._src_prefix, 'src/TraceInput'), stdout=False, show_progress=True)

        cmd = ['make', '-k', 'install'] + parallel_make_flags()
        LOGGER.info('Compiling TAU utilities...')
        # Nonzero return value is ignored since a full make would be required for all utilities to build.
        # Just cross your fingers and hope that the utilities you need are compiled.
        # If they don't build then package verification will fail so no harm done.
        util.create_subprocess(cmd, cwd=os.path.join(self._src_prefix, 'utils'), stdout=False, show_progress=True)

    def make_install(self):
        """Installs TAU to ``self.install_prefix``.

        Executes 'make install' to build and install TAU.

        Raises:
            SoftwarePackageError: 'make install' failed.
        """
        cmd = ['make', 'install'] + parallel_make_flags()
        LOGGER.info('Compiling TAU...')
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('TAU compilation/installation failed')

    def install(self, force_reinstall=False):
        """Installs TAU.

        Configures, compiles, and installs TAU with all necessarry makefiles and libraries.

        Args:
            force_reinstall (bool): Set to True to force reinstall even if TAU is already installed and working.

        Raises:
            SoftwarePackageError: TAU failed installation or did not pass verification after it was installed.
        """
        self.check_env_compat()
        if self.forced_makefile:
            forced_install_prefix = os.path.abspath(os.path.join(os.path.dirname(self.forced_makefile), '..', '..'))
            self._set_install_prefix(forced_install_prefix)
            LOGGER.warning("TAU makefile was forced! Not verifying TAU installation")
            return
        unmanaged_hints = ["Allow TAU Commander to manage your TAU configurations",
                           "Check for earlier error or warning messages",
                           "Ask your system administrator to build any missing TAU configurations mentioned above"]
        if self.unmanaged or not force_reinstall:
            try:
                return self.verify()
            except SoftwarePackageError as err:
                if self.unmanaged:
                    raise SoftwarePackageError("%s source package is unavailable and the installation at '%s' "
                                               "is invalid:\n\n    %s" % (self.title, self.install_prefix, err),
                                               *unmanaged_hints)
                elif not force_reinstall:
                    LOGGER.info("TAU must be reconfigured: %s", err)
        if self.unmanaged and not util.path_accessible(self.src, 'w'):
            raise SoftwarePackageError("Unable to configure TAU: '%s' is not writable." % self.install_prefix,
                                       *unmanaged_hints)
        # Check dependencies after verifying TAU instead of before in case
        # we're using an unmanaged TAU or forced makefile.
        for pkg in self.dependencies.itervalues():
            pkg.install(force_reinstall)
        LOGGER.info("Installing %s at '%s'", self.title, self.install_prefix)
        with new_os_environ(), util.umask(002):
            try:
                # Keep reconfiguring the same source because that's how TAU works
                if not (self.include_path and os.path.isdir(self.include_path)):
                    shutil.move(self._prepare_src(), self.install_prefix)
                self._src_prefix = self.install_prefix
                self.installation_sequence()
                self.set_group()
            except SoftwarePackageError as err:
                if not util.path_accessible(self.install_prefix, 'w'):
                    err.value += ": the TAU installation at '%s' is not writable" % self.install_prefix
                    err.hints = ["Grant write permission on '%s'" % self.install_prefix] + unmanaged_hints + err.hints
                    parent_prefix = os.path.dirname(self.install_prefix)
                    if util.path_accessible(parent_prefix, 'w'):
                        err.value += " (but the parent directory is)"
                raise err
            except Exception as err:
                LOGGER.info("%s installation failed: %s", self.title, err)
                raise
        # Verify the new installation
        LOGGER.info("Verifying %s installation...", self.title)
        return self.verify()

    def installation_sequence(self):
        self.configure()
        if self.minimal:
            self.make_install_minimal()
        else:
            self.make_install()
        # Rebuild makefile cache on next call to get_makefile()
        # since a new, possibly better makefile is now available
        self._tau_makefile = None

    def _compiler_tags(self):
        return {host_compilers.INTEL: 'intel' if self.tau_magic.operating_system is CRAY_CNL else 'icpc',
                host_compilers.PGI: 'pgi'}

    def get_tags(self):
        """Get tags for this TAU installation.

        Each TAU configuration (makefile, library, Python bindings, etc.) is identified by its tags.
        Tags can appear in the makefile name in any order so the order of the tags returned by this
        function will likely not match the order they appear in the makefile name or tau_exec command line.

        Returns:
            set: Makefile tags, e.g. set('papi', 'pdt', 'icpc')
        """
        tags = set()
        tags.add(self.uid)
        cxx_compiler = self.compilers[CXX].unwrap()
        try:
            tags.add(self._compiler_tags()[cxx_compiler.info.family])
        except KeyError:
            pass
        if self.uses_pdt:
            tags.add('pdt')
        if self.uses_papi:
            tags.add('papi')
        if self.uses_scorep:
            tags.add('scorep')
        if self.pthreads_support:
            tags.add('pthread')
        elif self.openmp_support:
            if self.measure_openmp == 'ignore':
                tags.add('pthread')
            else:
                tags.add('openmp')
                if self.measure_openmp == 'ompt':
                    tags.add('ompt')
                    if self.uses_ompt_tr6:
                        tags.add('tr6')
                elif self.measure_openmp == 'opari':
                    tags.add('opari')
                else:
                    raise InternalError("Invalid value for measure_openmp: '%s'" % self.measure_openmp)
        if self.tbb_support:
            tags.add('tbb')
        if self.mpi_support:
            tags.add('mpi')
        if self.cuda_support or self.opencl_support:
            tags.add('cupti')
        if self.shmem_support:
            tags.add('shmem')
        if self.mpc_support:
            tags.add('mpc')
        if self.python_support:
            tags.add('python')
        if self.mpit:
            tags.add('mpit')
        if self.tags:
            for tag in self.tags:
                tags.add(tag)
        LOGGER.debug("TAU tags: %s", tags)
        return tags

    def _incompatible_tags(self):
        """Returns a set of makefile tags incompatible with the specified config."""
        tags = set()
        cxx_compiler = self.compilers[CXX].unwrap()
        # On Cray, TAU ignores compiler command line arguments and tags makefiles
        # according to what is specified in $PE_ENV, so the minimal configuration
        # could have any compiler tag and still be compatible.
        # On non-Cray systems, exclude tags from incompatible compilers.
        compiler_tags = self._compiler_tags() if self.tau_magic.operating_system is not CRAY_CNL else {}
        compiler_tag = compiler_tags.get(cxx_compiler.info.family, None)
        tags.update(tag for tag in compiler_tags.itervalues() if tag != compiler_tag)
        if not self.mpi_support:
            tags.add('mpi')
        if self.measure_openmp == 'ignore':
            tags.add('openmp')
            tags.add('opari')
            tags.add('ompt')
            tags.add('tr6')
            tags.add('gomp')
        if not self.uses_scorep:
            tags.add('scorep')
        if not self.shmem_support:
            tags.add('shmem')
        LOGGER.debug("Incompatible tags: %s", tags)
        return tags

    def _makefile_tags(self, makefile):
        return set(os.path.basename(makefile).split('.')[1].split('-')[1:])

    def _match_makefile(self, config_tags):
        tau_makefiles = glob.glob(os.path.join(self.lib_path, 'Makefile.tau*'))
        LOGGER.debug("Found makefiles: '%s'", tau_makefiles)
        dangerous_tags = self._incompatible_tags()
        LOGGER.debug("Will not use makefiles containing tags: %s", dangerous_tags)
        approx_tags = None
        approx_makefile = None
        for makefile in tau_makefiles:
            tags = self._makefile_tags(makefile)
            LOGGER.debug("%s has tags: %s", makefile, tags)
            if config_tags <= tags:
                LOGGER.debug("%s contains desired tags: %s", makefile, config_tags)
                if tags <= config_tags:
                    LOGGER.debug("Found TAU makefile %s", makefile)
                    return makefile
                elif not tags.intersection(dangerous_tags):
                    if not approx_tags or tags < approx_tags:
                        approx_makefile = makefile
                        approx_tags = tags
        return approx_makefile

    def get_makefile(self):
        """Returns an absolute path to a TAU_MAKEFILE.

        The file returned *should* supply all requested measurement features
        and application support features specified in the constructor.

        Returns:
            str: A file path that could be used to set the TAU_MAKEFILE environment
                 variable, or None if a suitable makefile couldn't be found.
        """
        if self._tau_makefile:
            return self._tau_makefile
        if self.forced_makefile:
            self._tau_makefile = self.forced_makefile
            return self.forced_makefile
        config_tags = self.get_tags()
        LOGGER.debug("Searching for makefile with tags: %s", config_tags)
        makefile = self._match_makefile(config_tags)
        if not makefile:
            LOGGER.debug("No TAU makefile exactly matches tags '%s'", config_tags)
            if not self.unmanaged:
                # This is a managed TAU installation so we can build it.
                raise SoftwarePackageError("TAU Makefile not found for tags '%s' in '%s'" %
                                           (', '.join(config_tags), self.install_prefix))
            # Ignore UID and try again in case the TAU configuration was built manually without a UID.
            # Warn the user that it's on them to know that the makefile is correct.
            config_tags.remove(self.uid)
            makefile = self._match_makefile(config_tags)
            if not makefile:
                LOGGER.debug("No TAU makefile approximately matches tags '%s'", config_tags)
                raise SoftwarePackageError("TAU Makefile not found for tags '%s' in '%s'" %
                                           (', '.join(config_tags), self.install_prefix))
        makefile = os.path.join(self.lib_path, makefile)
        LOGGER.debug("Found TAU makefile %s", makefile)
        self._tau_makefile = makefile
        return makefile

    @staticmethod
    def _sanitize_environment(env):
        """Unsets any TAU environment variables that were set by the user.

        A user's preexisting TAU configuration may conflict with the configuration
        specified by the TAU Commander project.  This routine lets us work in a
        clean environment without disrupting the user's shell environment.

        Args:
            env (dict): Environment variables.

        Returns:
            dict: `env` without TAU environment variables.
        """
        is_tau_var = lambda x: x.startswith('TAU_') or x.startswith('SCOREP_') or x in ('PROFILEDIR', 'TRACEDIR')
        dirt = {key: val for key, val in env.iteritems() if is_tau_var(key)}
        if dirt:
            LOGGER.info("\nIgnoring TAU environment variables set in user's environment:\n%s\n",
                        '\n'.join(["%s=%s" % item for item in dirt.iteritems()]))
        return dict([item for item in env.iteritems() if item[0] not in dirt])

    def compiletime_config(self, compiler, opts=None, env=None):
        """Configures environment for compilation with TAU.

        Modifies incoming command line arguments and environment variables
        for the TAU compiler wrapper scripts.

        Args:
            opts (list): Command line options.
            env (dict): Environment variables.

        Returns:
            tuple: (opts, env) updated to support TAU.
        """
        # The additional `compiler` argument is needed to TAU falls back to the right compiler
        # pylint: disable=arguments-differ
        opts, env = super(TauInstallation, self).compiletime_config(opts, env)
        env = self._sanitize_environment(env)
        if self.baseline:
            return opts, env
        for pkg in self.dependencies.itervalues():
            opts, env = pkg.compiletime_config(opts, env)

        try:
            tau_opts = set(self.force_tau_options)
        except AttributeError:
            try:
                tau_opts = set(env['TAU_OPTIONS'].split())
            except KeyError:
                tau_opts = set()
            try:
                tau_opts = set(self.extra_tau_options)
            except AttributeError:
                tau_opts = set()
            if self.source_inst != 'never' or self.compiler_inst != 'never':
                for flag in '-optAppCC', '-optAppCXX', '-optAppF90':
                    tau_opts.add(flag+'='+compiler.absolute_path)
            if self.source_inst == 'manual' or (self.source_inst == 'never' and self.compiler_inst == 'never'):
                tau_opts.add('-optLinkOnly')
            else:
                tau_opts.add('-optRevert')
            if self.verbose:
                tau_opts.add('-optVerbose')
            if self.compiler_inst == 'always':
                tau_opts.add('-optCompInst')
            elif self.compiler_inst == 'never':
                tau_opts.add('-optNoCompInst')
            elif self.compiler_inst == 'fallback':
                tau_opts.add('-optRevert')
            if self.keep_inst_files:
                tau_opts.add('-optKeepFiles')
            if self.reuse_inst_files:
                tau_opts.add('-optReuseFiles')
            if self.select_file:
                select_file = os.path.realpath(os.path.abspath(self.select_file))
                tau_opts.add('-optTauSelectFile=%s' % select_file)
            if self.measure_io:
                tau_opts.add('-optTrackIO')
            if self.measure_memory_alloc:
                tau_opts.add('-optMemDbg')
            if self.openmp_support and self.source_inst == 'automatic':
                tau_opts.add('-optContinueBeforeOMP')
            if logger.LOG_LEVEL != 'DEBUG':
                tau_opts.add('-optQuiet')
            if self.sample or self.compiler_inst != 'never':
                opts.append('-g')
            if self.source_inst != 'never' and self.compilers[CC].unwrap().info.family is not IBM:
                opts.append('-DTAU_ENABLED=1')
        try:
            extra_tau_opts = set(self.extra_tau_options)
            tau_opts |= extra_tau_opts
        except AttributeError:
            pass
        env['TAU_OPTIONS'] = ' '.join(tau_opts)
        makefile = self.get_makefile()
        tags = self._makefile_tags(makefile)
        if self.uid not in tags:
            LOGGER.warning("Unable to verify compiler compatibility of TAU makefile '%s'.\n\n"
                           "This might be OK, but it is your responsibility to know that TAU was configured "
                           "correctly for your experiment. Compiler incompatibility may cause your experiment "
                           "to crash or produce invalid data.  If you're unsure, use --tau=download to allow "
                           "TAU Commander to manage your TAU configurations.", makefile)
        env['TAU_MAKEFILE'] = makefile
        return list(set(opts)), env


    def runtime_config(self, opts=None, env=None):
        """Configures environment for execution with TAU.

        Modifies incoming command line arguments and environment variables
        for the TAU library and tau_exec script.

        Args:
            opts (list): Command line options.
            env (dict): Environment variables.

        Returns:
            tuple: (opts, env) updated to support TAU.
        """
        opts, env = super(TauInstallation, self).runtime_config(opts, env)
        env = self._sanitize_environment(env)
        env['TAU_VERBOSE'] = str(int(self.verbose))
        if self.profile == 'tau':
            env['TAU_PROFILE'] = '1'
        elif self.profile == 'merged':
            env['TAU_PROFILE'] = '1'
            env['TAU_PROFILE_FORMAT'] = 'merged'
        elif self.profile == 'cubex':
            env['SCOREP_ENABLE_PROFILING'] = '1'
        else:
            env['TAU_PROFILE'] = '0'
            env['SCOREP_ENABLE_PROFILING'] = 'false'
        if self.trace == 'slog2':
            env['TAU_TRACE'] = '1'
        elif self.trace == 'otf2':
            env['TAU_TRACE'] = '1'
            env['TAU_TRACE_FORMAT'] = 'otf2'
        else:
            env['TAU_TRACE'] = '0'
            env['SCOREP_ENABLE_TRACING'] = 'false'
        env['TAU_SAMPLING'] = str(int(self.sample))
        if self.sample:
            # Based on periods shown in TauEnv.cpp as of tau2/e481b2bbc98c014a225d79bc4d0959b203d840d4
            arch_period = {INTEL_KNC: 100000,
                           INTEL_KNL: 100000,
                           IBM_BGL: 20000,
                           IBM_BGP: 20000,
                           IBM_BGQ: 50000}
            if self.sampling_period > 0:
                env['TAU_EBS_PERIOD'] = str(self.sampling_period)
            else:
                self.smapling_period = arch_period.get(self.target_arch, 10000)
                env['TAU_EBS_PERIOD'] = str(self.sampling_period)
        env['TAU_TRACK_HEAP'] = str(int(self.measure_heap_usage))
        env['TAU_TRACK_LOAD'] = str(int(self.measure_system_load))
        env['TAU_COMM_MATRIX'] = str(int(self.measure_comm_matrix))
        env['TAU_CALLSITE'] = str(int(self.measure_callsite))
        env['TAU_METRICS'] = ",".join(self.metrics) + ","
        env['TAU_THROTTLE'] = str(int(self.throttle))
        env['TAU_MERGE_METADATA'] = str(int(self.metadata_merge))
        env['TAU_TRACK_MEMORY_FOOTPRINT'] = str(int(self.track_memory_footprint))
        if self.throttle:
            env['TAU_THROTTLE_PERCALL'] = str(int(self.throttle_per_call))
            env['TAU_THROTTLE_NUMCALLS'] = str(int(self.throttle_num_calls))
        if self.callpath_depth > 0:
            env['TAU_CALLPATH'] = '1'
            env['TAU_CALLPATH_DEPTH'] = str(self.callpath_depth)
        if self.unwind_depth > 0:
            env['TAU_EBS_UNWIND'] = '1'
            env['TAU_EBS_UNWIND_DEPTH'] = str(self.unwind_depth)
        if self.select_file and self.application_linkage == 'dynamic':
            env['TAU_SELECT_FILE'] = os.path.realpath(os.path.abspath(self.select_file))
        if self.verbose:
            opts.append('-v')
        if self.sample:
            opts.append('-ebs')
        if self.measure_cuda:
            opts.append('-cupti')
        if self.measure_opencl:
            opts.append('-opencl')
        if self.measure_openmp == 'ompt':
            opts.append('-ompt')
        if self.uses_ompt_tr6:
            env['TAU_OMPT_RESOLVE_ADDRESS_EAGERLY'] = '1'
        if self.measure_io:
            opts.append('-io')
        if self.measure_memory_alloc:
            env['TAU_SHOW_MEMORY_FUNCTIONS'] = '1'
            opts.append('-memory')
        if self.measure_shmem:
            opts.append('-shmem')
        if self.ptts:
            opts.append('-ptts')
        if self.ptts_post:
            opts.append('-ptts-post')
        if self.ptts_sample_flags:
            opts.append('-ptts-sample-flags=%s' %self.ptts_sample_flags)
        if self.ptts_report_flags:
            opts.append('-ptts-report-flags=%s' %self.ptts_report_flags)
        return list(set(opts)), env

    def get_compiler_command(self, compiler):
        """Get the compiler wrapper command for the given compiler.

        Args:
            compiler (InstalledCompiler): A compiler to find a wrapper for.

        Returns:
            str: Command for TAU compiler wrapper without path or arguments.
        """
        use_wrapper = (not self.baseline and
                       (self.source_inst != 'never' or
                        self.compiler_inst != 'never' or
                        self.measure_openmp == 'opari' or
                        self.application_linkage == 'static'))
        if use_wrapper:
            return TAU_COMPILER_WRAPPERS[compiler.info.role]
        else:
            return compiler.absolute_path

    def compile(self, compiler, compiler_args):
        """Executes a compilation command.

        Sets TAU environment variables and configures TAU compiler wrapper
        command line arguments to match specified configuration, then
        executes the compiler command.

        Args:
            compiler (InstalledCompiler): A compiler command.
            compiler_args (list): Compiler command line arguments.

        Raises:
            ConfigurationError: Compilation failed.

        Returns:
            int: Compiler return value (always 0 if no exception raised).
        """
        self.install()
        opts, env = self.compiletime_config(compiler)
        compiler_cmd = self.get_compiler_command(compiler)
        cmd = [compiler_cmd] + opts + compiler_args
        tau_env_opts = sorted('%s=%s' % item for item in env.iteritems() if item[0].startswith('TAU_'))
        LOGGER.debug('\n'.join(tau_env_opts))
        LOGGER.debug(' '.join(cmd))
        retval = util.create_subprocess(cmd, env=env, stdout=True)
        if retval != 0:
            raise ConfigurationError("TAU was unable to build the application.",
                                     "Check that the application builds with its normal compilers, i.e. without TAU.",
                                     "Use taucmdr --log and see detailed output at the end of '%s'" % logger.LOG_FILE)
        return retval

    def _rewrite_launcher_appfile_cmd(self, cmd, tau_exec):
        launcher = cmd[0]
        appfile_flags = PROGRAM_LAUNCHERS.get(launcher)
        if not appfile_flags:
            raise InternalError("Application configuration file flags for '%s' are unknown" % launcher)
        for i, flag in enumerate(cmd[1:], 1):
            try:
                flag, appfile = flag.split('=')
                with_equals = True
            except ValueError:
                try:
                    appfile = cmd[i+1]
                    with_equals = False
                except IndexError:
                    raise InternalError("Unable to parse application configuration file in '%s'" % cmd)
            if flag in appfile_flags:
                appfile_arg_idx = i
                appfile_flag = flag
                break
        else:
            raise InternalError("None of '%s' found in '%s'" % (appfile_flags, cmd))
        tau_appfile = os.path.join(util.mkdtemp(), appfile+".tau")
        LOGGER.debug("Rewriting '%s' as '%s'", appfile, tau_appfile)
        with open(tau_appfile, 'w') as fout, open(appfile, 'r') as fin:
            for lineno, line in enumerate(fin, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                application_cmd = line.split()
                if launcher == 'srun':
                    # Slurm makes this easy: https://computing.llnl.gov/tutorials/linux_clusters/multi-prog.html
                    idx = 1
                else:
                    for idx, exe in enumerate(application_cmd):
                        if util.which(exe):
                            break
                    else:
                        raise ConfigurationError("No executables found on line %d of '%s'" % (lineno, appfile),
                                                 "Check the file for errors. Does it work without TAU?",
                                                 "Avoid breaking commands over multiple lines.")
                tau_line = ' '.join(application_cmd[:idx] + tau_exec + application_cmd[idx:] + ['\n'])
                LOGGER.debug(tau_line)
                fout.write(tau_line)
        if with_equals:
            return cmd[:appfile_arg_idx] + [appfile_flag+'='+tau_appfile] + cmd[appfile_arg_idx+1:]
        else:
            return cmd[:appfile_arg_idx] + [appfile_flag, tau_appfile] + cmd[appfile_arg_idx+2:]

    def get_application_command(self, launcher_cmd, application_cmds):
        """Build a command line to launch an application under TAU.

        Sometimes TAU needs to use tau_exec, sometimes not.  This routine
        also handles backend launch commands like ``aprun``.

        `application_cmds` may be an empty list if the application is launched
        via a configuration file, e.g. ``mpirun --app myapp.cfg``.

        Args:
            launcher_cmd (list): Application launcher with command line arguments, e.g. ``['mpirun', '-np', '4']``.
            application_cmds (list): List of application command with command line arguments (list of list),
                                     e.g. ``[['./a.out', '-g', 'hello'], [':', '-np', '2', './b.out', 'foobar']]``

        Returns:
            tuple: (cmd, env) where `cmd` is the new command line and `env` is a dictionary of environment
                   variables to set before running the application command.
        """
        self.install()
        opts, env = self.runtime_config()
        # Per Sameer's request, shim in site-specific flags.
        # These should be specified in a taucmdr module or similar.
        try:
            launcher_cmd.extend(os.environ['__TAUCMDR_LAUNCHER_ARGS__'].split(' '))
        except KeyError:
            pass
        if self.baseline:
            cmd = ['tau_baseline'] + launcher_cmd
            for application_cmd in application_cmds:
                cmd.extend(application_cmd)
            return cmd, env
        if any('python' in subcmd for subcmd in launcher_cmd):
            #self.uses_python=True
            self._tau_makefile=None
            self._uid = None
            for subcmd in launcher_cmd:
                if 'python' in subcmd:
                    self.python_path = subcmd
            self.install()
        use_tau_exec = (self.application_linkage != 'static' and
                        (self.profile != 'none' or self.trace != 'none') and
                        ((self.source_inst == 'never' and self.compiler_inst == 'never') or
                         self.measure_opencl or
                         self.tbb_support or
                         self.pthreads_support) and not self.python_support)
        if not use_tau_exec:
            tau_exec = []
            if self.python_support:
                makefile = self.get_makefile()
                tags = self._makefile_tags(makefile)
                if not self.mpi_support:
                    tags.add('serial')
                tau_exec = ['tau_python', '-T', ','.join([tag for tag in tags if tag != 'python']), '-tau-python-interpreter=%s' % self.python_path] + opts
                launcher_cmd = []
        else:
            makefile = self.get_makefile()
            tags = self._makefile_tags(makefile)
            if not self.mpi_support:
                tags.add('serial')
            if self.uid not in tags and self.unmanaged:
                LOGGER.warning("Unable to verify runtime compatibility of TAU makefile '%s'.\n\n"
                               "This might be OK, but it is your responsibility to know that TAU was configured "
                               "correctly for your experiment. Runtime incompatibility may cause your experiment "
                               "to crash or produce invalid data.  If you're unsure, use '--tau=download' when "
                               "creating your target to allow TAU Commander to manage your TAU configurations.",
                               makefile)
            tau_exec = ['tau_exec', '-T', ','.join(tags)] + opts
        if not application_cmds:
            cmd = self._rewrite_launcher_appfile_cmd(launcher_cmd, tau_exec)
        else:
            cmd = launcher_cmd
            cmd.extend(tau_exec)
            cmd.extend(application_cmds[0])
            for application_cmd in application_cmds[1:]:
                for i, part in enumerate(application_cmd):
                    if util.which(part):
                        cmd.extend(application_cmd[:i])
                        cmd.extend(tau_exec)
                        cmd.extend(application_cmd[i:])
                        break
                else:
                    raise InternalError("Application command '%s' contains no executables" % application_cmd)
        return cmd, env

    def _check_java(self):
        abspath = util.which('java')
        if not abspath:
            raise ConfigurationError("'java' not found in PATH")
        try:
            stdout = util.get_command_output([abspath, '-version'])
        except (CalledProcessError, OSError) as err:
            raise ConfigurationError("Failed to get Java version: %s" % err)
        if 'Java(TM)' not in stdout:
            LOGGER.warning("'%s' does not appear to be Oracle Java.  Visual performance may be poor.", abspath)

    def _check_X11(self):  # pylint: disable=invalid-name
        _, env = self.runtime_config()
        try:
            display = env['DISPLAY']
        except KeyError:
            raise ConfigurationError("X11 display not configured.",
                                     "Try setting the DISPLAY environment variable.")
        try:
            host, _ = display.split(':')
        except ValueError:
            LOGGER.warning("Cannot parse DISPLAY environment variable.")
        if host and not host.startswith('/'):
            LOGGER.warning("X11 appears to be forwarded to a remote display. Visual performance may be poor.")

    def get_data_format(self, path):
        """Guess the data format of a file path.

        Look at a file's extension and guess what kind of performance data it might be.

        Args:
            path (str): File path.

        Returns:
            str: String indicating the data format.

        Raises:
            ConfigurationError: Cannot determine the file's data format.
        """
        root, ext = os.path.splitext(path)
        if os.path.isdir(path) or root == 'profile':
            return 'tau'
        elif ext == '.ppk':
            return 'ppk'
        elif ext == '.xml':
            return 'merged'
        elif ext == '.cubex':
            return 'cubex'
        elif ext == '.slog2':
            return 'slog2'
        elif ext == '.otf2':
            return 'otf2'
        elif ext == '.gz':
            root, ext = os.path.splitext(root)
            if ext == '.xml':
                return 'merged'
        raise ConfigurationError("Cannot determine data format of '%s'" % path)

    def is_profile_format(self, fmt):
        """Return True if ``fmt`` is a string indicating a profile data format."""
        return fmt in ('tau', 'ppk', 'merged', 'cubex')

    def is_trace_format(self, fmt):
        """Return True if ``fmt`` is a string indicating a trace data format."""
        return fmt in ('slog2', 'otf2')

    def _show_unknown(self, tool):
        def launcher(_, paths, env):
            cmd = [tool] + paths
            LOGGER.warning("'%s' not supported. Trying command '%s'", tool, ' '.join(cmd))
            try:
                return util.create_subprocess(cmd, env=env)
            except (CalledProcessError, OSError) as err:
                raise ConfigurationError("'%s' failed: %s" % (tool, err))
        return launcher

    def _show_paraprof(self, fmt, paths, env):
        self._check_java()
        self._check_X11()
        for path in paths:
            if not os.path.exists(path):
                raise ConfigurationError("Profile file '%s' does not exist" % path)
        if fmt == 'tau':
            retval = 0
            for path in paths:
                retval += util.create_subprocess([os.path.join(self.bin_path, 'paraprof')], cwd=path, env=env)
            return retval
        else:
            return util.create_subprocess([os.path.join(self.bin_path, 'paraprof')] + paths, env=env)

    def _show_pprof(self, fmt, paths, env):
        if fmt != 'tau':
            raise ConfigurationError("pprof cannot open profiles in '%s' format" % fmt)
        retval = 0
        for path in paths:
            if not os.path.exists(path):
                raise ConfigurationError("Profile directory '%s' does not exist" % path)
            for thisdir, subdirs, files in os.walk(path):
                if any(file_name.startswith("profile") for file_name in files):
                    LOGGER.info("\nCurrent trial/metric directory: %s", os.path.basename(thisdir))
                    retval += util.create_subprocess([os.path.join(self.bin_path, 'pprof'), '-a'], cwd=thisdir, env=env)
                elif any(subdir.startswith("MULTI__") for subdir in subdirs):
                    for subdir in [file_name.startswith("MULTI__") for file_name in files]:
                        LOGGER.info("\nCurrent trial/metric directory: %s", os.path.basename(subdir))
                        retval += util.create_subprocess([os.path.join(self.bin_path, 'pprof'), '-a'], cwd=subdir, env=env)
                else:
                    raise ConfigurationError("No profile files found in '%s'" % path)
        return retval

    def _show_jumpshot(self, fmt, paths, env):
        if fmt != 'slog2':
            raise ConfigurationError("jumpshot cannot open traces in '%s' format" % fmt)
        self._check_java()
        self._check_X11()
        retval = 0
        for path in paths:
            if not os.path.exists(path):
                raise ConfigurationError("Trace file '%s' does not exist" % path)
            path = os.path.abspath(path)
            cwd = os.path.dirname(path)
            retval += util.create_subprocess([os.path.join(self.bin_path, 'jumpshot'), path],
                                             cwd=cwd, env=env, stdout=False)
        return retval

    def _show_vampir(self, fmt, paths, env):
        if fmt != 'otf2':
            raise ConfigurationError("Vampir cannot open traces in '%s' format" % fmt)
        if not util.which('vampir'):
            raise ConfigurationError("Vampir not found in PATH.")
        self._check_java()
        self._check_X11()
        retval = 0
        for path in paths:
            if not os.path.exists(path):
                raise ConfigurationError("Trace file '%s' does not exist" % path)
            path = os.path.abspath(path)
            cwd = os.path.dirname(path)
            evt_files = glob.glob(os.path.join(cwd, 'traces/*.evt'))
            def_files = glob.glob(os.path.join(cwd, 'traces/*.def'))
            if len(evt_files) + len(def_files) > resource.getrlimit(resource.RLIMIT_NOFILE)[0]:
                raise ConfigurationError("Too many trace files, use vampirserver to view.")
            retval += util.create_subprocess(['vampir', path], cwd=cwd, env=env)
        return retval

    def _prep_data_analysis_tools(self):
        """Checks that data analysis tools are installed, or installs them if needed."""
        if not glob.glob(os.path.join(self.lib_path, 'Makefile.tau*')):
            return self.install()
        for cmd in DATA_TOOLS:
            path = os.path.join(self.bin_path, cmd)
            if not (os.path.exists(path) and os.access(path, os.X_OK)):
                return self.install()

    def show_data_files(self, dataset, profile_tools=None, trace_tools=None):
        """Displays profile and trace data.

        Opens one more more data analysis tools to display the specified data files.

        Args:
            dataset (dict): Lists of paths to data files indexed by data format.  See :any:`get_data_format`.
            profile_tools (list): Visualization or data processing tools for profiles.
            trace_tools (list): Visualization or data processing tools for traces.

        Raises:
            ConfigurationError: An error occurred while displaying a data file.
        """
        self._prep_data_analysis_tools()
        _, env = self.runtime_config()
        for fmt, paths in dataset.iteritems():
            if self.is_profile_format(fmt):
                tools = profile_tools if profile_tools is not None else PROFILE_ANALYSIS_TOOLS
            elif self.is_trace_format(fmt):
                tools = trace_tools if trace_tools is not None else TRACE_ANALYSIS_TOOLS
            else:
                raise InternalError("Unhandled data format '%s'" % fmt)
            for tool in tools:
                try:
                    launcher = getattr(self, '_show_'+tool)
                except AttributeError:
                    launcher = self._show_unknown(tool)
                try:
                    retval = launcher(fmt, paths, env)
                except ConfigurationError as err:
                    LOGGER.warning("%s failed: %s", tool, err)
                else:
                    if retval == 0:
                        break
                    LOGGER.warning("%s returned %d, trying another tool", tool, retval)
            else:
                raise ConfigurationError("All analysis tools failed",
                                         "Check Java installation, X11 installation,"
                                         " network connectivity, and file permissions")

    def create_ppk_file(self, dest, src, remove_existing=True):
        """Write a PPK file at ``dest`` from the data at ``src``.

        Args:
            dest (str): Path to the PPK file to create.
            src (str): Directory containing TAU profiles to convert to PPK format.
            remove_existing (bool): If True, delete ``dest`` before writing it.
        """
        self._prep_data_analysis_tools()
        _, env = self.runtime_config()
        self._check_java()
        if remove_existing and os.path.exists(dest):
            os.remove(dest)
        cmd = ['paraprof', '--pack', dest]
        LOGGER.info("Writing '%s'...", dest)
        if util.create_subprocess(cmd, cwd=src, env=env, stdout=False, show_progress=True):
            raise ConfigurationError("'%s' failed in '%s'" % (' '.join(cmd), src),
                                     "Make sure Java is installed and working",
                                     "Install the most recent Java from http://java.com")

    def merge_tau_trace_files(self, prefix):
        """Use tau_treemerge.pl to merge multiple TAU trace files into a single edf and a single trc file.

        The new edf file and trc file are written to ``prefix``.

        Args:
            prefix (str): Path to the directory containing ``*.trc`` and ``*.edf`` files.
        """
        self._prep_data_analysis_tools()
        trc_files = glob.glob(os.path.join(prefix, '*.trc'))
        edf_files = glob.glob(os.path.join(prefix, '*.edf'))
        if not trc_files:
            raise ConfigurationError("No *.trc files at '%s'" % prefix)
        if not edf_files:
            raise ConfigurationError("No *.edf files at '%s'" % prefix)
        merged_trc = os.path.join(prefix, 'tau.trc')
        merged_edf = os.path.join(prefix, 'tau.edf')
        if os.path.isfile(merged_trc):
            raise ConfigurationError("Remove '%s' before merging *.trc files")
        if os.path.isfile(merged_edf):
            raise ConfigurationError("Remove '%s' before merging *.edf files")
        cmd = [os.path.join(self.bin_path, 'tau_treemerge.pl')]
        LOGGER.info("Merging %d TAU trace files...", len(trc_files) + len(edf_files))
        if util.create_subprocess(cmd, cwd=prefix, stdout=False, log=True, show_progress=True):
            raise InternalError("Nonzero return code from tau_treemerge.pl")

    def tau_trace_to_slog2(self, trc, edf, slog2):
        """Convert a TAU trace file to SLOG2 format.

        Args:
            trc (str): Path to the trc file.
            edf (str): Path to the edf file.
            slog2 (str): Path to the slog2 file to create.
        """
        self._prep_data_analysis_tools()
        LOGGER.info("Converting TAU trace files to SLOG2 format...")
        cmd = [os.path.join(self.bin_path, 'tau2slog2'), trc, edf, '-o', slog2]
        if util.create_subprocess(cmd, stdout=False, log=True, show_progress=True):
            os.remove(slog2)
            raise InternalError("Nonzero return code from tau2slog2")
        if not os.path.exists(slog2):
            raise InternalError("Failed to convert TAU trace data: no slog2 files exist after calling 'tau2slog2'")

    def tau_metrics(self):
        """List TAU metrics available on this target.

        Returns a list of (name, description) tuples.

        Returns:
            list: List of event name/description tuples.
        """
        metrics = [("LOGICAL_CLOCK", "Logical clock that increments on each request."),
                   ("USER_CLOCK", ("User-defined clock. Implement "
                                   "'void metric_write_userClock(int tid, double value)'  to set the clock value.")),
                   ("GET_TIME_OF_DAY", "Wall clock that calls gettimeofday."),
                   ("TIME", "Alias for GET_TIME_OF_DAY. Wall clock that calls gettimeofday."),
                   ("CLOCK_GET_TIME", "Wall clock that calls clock_gettime."),
                   ("P_WALL_CLOCK_TIME", "Wall clock that calls PAPI_get_real_usec."),
                   ("PAPI_TIME", "Alias for P_WALL_CLOCK_TIME.  Wall clock that calls PAPI_get_real_usec."),
                   ("P_VIRTUAL_TIME", "PAPI virtual clock that calls PAPI_get_virt_usec."),
                   ("PAPI_VIRTUAL_TIME", ("Alias for P_VIRTUAL_TIME.  "
                                          "PAPI virtual clock that calls PAPI_get_virt_usec.")),
                   ("CPU_TIME", "CPU timer that calls getrusage."),
                   ("LINUX_TIMERS", "Linux high resolution wall clock."),
                   ("TAU_MPI_MESSAGE_SIZE", "Running sum of all MPI messsage sizes."),
                   ("MEMORY_DELTA", "Instantaneous resident set size (RSS)")]
        if self.cuda_support:
            metrics.append(("TAUGPU_TIME", "Wall clock that uses TAU's GPU timestamps."))
        if self.target_os is CRAY_CNL:
            metrics.extend([("CRAY_TIMERS", "Cray high resolution clock."),
                            ("ENERGY", "Cray Power Monitoring: /sys/cray/pm_counters/energy"),
                            ("ACCEL_ENERGY", "Cray Power Monitoring: /sys/cray/pm_counters/accel_energy")])
        if self.target_arch is IBM_BGL:
            metrics.append(("BGL_TIMERS", "BlueGene/L high resolution clock."))
        elif self.target_arch is IBM_BGP:
            metrics.append(("BGP_TIMERS", "BlueGene/P high resolution clock."))
        elif self.target_arch is IBM_BGQ:
            metrics.append(("BGQ_TIMERS", "BlueGene/Q high resolution clock."))
        return metrics

    def rewrite(self, rewrite_package, executable, inst_file):
        makefile = self.get_makefile()
        tags = self._makefile_tags(makefile)
        if not self.mpi_support:
            tags.add('serial')
        _, env = self.runtime_config()
        if rewrite_package == 'dyninst':
            rewrite_cmd = 'tau_run'
            dyninstroot = os.path.join(self.install_prefix, self.target_arch.name, 'dyninst-9.3.2-working')
            env['DYNINST_ROOT'] = dyninstroot
            env['DYNINSTAPI_RT_LIB'] = '%s/lib/libdyninstAPI_RT.so' %dyninstroot
            env['LD_LIBRARY_PATH'] = '%s:%s' %(os.path.join(dyninstroot, 'lib') , env['LD_LIBRARY_PATH'])
        elif rewrite_package == 'pebil':
            rewrite_cmd = 'tau_pebil_rewrite'
        elif rewrite_package == 'maqao':
            rewrite_cmd = 'tau_rewrite'
        cmd = [rewrite_cmd, '-T', ','.join(tags), executable, '-o', inst_file]
        retval = util.create_subprocess(cmd, env=env, stdout=True)
        if retval != 0:
            raise ConfigurationError("TAU was unable rewrite the executable.")
        return retval

    def get_python_version(self, python_path):
        _, env = self.runtime_config()
        cmd = [python_path , '--version']
        out = util.get_command_output(cmd)
        p=re.compile('\d+\.\d+\.\d+')
        m = p.search(out)
        return m.group()
