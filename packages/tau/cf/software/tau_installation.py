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

import os
import glob
import shutil
from tau import logger, util
from tau.error import ConfigurationError, InternalError
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import Installation, parallel_make_flags
from tau.cf.compiler import host
from tau.cf.compiler.host import CC, CXX, FC, UPC
from tau.cf.compiler.mpi import MPI_CC, MPI_CXX, MPI_FC
from tau.cf.compiler.shmem import SHMEM_CC, SHMEM_CXX, SHMEM_FC
from tau.cf.platforms import TauMagic, INTEL_KNL, CRAY_CNL, DARWIN


LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://tau.uoregon.edu/tau.tgz'}

NIGHTLY = 'http://fs.paratools.com/tau-nightly.tgz'

COMMANDS = {None:
            ['jumpshot',
             'paraprof',
             'perfdmf_configure',
             'perfdmf_createapp',
             'perfdmf_createexp',
             'perfdmfdb.py',
             'perfdmf_loadtrial',
             'perfexplorer',
             'perfexplorer_configure',
             'phaseconvert',
             'pprof',
             'ppscript',
             'slog2print',
             'tau2slog2',
             'tau_analyze',
             'taucc',
             'tau_cc.sh',
             'tau_compiler.sh',
             'tau-config',
             'tau_convert',
             'taucxx',
             'tau_cxx.sh',
             'taudb_configure',
             'taudb_install_cert',
             'taudb_keygen',
             'taudb_loadtrial',
             'tau_ebs2otf.pl',
             'tau_ebs_process.pl',
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
             'tau_merge',
             'tau_multimerge',
             'tau_pebil_rewrite',
             'tau_reduce',
             'tau_rewrite',
             'tau_selectfile',
             'tau_show_libs',
             'tau_throttle.sh',
             'tau_treemerge.pl',
             'tauupc',
             'tau_upc.sh',
             'tau_user_setup.sh',
             'trace2profile']}

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
                         SHMEM_FC: 'tau_f90.sh'}

TAU_MINIMAL_COMPILERS = [CC, CXX]


