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
from tau import logger, util
from tau.error import ConfigurationError, InternalError
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import Installation, parallel_make_flags
from tau.cf.software.pdt_installation import PdtInstallation
from tau.cf.software.binutils_installation import BinutilsInstallation
from tau.cf.software.libunwind_installation import LibunwindInstallation
from tau.cf.software.papi_installation import PapiInstallation
from tau.cf.compiler import SYSTEM_COMPILERS, GNU_COMPILERS, INTEL_COMPILERS, PGI_COMPILERS
from tau.cf.compiler import CC_ROLE, CXX_ROLE, FC_ROLE, UPC_ROLE
from tau.cf.compiler.mpi import SYSTEM_MPI_COMPILERS, INTEL_MPI_COMPILERS
from tau.cf.compiler.mpi import MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE
from tau.cf.target import TauArch


LOGGER = logger.get_logger(__name__)

SOURCES = {None: 'http://tau.uoregon.edu/tau.tgz'}

COMMANDS = [
    'jumpshot',
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
    'trace2profile']


TAU_COMPILER_WRAPPERS = {CC_ROLE: 'tau_cc.sh',
                         CXX_ROLE: 'tau_cxx.sh',
                         FC_ROLE: 'tau_f90.sh',
                         UPC_ROLE: 'tau_upc.sh',
                         MPI_CC_ROLE: 'tau_cc.sh',
                         MPI_CXX_ROLE: 'tau_cxx.sh',
                         MPI_FC_ROLE: 'tau_f90.sh'}