class TauInstallation(Installation):
    """Encapsulates a TAU installation.

    TAU is an enormous, organic, complex piece of software so this class is
    unusually complex to consider all the corner cases.  This is where most
    of the systemization of TAU is actually implemented so it can get ugly.
    """
    # Settle down pylint.  This is a big, ugly class and there's not much we can do about it.
    # pylint: disable=too-many-instance-attributes, too-many-arguments, too-many-locals, too-many-statements

    def __init__(self, sources, target_arch, target_os, compilers,
                 # Application support features
                 openmp_support,
                 pthreads_support,
                 tbb_support,
                 mpi_support,
                 mpi_include_path,
                 mpi_library_path,
                 mpi_libraries,
                 cuda_support,
                 cuda_prefix,
                 opencl_support,
                 opencl_prefix,
                 shmem_support,
                 shmem_include_path,
                 shmem_library_path,
                 shmem_libraries,
                 mpc_support,
                 # Instrumentation methods and options
                 source_inst,
                 compiler_inst,
                 link_only,
                 io_inst,
                 keep_inst_files,
                 reuse_inst_files,
                 select_file,
                 # Measurement methods and options
                 profile,
                 trace,
                 sample,
                 metrics,
                 measure_mpi,
                 measure_openmp,
                 measure_opencl,
                 measure_cuda,
                 measure_shmem,
                 measure_heap_usage,
                 measure_memory_alloc,
                 measure_comm_matrix,
                 callpath_depth,
                 throttle,
                 throttle_per_call,
                 throttle_num_calls,
                 forced_makefile):
        """Initialize the TAU installation wrapper class.

        Args:
            sources (dict): Packages sources as strings indexed by package names as strings.  A source may be a
                            path to a directory where the software has already been installed, or a path to a source
                            archive file, or the special keywords 'download' or 'nightly'.
            target_arch (Architecture): Target architecture description.
            target_os (OperatingSystem): Target operating system description.
            compilers (InstalledCompilerSet): Compilers to use if software must be compiled.
            openmp_support (bool): Enable or disable OpenMP support in TAU.
            pthreads_support (bool): Enable or disable pthreads support in TAU.
            tbb_support (bool): Enable or disable tbb support in TAU.
            mpi_support (bool): Enable or disable MPI support in TAU.
            mpi_include_path (list):  Paths to search for MPI header files.
            mpi_library_path (list): Paths to search for MPI library files.
            mpi_libraries (list): MPI libraries to include when linking with TAU.
            cuda_support (bool): Enable or disable CUDA support in TAU.
            opencl_support (bool): Enable or disable OpenCL support in TAU.
            shmem_support (bool): Enable or disable SHMEM support in TAU.
            shmem_include_path (list):  Paths to search for SHMEM header files.
            shmem_library_path (list): Paths to search for SHMEM library files.
            shmem_libraries (list): SHMEM libraries to include when linking with TAU.
            mpc_support (bool): Enable or disable MPC support in TAU.
            source_inst (bool): Enable or disable source-based instrumentation in TAU.
            compiler_inst (bool): Enable or disable compiler-based instrumentation in TAU.
            link_only (bool): True to disable instrumentation and link TAU libraries.
            io_inst (bool): Enable or disable POSIX I/O instrumentation in TAU.
            keep_inst_files (bool): If True then do not remove instrumented source files after compilation.
            reuse_inst_files (bool): If True then reuse instrumented source files for compilation when available.
            select_file (str): Path to selective instrumentation file.
            profile (str): Enable or disable profiling.
            trace (str): Enable or disable tracing.
            sample (bool): Enable or disable event-based sampling.
            metrics (list): Metrics to measure, e.g. ['TIME', 'PAPI_FP_INS']
            measure_mpi (bool): If True then measure time spent in MPI calls.
            measure_openmp (str): String specifying OpenMP measurement method, e.g. 'opari' or 'ompt'
            measure_cuda (bool): If True then measure time spent in CUDA calls.
            measure_shmem (bool): If True then measure time spent in SHMEM calls.
            measure_heap_usage (bool): If True then measure memory usage.
            measure_memory_alloc (bool): If True then record memory allocation and deallocation events.
            measure_comm_matrix (bool): If True then record the point-to-point communication matrix.
            callpath_depth (int): Depth of callpath measurement.  0 to disable.
            throttle (bool): If True then throttle lightweight events.
            throttle_per_call (int): Maximum microseconds per call of a lightweight event.
            throttle_num_calls (int): Minimum number of calls for a lightweight event.
            forced_makefile (str): Path to external makefile if forcing TAU_MAKEFILE or None.
        """
        super(TauInstallation, self).__init__('tau', 'TAU Performance System', sources, target_arch, target_os,
                                              compilers, REPOS, COMMANDS, None, None)
        self._tau_makefile = None
        if self.src == 'nightly':
            self.src = NIGHTLY
        self.tau_magic = TauMagic.find((self.target_arch, self.target_os))
        self.verbose = (logger.LOG_LEVEL == 'DEBUG')
        self.openmp_support = openmp_support
        self.opencl_support = opencl_support
        self.opencl_prefix = opencl_prefix
        self.pthreads_support = pthreads_support
        self.tbb_support = tbb_support
        self.mpi_support = mpi_support
        self.mpi_include_path = mpi_include_path
        self.mpi_library_path = mpi_library_path
        self.mpi_libraries = mpi_libraries
        self.cuda_support = cuda_support
        self.cuda_prefix = cuda_prefix
        self.shmem_support = shmem_support
        self.shmem_include_path = shmem_include_path
        self.shmem_library_path = shmem_library_path
        self.shmem_libraries = shmem_libraries
        self.mpc_support = mpc_support
        self.source_inst = source_inst
        self.compiler_inst = compiler_inst
        self.link_only = link_only
        self.io_inst = io_inst
        self.keep_inst_files = keep_inst_files
        self.reuse_inst_files = reuse_inst_files
        self.select_file = select_file
        self.profile = profile
        self.trace = trace
        self.sample = sample
        self.metrics = metrics
        self.measure_mpi = measure_mpi
        self.measure_openmp = measure_openmp
        self.measure_opencl = measure_opencl
        self.measure_cuda = measure_cuda
        self.measure_shmem = measure_shmem
        self.measure_heap_usage = measure_heap_usage
        self.measure_memory_alloc = measure_memory_alloc
        self.measure_comm_matrix = measure_comm_matrix
        self.callpath_depth = callpath_depth
        self.throttle = throttle
        self.throttle_per_call = throttle_per_call
        self.throttle_num_calls = throttle_num_calls
        self.forced_makefile = forced_makefile
        if forced_makefile is None:
            for pkg in 'binutils', 'libunwind', 'papi', 'pdt':
                uses_pkg = getattr(self, '_uses_'+pkg)
                if uses_pkg():
                    self.add_dependency(pkg, sources)
            if self._uses_scorep():
                self.add_dependency('scorep', sources, mpi_support, shmem_support,
                                    self._uses_binutils(), self._uses_libunwind(), self._uses_papi(), self._uses_pdt())
        else:
            for pkg in 'binutils', 'libunwind', 'papi', 'pdt':
                if sources[pkg]:
                    self.add_dependency(pkg, sources)
            if sources['scorep']:
                self.add_dependency('scorep', sources, mpi_support, shmem_support,
                                    sources['binutils'], sources['libunwind'], sources['papi'], sources['pdt'])

    def _calculate_uid(self):
        uid_parts = [self.src, self.target_arch.name, self.target_os.name]
        # TAU changes if any compiler changes.
        uid_parts.extend(sorted(comp.uid for comp in self.compilers.itervalues()))
        return util.calculate_uid(uid_parts)

    def _set_install_prefix(self, value):
        # TAU puts installation files (bin, lib, etc.) in a magically named subfolder
        super(TauInstallation, self)._set_install_prefix(value)
        arch_path = os.path.join(self.install_prefix, self.tau_magic.name)
        self.bin_path = os.path.join(arch_path, 'bin')
        self.lib_path = os.path.join(arch_path, 'lib')

    def _uses_pdt(self):
        # TAU uses PDT to generate the SHMEM wrapper libraries, so PDT is required for SHMEM support
        return self.source_inst == 'automatic' or self.shmem_support

    def _uses_binutils(self):
        return self.sample or self.compiler_inst != 'never' or self.measure_openmp in ('ompt', 'gomp')

    def _uses_libunwind(self):
        return (self.target_os is not DARWIN and
                (self.sample or self.compiler_inst != 'never' or self.openmp_support))

    def _uses_papi(self):
        return bool(len([met for met in self.metrics if 'PAPI' in met]))

    def _uses_scorep(self):
        return self.profile == 'cubex' or self.trace == 'otf2'

    def _prepare_src(self, reuse_archive=True):
        if self.src == NIGHTLY:
            reuse_archive = False
        return super(TauInstallation, self)._prepare_src(reuse_archive)

    def verify(self):
        super(TauInstallation, self).verify()

        # Check for TAU libraries
        tau_makefile = self.get_makefile()
        makefile_tags = os.path.basename(tau_makefile).replace("Makefile.tau", "")
        static_lib = "libtau%s.*" % makefile_tags
        shared_lib = "libTAUsh%s.*" % makefile_tags
        for pattern in static_lib, shared_lib:
            if glob.glob(os.path.join(self.lib_path, pattern)):
                break
        else:
            raise SoftwarePackageError("TAU libraries for makefile '%s' not found" % tau_makefile)

        # Open TAU makefile and check BFDINCLUDE, UNWIND_INC, PAPIDIR, etc.
        with open(tau_makefile, 'r') as fin:
            for line in fin:
                if self._uses_binutils() and 'BFDINCLUDE=' in line:
                    binutils = self.dependencies['binutils']
                    bfd_inc = line.split('=')[1].strip().strip("-I")
                    if binutils.include_path != bfd_inc:
                        LOGGER.debug("BFDINCLUDE='%s' != '%s'", bfd_inc, binutils.include_path)
                        raise SoftwarePackageError("BFDINCLUDE in '%s' is invalid" % tau_makefile)
                if self._uses_libunwind() and 'UNWIND_INC=' in line:
                    libunwind = self.dependencies['libunwind']
                    libunwind_inc = line.split('=')[1].strip().strip("-I")
                    if libunwind.include_path != libunwind_inc:
                        LOGGER.debug("UNWIND_INC='%s' != '%s'", libunwind_inc, libunwind.include_path)
                        raise SoftwarePackageError("UNWIND_INC in '%s' is invalid" % tau_makefile)
                if self._uses_papi() and 'PAPIDIR=' in line:
                    papi = self.dependencies['papi']
                    papi_dir = line.split('=')[1].strip()
                    if papi.install_prefix != papi_dir:
                        LOGGER.debug("PAPI_DIR='%s' != '%s'", papi_dir, papi.install_prefix)
                        raise SoftwarePackageError("PAPI_DIR in '%s' is invalid" % tau_makefile)
                if self._uses_scorep() and 'SCOREPDIR=' in line:
                    scorep = self.dependencies['scorep']
                    scorep_dir = line.split('=')[1].strip()
                    if scorep.install_prefix != scorep_dir:
                        LOGGER.debug("SCOREPDIR='%s' != '%s'", scorep_dir, scorep.install_prefix)
                        raise SoftwarePackageError("SCOREPDIR in '%s' is invalid" % tau_makefile)

        # Check for iowrapper libraries and link options
        if self.io_inst:
            # Replace right-most occurance of 'Makefile.tau' with 'shared'
            tagged_shared_dir = 'shared'.join(self.get_makefile().rsplit('Makefile.tau', 1))
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
        LOGGER.debug("TAU installation at '%s' is valid", self.install_prefix)

    def _select_flags(self, header, libglobs, user_inc, user_lib, user_libraries, wrap_cc, wrap_cxx, wrap_fc):
        def unique(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]
        selected_inc, selected_lib, selected_library = None, None, None
        # Prefer user-specified paths over autodetected paths
        include_path = unique(user_inc + wrap_cc.include_path + wrap_cxx.include_path + wrap_fc.include_path)
        if include_path:
            # Unfortunately, TAU's configure script can only accept one path on -mpiinc
            # and it expects the compiler's include path argument (e.g. "-I") to be omitted
            for path in include_path:
                if os.path.exists(os.path.join(path, header)):
                    selected_inc = path
                    break
            else:
                raise ConfigurationError("%s not found on include path: %s" %
                                         (header, os.pathsep.join(include_path)))
        library_path = unique(user_lib + wrap_cc.library_path + wrap_cxx.library_path + wrap_fc.library_path)
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
            fc_magic_map = {host.GNU: 'gfortran',
                            host.INTEL: 'intel',
                            host.PGI: 'pgi',
                            host.CRAY: 'cray',
                            host.IBM: 'ibm',
                            host.IBM_BG: 'ibm'}
            try:
                fortran_magic = fc_magic_map[fc_family]
            except KeyError:
                LOGGER.warning("Can't determine TAU magic word for %s %s", fc_comp.info.short_descr, fc_comp)
                raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)

        # Set up MPI paths and libraries
        mpiinc, mpilib, mpilibrary = None, None, None
        if self.mpi_support:
            mpiinc, mpilib, mpilibrary = \
                self._select_flags('mpi.h', ('libmpi*',),
                                   self.mpi_include_path,
                                   self.mpi_library_path,
                                   self.mpi_libraries,
                                   self.compilers[MPI_CC],
                                   self.compilers[MPI_CXX],
                                   self.compilers[MPI_FC])

        # Set up SHMEM paths and libraries
        shmeminc, shmemlib, shmemlibrary = None, None, None
        if self.shmem_support:
            shmeminc, shmemlib, shmemlibrary = \
                self._select_flags('shmem.h', ('lib*shmem*', 'lib*sma*'),
                                   self.shmem_include_path,
                                   self.shmem_library_path,
                                   self.shmem_libraries,
                                   self.compilers[SHMEM_CC],
                                   self.compilers[SHMEM_CXX],
                                   self.compilers[SHMEM_FC])
            # FIXME: A hack to for OpenSHMEM? 
            if self.tau_magic.name == 'x86_64':
                cc_command = self.compilers[SHMEM_CC].command
                cxx_command = self.compilers[SHMEM_CXX].command
                fortran_magic = 'oshfort'

        binutils = self.dependencies.get('binutils')
        libunwind = self.dependencies.get('libunwind')
        papi = self.dependencies.get('papi')
        pdt = self.dependencies.get('pdt')
        scorep = self.dependencies.get('scorep')

        flags = [flag for flag in
                 ['-arch=%s' % self.tau_magic.name,
                  '-cc=%s' % cc_command,
                  '-c++=%s' % cxx_command,
                  '-fortran=%s' % fortran_magic if fortran_magic else None,
                  '-bfd=%s' % binutils.install_prefix if binutils else None,
                  '-papi=%s' % papi.install_prefix if papi else None,
                  '-unwind=%s' % libunwind.install_prefix if libunwind else None,
                  '-scorep=%s' % scorep.install_prefix if scorep else None,
                  '-pthread' if self.pthreads_support else None,
                  '-tbb' if self.tbb_support else None,
                  '-mpi' if self.mpi_support else None,
                  '-mpiinc=%s' % mpiinc if mpiinc else None,
                  '-mpilib=%s' % mpilib if mpilib else None,
                  '-mpilibrary=%s' % mpilibrary if mpilibrary else None,
                  '-cuda=%s' % self.cuda_prefix if self.cuda_prefix else None,
                  '-opencl=%s' % self.opencl_prefix if self.opencl_prefix else None,
                  '-shmem' if self.shmem_support else None,
                  '-shmeminc=%s' % shmeminc if shmeminc else None,
                  '-shmemlib=%s' % shmemlib if shmemlib else None,
                  '-shmemlibrary=%s' % shmemlibrary if shmemlibrary else None,
                 ] if flag]
        useropts = ['-O2', '-g']
        if self.target_arch is INTEL_KNL:
            useropts.append('-DTAU_MAX_THREADS=512')
        flags.append('-useropt="%s"' % '#'.join(useropts))
        if pdt:
            flags.append('-pdt=%s' % pdt.install_prefix)
            flags.append('-pdt_c++=%s' % pdt.compilers[CXX].info.command)
        if self.openmp_support:
            flags.append('-openmp')
            if self.measure_openmp == 'ompt':
                flags.append('-ompt=download')
            elif self.measure_openmp == 'opari':
                flags.append('-opari')
        if self.io_inst:
            flags.append('-iowrapper')
        cmd = ['./configure'] + flags
        LOGGER.info("Configuring TAU...")
        if util.create_subprocess(cmd, cwd=self.src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('TAU configure failed')

    def make_install(self):
        """Installs TAU to ``self.install_prefix``.

        Executes 'make install' to build and install TAU.

        Raises:
            SoftwarePackageError: 'make install' failed.
        """
        cmd = ['make', 'install'] + parallel_make_flags()
        LOGGER.info('Compiling and installing TAU...')
        if util.create_subprocess(cmd, cwd=self.src_prefix, stdout=False, show_progress=True):
            raise SoftwarePackageError('TAU compilation/installation failed')

    def install(self, force_reinstall=False):
        """Installs TAU.

        Configures, compiles, and installs TAU with all necessarry makefiles and libraries.

        Args:
            force_reinstall (bool): Set to True to force reinstall even if TAU is already installed and working.

        Raises:
            SoftwarePackageError: TAU failed installation or did not pass verification after it was installed.
        """
        if self.forced_makefile:
            forced_install_prefix = os.path.abspath(os.path.join(os.path.dirname(self.forced_makefile), '..', '..'))
            self._set_install_prefix(forced_install_prefix)
            for pkg in self.dependencies.itervalues():
                pkg.install(force_reinstall=False)
            LOGGER.warning("TAU makefile was forced! Not verifying TAU installation")
            return 
        if not self.src or not force_reinstall:
            for pkg in self.dependencies.itervalues():
                pkg.install(force_reinstall)
            try:
                return self.verify()
            except SoftwarePackageError as err:
                if not self.src:
                    raise SoftwarePackageError("%s source package is unavailable and the installation at '%s' "
                                               "is invalid: %s" % (self.title, self.install_prefix, err),
                                               "Specify source code path or URL to enable package reinstallation.")
                elif not force_reinstall:
                    LOGGER.debug(err)
        LOGGER.info("Installing %s at '%s'", self.title, self.install_prefix)
        try:
            # Keep reconfiguring the same source because that's how TAU works
            if not (self.include_path and os.path.isdir(self.include_path)):
                shutil.move(self._prepare_src(), self.install_prefix)
            self.src_prefix = self.install_prefix
            self.configure()
            self.make_install()
        except Exception as err:
            LOGGER.info("%s installation failed: %s ", self.title, err)
            raise
        # Verify the new installation
        LOGGER.info("Verifying %s installation...", self.title)
        return self.verify()

    def get_tags(self):
        """Get tags for this TAU installation.

        Each TAU configuration (makefile, library, Python bindings, etc.) is identified by its tags.
        Tags can appear in the makefile name in any order so the order of the tags returned by this
        function will likely not match the order they appear in the makefile name or tau_exec command line.

        Returns:
            list: Makefile tags, e.g. ['papi', 'pdt', 'icpc']
        """
        tags = []
        cxx_compiler = self.compilers[CXX].unwrap()
        compiler_tags = {host.INTEL: 'intel' if self.target_os == CRAY_CNL else 'icpc',
                         host.PGI: 'pgi'}
        try:
            tags.append(compiler_tags[cxx_compiler.info.family])
        except KeyError:
            pass
        if self._uses_pdt():
            tags.append('pdt')
        if self._uses_papi():
            tags.append('papi')
        if self._uses_scorep():
            tags.append('scorep')
        if self.openmp_support:
            tags.append('openmp')
            openmp_tags = {'ompt': 'ompt', 'opari': 'opari'}
            try:
                tags.append(openmp_tags[self.measure_openmp])
            except KeyError:
                pass
        if self.pthreads_support:
            tags.append('pthread')
        if self.tbb_support:
            tags.append('tbb')
        if self.mpi_support:
            tags.append('mpi')
        if self.cuda_support:
            tags.append('cupti')
        if self.shmem_support:
            tags.append('shmem')
        if self.mpc_support:
            tags.append('mpc')
        LOGGER.debug("TAU tags: %s", tags)
        return set(tags)

    def _incompatible_tags(self):
        """Returns a set of makefile tags incompatible with the specified config."""
        tags = []
        cxx_compiler = self.compilers[CXX].unwrap()
        compiler_tags = {host.INTEL: 'intel' if self.target_os == CRAY_CNL else 'icpc',
                         host.PGI: 'pgi'}
        compiler_tag = compiler_tags.get(cxx_compiler.info.family, None)
        tags.extend(tag for tag in compiler_tags.itervalues() if tag != compiler_tag)
        if not self.mpi_support:
            tags.append('mpi')
        if self.measure_openmp != 'opari':
            tags.append('opari')
        if not self.openmp_support:
            tags.append('openmp')
        if not self._uses_scorep():
            tags.append('scorep')
        if not self.shmem_support:
            tags.append('shmem')
        LOGGER.debug("Incompatible tags: %s", tags)
        return set(tags)

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
        tau_makefiles = glob.glob(os.path.join(self.lib_path, 'Makefile.tau*'))
        LOGGER.debug("Found makefiles: '%s'", tau_makefiles)
        config_tags = self.get_tags()
        LOGGER.debug("Searching for makefile with tags: %s", config_tags)
        approx_tags = None
        approx_makefile = None
        dangerous_tags = self._incompatible_tags()
        LOGGER.debug("Will not use makefiles containing tags: %s", dangerous_tags)
        for makefile in tau_makefiles:
            tags = set(os.path.basename(makefile).split('.')[1].split('-')[1:])
            LOGGER.debug("%s has tags: %s", makefile, tags)
            if config_tags <= tags:
                LOGGER.debug("%s contains desired tags: %s", makefile, config_tags)
                if tags <= config_tags:
                    makefile = os.path.join(self.lib_path, makefile)
                    LOGGER.debug("Found TAU makefile %s", makefile)
                    self._tau_makefile = makefile
                    return makefile
                elif not tags & dangerous_tags:
                    if not approx_tags or tags < approx_tags:
                        approx_makefile = makefile
                        approx_tags = tags
                    LOGGER.debug("Best approximate match is: %s", approx_tags)
        LOGGER.debug("No TAU makefile exactly matches tags '%s'", config_tags)
        if approx_makefile:
            makefile = os.path.join(self.lib_path, approx_makefile)
            LOGGER.debug("Found approximate match with TAU makefile %s", makefile)
            self._tau_makefile = makefile
            return makefile
        LOGGER.debug("No TAU makefile approximately matches tags '%s'", config_tags)
        raise SoftwarePackageError("TAU Makefile not found for tags '%s' in '%s'" %
                                   (', '.join(config_tags), self.install_prefix))

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

    def compiletime_config(self, opts=None, env=None):
        """Configures environment for compilation with TAU.

        Modifies incoming command line arguments and environment variables
        for the TAU compiler wrapper scripts.

        Args:
            opts (list): Command line options.
            env (dict): Environment variables.

        Returns:
            tuple: (opts, env) updated to support TAU.
        """
        opts, env = super(TauInstallation, self).compiletime_config(opts, env)
        env = self._sanitize_environment(env)
        for pkg in self.dependencies.itervalues():
            opts, env = pkg.compiletime_config(opts, env)
        try:
            tau_opts = set(env['TAU_OPTIONS'].split(' '))
        except KeyError:
            tau_opts = set()
        if self.source_inst == 'never' and self.compiler_inst == 'never':
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
        if self.link_only:
            tau_opts.add('-optLinkOnly')
        if self.keep_inst_files:
            tau_opts.add('-optKeepFiles')
        if self.reuse_inst_files:
            tau_opts.add('-optReuseFiles')
        if self.select_file:
            select_file = os.path.realpath(os.path.abspath(self.select_file))
            tau_opts.add('-optTauSelectFile=%s' % select_file)
        if self.io_inst:
            tau_opts.add('-optTrackIO')
        if self.measure_memory_alloc:
            tau_opts.add('-optMemDbg')
        if self.openmp_support and self.source_inst != 'never':
            tau_opts.add('-optContinueBeforeOMP')
        try:
            tau_opts.update(self.force_tau_options)
        except AttributeError:
            pass
        if self.sample or self.compiler_inst != 'never':
            opts.append('-g')
        env['TAU_MAKEFILE'] = self.get_makefile()
        env['TAU_OPTIONS'] = ' '.join(tau_opts)
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
        if self.trace == 'slog2':
            env['TAU_TRACE'] = '1'
        elif self.trace == 'otf2':
            env['TAU_TRACE'] = '1'
            env['SCOREP_ENABLE_TRACING'] = '1'
        else:
            env['TAU_TRACE'] = '0'
        env['TAU_SAMPLING'] = str(int(self.sample))
        env['TAU_TRACK_HEAP'] = str(int(self.measure_heap_usage))
        env['TAU_COMM_MATRIX'] = str(int(self.measure_comm_matrix))
        env['TAU_METRICS'] = ",".join(self.metrics) + ","
        env['TAU_THROTTLE'] = str(int(self.throttle))
        if self.throttle:
            env['TAU_THROTTLE_PERCALL'] = str(int(self.throttle_per_call))
            env['TAU_THROTTLE_NUMCALLS'] = str(int(self.throttle_num_calls))
        if self.callpath_depth > 0:
            env['TAU_CALLPATH'] = '1'
            env['TAU_CALLPATH_DEPTH'] = str(self.callpath_depth)
        if self.verbose:
            opts.append('-v')
        if self.sample:
            opts.append('-ebs')
        if self.measure_cuda:
            opts.append('-cupti')
        if self.measure_opencl:
            opts.append('-opencl')
        if self.io_inst:
            opts.append('-io')
        if self.measure_memory_alloc:
            env['TAU_SHOW_MEMORY_FUNCTIONS'] = '1'
        if self.measure_shmem:
            opts.append('-shmem')
        return list(set(opts)), env

    def get_compiler_command(self, compiler):
        """Get the compiler wrapper command for the given compiler.

        Args:
            compiler (InstalledCompiler): A compiler to find a wrapper for.

        Returns:
            str: Command for TAU compiler wrapper without path or arguments.
        """
        use_wrapper = (self.source_inst != 'never' or
                       self.compiler_inst != 'never' or
                       self.target_os is CRAY_CNL)
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
            compiler (Compiler): A compiler command.
            compiler_args (list): Compiler command line arguments.

        Raises:
            ConfigurationError: Compilation failed.

        Returns:
            int: Compiler return value (always 0 if no exception raised).
        """
        opts, env = self.compiletime_config()
        compiler_cmd = self.get_compiler_command(compiler)
        cmd = [compiler_cmd] + opts + compiler_args
        tau_env_opts = sorted('%s=%s' % item for item in env.iteritems() if item[0].startswith('TAU_'))
        LOGGER.info('\n'.join(tau_env_opts))
        LOGGER.info(' '.join(cmd))
        retval = util.create_subprocess(cmd, env=env, stdout=True)
        if retval != 0:
            raise ConfigurationError("TAU was unable to build the application.",
                                     "Check that the application builds with its normal compilers, i.e. without TAU."
                                     "Use tau --log and see detailed output at the end of '%s'" % logger.LOG_FILE)
        return retval

    def get_application_command(self, launcher_cmd, application_cmd):
        """Build a command line to launch an application under TAU.

        Sometimes TAU needs to use tau_exec, sometimes not.  This routine
        also handles backend launch commands like `aprun`.

        Args
            launcher_cmd (list): Application launcher with command line arguments, e.g. ['mpirun', '-np', '4'].
            application_cmd (list): Application command with command line arguments, e.g. ['./a.out', '-g', 'hello'].

        Returns:
            tuple: (cmd, env) where `cmd` is the new command line and `env` is a dictionary of environment
                   variables to set before running the application command.
        """
        opts, env = self.runtime_config()
        use_tau_exec = (self.measure_opencl or
                        self.tbb_support or
                        self.pthreads_support or
                        self.target_os is not CRAY_CNL or
                        (self.source_inst == 'never' and
                         self.compiler_inst == 'never' and
                         not self.link_only))
        if use_tau_exec:
            tau_exec_opts = opts
            tags = self.get_tags()
            if not self.mpi_support:
                tags.add('serial')
            if self.opencl_support:
                tags.add('cupti')
            tau_exec = ['tau_exec', '-T', ','.join(tags)] + tau_exec_opts
            cmd = launcher_cmd + tau_exec + application_cmd
        else:
            cmd = launcher_cmd + application_cmd
        return cmd, env

    def show_profile(self, path, tool_name=None):
        """Shows profile data in the specified file or folder.

        Args:
            path (str): Path to the directory containing profile files or MULTI__ directories.
            tool_name (str): Name of the profile visualization tool to use, e.g. 'pprof'.

        Returns:
            int: Return code of the visualization tool.
        """
        LOGGER.debug("Showing profile files at '%s'", path)
        _, env = self.runtime_config()
        tools = (tool_name,) if tool_name else ('paraprof', 'pprof')
        for tool in (os.path.join(self.bin_path, x) for x in tools):
            if not os.path.isdir(path):
                cmd = [tool, path]
            else:
                profiles = 'tauprofile.xml', 'profile.cubex'
                for profile in (os.path.join(path, x) for x in profiles):
                    if os.path.isfile(profile):
                        cmd = [tool, profile]
                        break
                else:
                    cmd = [tool]
            if util.create_subprocess(cmd, cwd=path, env=env) == 0:
                break
            LOGGER.warning("%s failed", tool)
        else:
            raise ConfigurationError("All visualization or reporting tools failed to open '%s'" % path,
                                     "Check Java installation, X11 installation,"
                                     " network connectivity, and file permissions")

    def show_trace(self, path, tool_name=None):
        """Shows trace data in the specified file or folder.

        Merges the traces and converts them if needed.

        Args:
            path (str): Path to the directory containing trace files.
            tool_name (str): Name of the profile visualization tool to use, e.g. 'vampir'.

        Returns:
            int: Return code of the visualization tool.
        """
        LOGGER.debug("Showing trace files at '%s'", path)
        _, env = self.runtime_config()
        if self.trace == 'otf2' and tool_name is None:
            tool_name = 'vampir'
            LOGGER.info('otf2 requires vampir')
        if tool_name is None:
            tool_name = 'jumpshot'
        if tool_name == 'jumpshot':
            if not os.path.isdir(path):
                raise InternalError("Individual trace files not yet supported.")
            tau_slog2 = os.path.join(path, 'tau.slog2')
            if not os.path.isfile(tau_slog2):
                if not os.path.isfile(os.path.join(path, 'tau.trc')):
                    trc_files = glob.glob(os.path.join(path, '*.trc'))
                    edf_files = glob.glob(os.path.join(path, '*.edf'))
                    if not (trc_files and edf_files):
                        raise ConfigurationError("No *.trc or *.edf files!")
                    cmd = ['tau_treemerge.pl']
                    retval = util.create_subprocess(cmd, cwd=path, env=env, log=False)
                    if retval != 0:
                        raise InternalError("Nonzero return code from tau_treemerge.pl")
                cmd = ['tau2slog2', 'tau.trc', 'tau.edf', '-o', 'tau.slog2']
                retval = util.create_subprocess(cmd, cwd=path, env=env, log=False)
                if retval != 0:
                    raise InternalError("Nonzero return code from %s" % ' '.join(cmd))
            LOGGER.info("Opening %s in %s", tau_slog2, tool_name)
            cmd = [tool_name, tau_slog2]
            retval = util.create_subprocess(cmd, cwd=path, env=env, log=False)
        elif tool_name == 'vampir' or tool_name == 'vampirserver':
            import resource
            tau_otf2 = os.path.join(path, 'traces.otf2')
            if not os.path.isfile(tau_otf2):
                raise ConfigurationError("otf2 trace files not found.")
            evt_files = glob.glob(os.path.join(path, 'traces/*.evt'))
            def_files = glob.glob(os.path.join(path, 'traces/*.def'))
            if len(evt_files) + len(def_files) > resource.getrlimit(resource.RLIMIT_NOFILE)[0]:
                raise ConfigurationError("Too many trace files, use Vampir server to view.")
            if not util.which('vampir'):
                raise ConfigurationError("Vampir not found in PATH. Contact ParaTools for more information on Vampir.")
            LOGGER.info("Opening %s in %s", tau_otf2, tool_name)
            cmd = [tool_name, tau_otf2]
            retval = util.create_subprocess(cmd, cwd=path, env=env, log=False)
        else:
            raise InternalError("Only vampir and jumpshot supported at this time")
        if retval == 0:
            return
        else:
            raise ConfigurationError("Trace visualizer failed to open '%s'" % path,
                                     "Check Java installation, X11 installation,"
                                     " network connectivity, and file permissions")

    def pack_profiles(self, prefix, ppk_file):
        """Create a PPK file from profile.* files.

        Args:
            prefix (str): Path to the directory containing profile.* files.
            ppk_file (str): Absolute path to the PPK file that will be created.

        Raises:
            ConfigurationError: paraprof failed to pack the profiles.
        """
        _, env = self.runtime_config()
        cmd = ['paraprof', '--pack', ppk_file]
        retval = util.create_subprocess(cmd, cwd=prefix, env=env)
        if retval:
            raise ConfigurationError("ParaProf command '%s' failed in '%s'" % (' '.join(cmd), prefix),
                                     "Make sure Java is installed and working",
                                     "Install the most recent Java from http://java.com")

    def check_metrics(self):
        """Checks metrics for compatibility.

        Raises:
            ConfigurationError if there are incompatible metrics.
        """
        if not self._uses_papi():
            return
        papi_metrics = [metric.replace('PAPI_NATIVE:', '') for metric in self.metrics if metric.startswith("PAPI")]
        if papi_metrics:
            event_chooser_cmd = os.path.join(self.dependencies['papi'].bin_path, 'papi_event_chooser')
            cmd = [event_chooser_cmd, 'PRESET'] + papi_metrics
            if util.create_subprocess(cmd, stdout=False, show_progress=False):
                raise ConfigurationError("PAPI metrics [%s] are not compatible on this target." %
                                         ', '.join(papi_metrics),
                                         "Use papi_avail to check metric availability.",
                                         "Spread the desired metrics over multiple measurements.",
                                         "Choose fewer metrics.")