class TauInstallation(Installation):
    """Encapsulates a TAU installation.
    
    TAU is an enormous, organic, complex piece of software so this class is 
    unusually complex to consider all the corner cases.  This is where most
    of the systemization of TAU is actually implemented so it can get ugly.
    """

    def __init__(self, prefix, src, host_arch, host_os, compilers, 
                 verbose,
                 # Source for dependencies
                 pdt_source,
                 binutils_source,
                 libunwind_source,
                 papi_source,
                 # Application support features
                 openmp_support,
                 pthreads_support, 
                 mpi_support,
                 mpi_include_path,
                 mpi_library_path,
                 mpi_libraries,
                 cuda_support,
                 shmem_support,
                 mpc_support,
                 # Instrumentation methods and options
                 source_inst,
                 compiler_inst,
                 link_only,
                 io_inst,
                 keep_inst_files,
                 reuse_inst_files,
                 # Measurement methods and options
                 profile,
                 trace,
                 sample,
                 metrics,
                 measure_mpi,
                 measure_openmp,
                 measure_pthreads,
                 measure_cuda,
                 measure_shmem,
                 measure_mpc,
                 measure_memory_usage,
                 measure_memory_alloc,
                 callpath_depth):
        """Initialize the TAU installation wrapper class.
        
        Args:
            prefix (str): Path to a directory to contain subdirectories for 
                          installation files, source file, and compilation files.
            src (str): Path to a directory where the software has already been 
                       installed, or a path to a source archive file, or the special
                       keyword 'download'.
            host_arch (Architecture): Target architecture description.
            host_os (OperatingSystem): Target operating system description.
            compilers (InstalledCompilerSet): Compilers to use if software must be compiled.
            verbose (bool): True to enable TAU verbose output.
            pdt_source (str): Path to PDT source, installation, or None.
            binutils_source (str): Path to GNU binutils source, installation, or None.
            libunwind_source (str): Path to libunwind source, installation, or None.
            papi_source (str): Path to PAPI source, installation, or None.
            openmp_support (bool): Enable or disable OpenMP support in TAU.
            pthreads_support (bool): Enable or disable pthreads support in TAU.
            mpi_support (bool): Enable or disable MPI support in TAU.
            mpi_include_path (list):  Paths to search for MPI header files. 
            mpi_library_path (list): Paths to search for MPI library files.
            mpi_libraries (list): MPI libraries to include when linking with TAU.
            cuda_support (bool): Enable or disable CUDA support in TAU.
            shmem_support (bool): Enable or disable SHMEM support in TAU.
            mpc_support (bool): Enable or disable MPC support in TAU.
            source_inst (bool): Enable or disable source-based instrumentation in TAU.
            compiler_inst (bool): Enable or disable compiler-based instrumentation in TAU. 
            link_only (bool): True to disable instrumentation and link TAU libraries.
            io_inst (bool): Enable or disable POSIX I/O instrumentation in TAU.
            keep_inst_files (bool): If True then do not remove instrumented source files after compilation.
            reuse_inst_files (bool): If True then reuse instrumented source files for compilation when available.
            profile (bool): Enable or disable profiling.
            trace (bool): Enable or disable tracing.
            sample (bool): Enable or disable event-based sampling.
            metrics (list): Metrics to measure, e.g. ['TIME', 'PAPI_FP_INS']
            measure_mpi (bool): If True then measure time spent in MPI calls. 
            measure_openmp (bool): If True then measure time spent in OpenMP directives.
            measure_pthreads (bool): If True then measure time spent in pthread calls.
            measure_cuda (bool): If True then measure time spent in CUDA calls.
            measure_shmem (bool): If True then measure time spent in SHMEM calls.
            measure_mpc (bool): If True then measure time spent in MPC calls.
            measure_memory_usage (bool): If True then measure memory usage.
            measure_memory_alloc (bool): If True then record memory allocation **and deallocation** events.
            callpath_depth (int): Depth of callpath measurement.  0 to disable.
        """
        self.pdt = None
        self.binutils = None
        self.libunwind = None
        self.papi = None
        try:
            arch = TauArch.get(host_arch, host_os).name
        except KeyError:
            raise InternalError("Invalid host_arch '%s' or host_os '%s'" % (host_arch, host_os))
        super(TauInstallation, self).__init__('TAU', prefix, src, '', arch, compilers, SOURCES)
        self.arch_path = os.path.join(self.install_prefix, str(arch))
        self.bin_path = os.path.join(self.arch_path, 'bin')
        self.lib_path = os.path.join(self.arch_path, 'lib')
        self.verbose = verbose
        self.pdt_source = pdt_source
        self.binutils_source = binutils_source
        self.libunwind_source = libunwind_source
        self.papi_source = papi_source
        self.openmp_support = openmp_support
        self.pthreads_support = pthreads_support 
        self.mpi_support = mpi_support
        self.mpi_include_path = mpi_include_path
        self.mpi_library_path = mpi_library_path
        self.mpi_libraries = mpi_libraries
        self.cuda_support = cuda_support
        self.shmem_support = shmem_support
        self.mpc_support = mpc_support
        self.source_inst = source_inst
        self.compiler_inst = compiler_inst
        self.link_only = link_only
        self.io_inst = io_inst
        self.keep_inst_files = keep_inst_files
        self.reuse_inst_files = reuse_inst_files
        self.profile = profile
        self.trace = trace
        self.sample = sample
        self.metrics = metrics
        self.measure_mpi = measure_mpi
        self.measure_openmp = measure_openmp
        self.measure_pthreads = measure_pthreads
        self.measure_cuda = measure_cuda
        self.measure_shmem = measure_shmem
        self.measure_mpc = measure_mpc
        self.measure_memory_usage = measure_memory_usage
        self.measure_memory_alloc = measure_memory_alloc
        self.callpath_depth = callpath_depth
        for pkg in ['pdt', 'binutils', 'libunwind', 'papi']:
            # We save a lot of typing here by using eval.
            # pylint: disable=eval-used
            if eval('self.uses_%s()' % pkg):
                if not getattr(self, '%s_source' % pkg): 
                    raise ConfigurationError("Specified TAU configuration requires %s but no source specified" % pkg)
            else:
                setattr(self, pkg, None)
        
    def uses_pdt(self):
        return self.source_inst != 'never'
    
    def uses_binutils(self):
        return (self.sample or 
                self.compiler_inst != 'never' or 
                self.measure_openmp == 'ompt' or
                self.measure_openmp == 'gomp')
        
    def uses_libunwind(self):
        return (self.arch != 'apple' and
                (self.sample or 
                 self.compiler_inst != 'never' or 
                 self.openmp_support))
        
    def uses_papi(self):
        return bool(len([met for met in self.metrics if 'PAPI' in met]))

    def _check_dependencies(self):
        """Ensures all required dependencies are installed and working.
        
        Kicks off dependency installation if a required dependency is not found.
        """
        if self.uses_pdt():
            self.pdt = PdtInstallation(self.prefix, self.pdt_source, self.arch, self.compilers)
            with self.pdt:
                self.pdt.install()
        if self.uses_binutils():
            self.binutils = BinutilsInstallation(self.prefix, self.binutils_source, self.arch, self.compilers)
            with self.binutils:
                self.binutils.install()
        if self.uses_libunwind():
            self.libunwind = LibunwindInstallation(self.prefix, self.libunwind_source, self.arch, self.compilers)
            with self.libunwind:
                self.libunwind.install()
        if self.uses_papi():
            self.papi = PapiInstallation(self.prefix, self.papi_source, self.arch, self.compilers)
            with self.papi:
                self.papi.install()
    
    def _verify(self, commands=None, libraries=None):
        """Returns true if the installation is valid.
        
        A working TAU installation has a directory named `arch` 
        containing `bin` and `lib` directories and provides all expected
        libraries and commands.
        
        Returns:
            True: If the installation at `install_prefix` is working.
        
        Raises:
          SoftwarePackageError: Describes why the installation is invalid.
        """
        super(TauInstallation, self)._verify(commands=COMMANDS)

        # Open TAU makefile and check BFDINCLUDE, UNWIND_INC, PAPIDIR, etc.
        makefile = self.get_makefile()
        with open(makefile, 'r') as fin:
            for line in fin:
                if self.binutils and ('BFDINCLUDE=' in line):
                    bfd_inc = line.split('=')[1].strip().strip("-I")
                    if self.binutils.include_path != bfd_inc:
                        LOGGER.debug("BFDINCLUDE='%s' != '%s'", bfd_inc, self.binutils.include_path)
                        raise SoftwarePackageError("BFDINCLUDE in TAU Makefile "
                                                   "doesn't match target BFD installation")
                if self.libunwind and ('UNWIND_INC=' in line):
                    libunwind_inc = line.split('=')[1].strip().strip("-I")
                    if self.libunwind.include_path != libunwind_inc:
                        LOGGER.debug("UNWIND_INC='%s' != '%s'", libunwind_inc, self.libunwind.include_path)
                        raise SoftwarePackageError("UNWIND_INC in TAU Makefile "
                                                   "doesn't match target libunwind installation")
                if self.papi and ('PAPIDIR=' in line):
                    papi_dir = line.split('=')[1].strip()
                    if self.papi.install_prefix != papi_dir:
                        LOGGER.debug("PAPI_DIR='%s' != '%s'", papi_dir, self.papi.install_prefix)
                        raise SoftwarePackageError("PAPI_DIR in TAU Makefile "
                                                   "doesn't match target PAPI installation")
        LOGGER.debug("TAU installation at '%s' is valid", self.install_prefix)
        return True
    
    def configure(self):
        """Configures TAU
        
        Executes TAU's configuration script with appropriate arguments to support the specified configuration.
        
        Raises:
            SoftwareConfigurationError: TAU's configure script failed.
        """
        # TAU's configure script does a really bad job of detecting MPI settings
        # so set up mpiinc, mpilib, mpilibrary when we have that information
        mpiinc = None
        mpilib = None
        mpilibrary = None
        if self.mpi_support: 
            # TAU's configure script does a really bad job detecting the wrapped compiler command
            # so don't even bother trying.  Pass as much of this as we can and hope for the best.
            cc_command = self.compilers[MPI_CC_ROLE].wrapped.info.command
            cxx_command = self.compilers[MPI_CXX_ROLE].wrapped.info.command
            fc_family = self.compilers[MPI_FC_ROLE].wrapped.info.family
            if self.mpi_include_path:
                # Unfortunately, TAU's configure script can only accept one path on -mpiinc
                # and it expects the compiler's include path argument (e.g. "-I") to be omitted
                for path in self.mpi_include_path:
                    if os.path.exists(os.path.join(path, 'mpi.h')):
                        mpiinc = path
                        break
                if not mpiinc:
                    raise ConfigurationError("mpi.h not found on MPI include path: %s" % self.mpi_include_path)
            if self.mpi_library_path:
                # Unfortunately, TAU's configure script can only accept one path on -mpilib
                # and it expects the compiler's include path argument (e.g. "-L") to be omitted
                for path in self.mpi_library_path:
                    if glob.glob(os.path.join(path, 'libmpi*')):
                        mpilib = path
                        break
            if self.mpi_libraries:
                # Multiple MPI libraries can be given but only if they're separated by a '#' symbol
                # and the compiler's library linking flag (e.g. '-l') must be included
                link_library_flag = self.compilers[CC_ROLE].info.family.link_library_flags[0]
                mpilibrary = '#'.join(["%s%s" % (link_library_flag, library) for library in self.mpi_libraries])
        else:
            # TAU's configure script can't cope with compiler absolute paths or compiler names that
            # don't exactly match what it expects.  Use `info.command` instead of `command` to work
            # around these problems e.g. 'gcc-4.9' becomes 'gcc' 
            cc_command = self.compilers[CC_ROLE].info.command
            cxx_command = self.compilers[CXX_ROLE].info.command
            fc_family = self.compilers[FC_ROLE].info.family

        # TAU's configure script can't detect Fortran compiler from the compiler
        # command so translate Fortran compiler command into TAU's funkey magic words
        magic_map = {GNU_COMPILERS: 'gfortran',
                     INTEL_COMPILERS: 'intel',
                     PGI_COMPILERS: 'pgi',
                     SYSTEM_COMPILERS: 'ftn',
                     SYSTEM_MPI_COMPILERS: 'mpif90',
                     INTEL_MPI_COMPILERS: 'mpiifort'}
        try:
            fortran_magic = magic_map[fc_family]
        except KeyError:
            raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)
        
        pdt_cxx_command = self.pdt.compilers[CXX_ROLE].info.command if self.pdt else ''
            
        flags = [ flag for flag in  
                 ['-prefix=%s' % self.install_prefix,
                  '-arch=%s' % self.arch,
                  '-cc=%s' % cc_command,
                  '-c++=%s' % cxx_command,
                  '-pdt_c++=%s' % pdt_cxx_command,
                  '-fortran=%s' % fortran_magic,
                  '-pdt=%s' % self.pdt.install_prefix if self.pdt else '',
                  '-bfd=%s' % self.binutils.install_prefix if self.binutils else '',
                  '-papi=%s' % self.papi.install_prefix if self.papi else '',
                  '-unwind=%s' % self.libunwind.install_prefix if self.libunwind else '',
                  '-pthread' if self.pthreads_support else '',
                  '-mpi' if self.mpi_support else '',
                  '-mpiinc=%s' % mpiinc if mpiinc else '',
                  '-mpilib=%s' % mpilib if mpilib else '',
                  '-mpilibrary=%s' % mpilibrary if mpilibrary else ''
                  ] if flag]
        if self.openmp_support:
            flags.append('-openmp')
            if self.measure_openmp == 'ompt':
                if self.compilers[CC_ROLE].info.family == INTEL_COMPILERS:
                    flags.append('-ompt')
                else:
                    # TODO: Shouldn't this be checked in model `compatible_with`?
                    raise ConfigurationError('OMPT for OpenMP measurement only works with Intel compilers')
            elif self.measure_openmp == 'opari':
                flags.append('-opari')
        cmd = ['./configure'] + flags
        LOGGER.info("Configuring TAU...")
        if util.create_subprocess(cmd, cwd=self._src_path, stdout=False):
            raise SoftwarePackageError('TAU configure failed')
    
    def make_install(self):
        """Installs TAU to ``self.install_prefix``.
        
        Executes 'make install' to build and install TAU.
        
        Raises:
            SoftwarePackageError: 'make install' failed.
        """
        cmd = ['make', 'install'] + parallel_make_flags()
        LOGGER.info('Compiling and installing TAU...')
        if util.create_subprocess(cmd, cwd=self._src_path, stdout=False):
            raise SoftwarePackageError('TAU compilation/installation failed')
    
    def install(self, force_reinstall=False):
        """Installs TAU.
        
        Configures, compiles, and installs TAU with all necessarry makefiles and libraries.
        
        Args:
            force_reinstall (bool): Set to True to force reinstall even if TAU is already installed and working.
            
        Raises:
            SofwarePackageError: TAU failed installation or did not pass verification after it was installed.
        """
        self._check_dependencies()

        if not self.src:
            try:
                return self._verify()
            except SoftwarePackageError as err:
                raise SoftwarePackageError("%s is missing or broken: %s" % (self.name, err),
                                           "Specify source code path or URL to enable broken package reinstallation.")
        elif not force_reinstall:
            try:
                return self._verify()
            except SoftwarePackageError as err:
                LOGGER.debug(err)
        LOGGER.info("Installing %s at '%s' from '%s' with arch=%s and %s compilers",
                    self.name, self.install_prefix, self.src, self.arch, self.compilers[CC_ROLE].info.family)

        self._prepare_src()
        self.configure()
        self.make_install()

        LOGGER.info('%s installation complete', self.name)
        return self._verify()

    def get_makefile_tags(self):
        """Get makefile tags for this TAU installation.

        Each TAU Makefile is identified by its tags.  Tags are also used by
        tau_exec to load the correct version of the TAU shared object library.

        Tags can appear in the makefile name in any order so the order of the
        tags returned by this function will likely not match the order they
        appear in the makefile name or tau_exec command line.

        Returns:
            list: Makefile tags, e.g. ['papi', 'pdt', 'icpc']
        """
        tags = []
        compiler_tags = {INTEL_COMPILERS: 'icpc', 
                         PGI_COMPILERS: 'pgi'}
        try:
            tags.append(compiler_tags[self.compilers[CXX_ROLE].info.family])
        except KeyError:
            pass
        if self.source_inst != 'never':
            tags.append('pdt')
        if len([met for met in self.metrics if 'PAPI' in met]):
            tags.append('papi')
        if self.openmp_support:
            tags.append('openmp')
            openmp_tags = {'ompt': 'ompt', 'opari': 'opari'}
            try:
                tags.append(openmp_tags[self.measure_openmp])
            except KeyError:
                pass
        if self.pthreads_support:
            tags.append('pthread')
        if self.mpi_support:
            tags.append('mpi')
        if self.cuda_support:
            tags.append('cuda')
        if self.shmem_support:
            tags.append('shmem')
        if self.mpc_support:
            tags.append('mpc')
        LOGGER.debug("TAU tags: %s", tags)
        return set(tags)
    
    def _incompatible_tags(self):
        """Returns a set of makefile tags incompatible with the specified config.
        
        Some tags, e.g. PDT, force actions to occur that should not.
        """
        tags = []
        if not self.mpi_support:
            tags.append('mpi')
        if self.source_inst == 'never':
            tags.append('pdt')
        if self.measure_openmp != 'opari':
            tags.append('opari')
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
        tau_makefiles = glob.glob(os.path.join(self.lib_path, 'Makefile.tau*'))
        LOGGER.debug("Found makefiles: '%s'", tau_makefiles)
        config_tags = self.get_makefile_tags()
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
            return makefile
        LOGGER.debug("No TAU makefile approximately matches tags '%s'", config_tags)
        raise SoftwarePackageError("TAU Makefile not found for tags '%s' in '%s'" % 
                                   (', '.join(config_tags), self.install_prefix))

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
        if self.sample or self.compiler_inst != 'never':
            opts.append('-g')
        try:
            tau_opts = env['TAU_OPTIONS'].split(' ')
        except KeyError:
            tau_opts = []       
        tau_opts.append('-optRevert')
        if self.verbose:
            tau_opts.append('-optVerbose')
        else:
            tau_opts.append('-optQuiet')
        if self.compiler_inst == 'always':
            tau_opts.append('-optCompInst')
        elif self.compiler_inst == 'never':
            tau_opts.append('-optNoCompInst')
        elif self.compiler_inst == 'fallback':
            tau_opts.append('-optRevert')
        if self.link_only:
            tau_opts.append('-optLinkOnly')
        if self.keep_inst_files:
            tau_opts.append('-optKeepFiles')
        if self.reuse_inst_files:
            tau_opts.append('-optReuseFiles')
        if self.io_inst:
            tau_opts.append('-optTrackIO')
        env['TAU_MAKEFILE'] = self.get_makefile()
        env['TAU_OPTIONS'] = ' '.join(tau_opts)
        if self.pdt:
            self.pdt.compiletime_config(opts, env)
        if self.binutils:
            self.binutils.compiletime_config(opts, env)
        if self.papi:
            self.papi.compiletime_config(opts, env)
        if self.libunwind:
            self.libunwind.compiletime_config(opts, env)
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
        env['TAU_VERBOSE'] = str(int(self.verbose))
        env['TAU_PROFILE'] = str(int(self.profile))
        env['TAU_TRACE'] = str(int(self.trace))
        env['TAU_SAMPLE'] = str(int(self.sample))
        if self.callpath_depth > 0:
            env['TAU_CALLPATH'] = '1'
            env['TAU_CALLPATH_DEPTH'] = str(self.callpath_depth)
        if self.verbose:
            opts.append('-v')
        if self.sample:
            opts.append('-ebs')
        env['TAU_METRICS'] = os.pathsep.join(self.metrics)
        return list(set(opts)), env

    def get_compiler_command(self, compiler):
        """Get the compiler wrapper command for the given compiler.
        
        Args:
            compiler (InstalledCompiler): A compiler to find a wrapper for.
            
        Returns:
            str: Command for TAU compiler wrapper without path or arguments.
        """
        use_wrapper = (self.source_inst != 'never' or
                       self.compiler_inst != 'never')
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
        tau_env_opts = ['%s=%s' % item for item in env.iteritems() if item[0].startswith('TAU_')]
        LOGGER.info('\n'.join(tau_env_opts))
        LOGGER.info(' '.join(cmd))
        retval = util.create_subprocess(cmd, env=env, stdout=True)
        if retval != 0:
            raise ConfigurationError("TAU was unable to build the application.",
                                     "See detailed output at the end of in '%s'" % logger.LOG_FILE)
        return retval

    def get_application_command(self, application_cmd, application_args):
        """Build a command line to launch an application under TAU.
        
        Sometimes TAU needs to use tau_exec, sometimes not.  This routine
        also handles backend launch commands like `aprun`.
        
        Args:
            application_cmd (str): The application command, e.g. './a.out'.
            application_args (list): The application command line arguments.
            
        Returns:
            tuple: (cmd, env) where `cmd` is the new command line and `env` is
                   a dictionary of environment variables to set before running
                   the application command.
        """
        tau_exec_opts, env = self.runtime_config()
        use_tau_exec = (self.source_inst == 'never' and
                        self.compiler_inst == 'never')
        if use_tau_exec:
            tags = self.get_makefile_tags()
            if not self.mpi_support:
                tags.add('serial')
            cmd = ['tau_exec', '-T', ','.join(tags)] + tau_exec_opts + [application_cmd] + application_args
        else:
            cmd = [application_cmd] + application_args
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
        _, env = super(TauInstallation,self).runtime_config()
        if tool_name:
            tools = [tool_name]
        else:
            tools = ['paraprof', 'pprof']
        for tool in tools:
            if os.path.isfile(path):
                cmd = [tool, path]
            else:
                cmd = [tool]
            LOGGER.info("Opening %s in %s", path, tool)
            retval = util.create_subprocess(cmd, cwd=path, env=env, log=False)
            if retval == 0:
                return
            else:
                LOGGER.warning("%s failed", tool)
        if retval != 0:
            raise ConfigurationError("All visualization or reporting tools failed to open '%s'" % path,
                                     "Check Java installation, X11 installation,"
                                     " network connectivity, and file permissions")
