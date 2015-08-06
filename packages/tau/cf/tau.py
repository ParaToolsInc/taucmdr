#
#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""
import os
import glob
import logger, util
from error import ConfigurationError, InternalError
from cf import SoftwarePackageError
from installation import Installation
from pdt import PdtInstallation
from bfd import BfdInstallation
from libunwind import LibunwindInstallation
from papi import PapiInstallation
from compiler import SYSTEM_FAMILY_NAME, GNU_FAMILY_NAME, INTEL_FAMILY_NAME, PGI_FAMILY_NAME
from compiler.role import *
from arch import TAU_ARCHITECTURES

LOGGER = logger.getLogger(__name__)

SOURCES = {None: 'http://tau.uoregon.edu/tau.tgz'}

COMPILER_WRAPPERS = {CC_ROLE.keyword: 'tau_cc.sh',
                     CXX_ROLE.keyword: 'tau_cxx.sh',
                     FC_ROLE.keyword: 'tau_f90.sh',
                     F77_ROLE.keyword: 'tau_f77.sh',
                     F90_ROLE.keyword: 'tau_f90.sh',
                     UPC_ROLE.keyword: 'tau_upc.sh'}

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


class TauInstallation(Installation):
    """
    Encapsulates a TAU installation
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, prefix, src, host_arch, host_os, compilers, 
                 verbose,
                 # Source for dependencies
                 pdt_source,
                 bfd_source,
                 libunwind_source,
                 papi_source,
                 # Application support features
                 openmp_support,
                 pthreads_support, 
                 mpi_support,
                 mpi_include_path,
                 mpi_library_path,
                 mpi_linker_flags,
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
                 measure_callpath):
        try:
            arch = TAU_ARCHITECTURES[host_arch][host_os]
        except KeyError:
            raise InternalError("Invalid host_arch '%s' or host_os '%s'" % (host_arch, host_os))
        super(TauInstallation, self).__init__('TAU', prefix, src, '', arch, 
                                              compilers, SOURCES)
        self.arch_path = os.path.join(self.install_prefix, arch)
        self.bin_path = os.path.join(self.arch_path, 'bin')
        self.lib_path = os.path.join(self.arch_path, 'lib')
        self.verbose = verbose
        self.pdt_source = pdt_source
        self.bfd_source = bfd_source
        self.libunwind_source = libunwind_source
        self.papi_source = papi_source
        self.openmp_support = openmp_support
        self.pthreads_support = pthreads_support 
        self.mpi_support = mpi_support
        self.mpi_include_path = mpi_include_path
        self.mpi_library_path = mpi_library_path
        self.mpi_linker_flags = mpi_linker_flags
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
        self.measure_callpath = measure_callpath
        for pkg in ['pdt', 'bfd', 'libunwind', 'papi']:
            if eval('self.uses_%s()' % pkg):
                if not getattr(self, '%s_source' % pkg): 
                    raise ConfigurationError("Specified TAU configuration requires %s but no source specified" % pkg)
            else:
                setattr(self, pkg, None)
        
    def uses_pdt(self):
        return (self.source_inst != 'never')
    
    def uses_bfd(self):
        return (self.sample or 
                self.compiler_inst != 'never' or 
                self.openmp_support)
        
    def uses_libunwind(self):
        return (self.arch != 'apple' and
                (self.sample or 
                 self.compiler_inst != 'never' or 
                 self.openmp_support))
        
    def uses_papi(self):
        return bool(len([met for met in self.metrics if 'PAPI' in met]))

    def _check_dependencies(self):
        """
        Ensures all required dependencies are installed and working.
        """
        if self.uses_pdt():
            self.pdt = PdtInstallation(self.prefix, self.pdt_source, self.arch, self.compilers)
            with self.pdt:
                self.pdt.install()
        if self.uses_bfd():
            self.bfd = BfdInstallation(self.prefix, self.bfd_source, self.arch, self.compilers)
            with self.bfd:
                self.bfd.install()
        if self.uses_libunwind():
            self.libunwind = LibunwindInstallation(self.prefix, self.libunwind_source, self.arch, self.compilers)
            with self.libunwind:
                self.libunwind.install()
        if self.uses_papi():
            self.papi = PapiInstallation(self.prefix, self.papi_source, self.arch, self.compilers)
            with self.papi:
                self.papi.install()
    
    def _verify(self):
        """Returns true if the installation is valid.
        
        A working TAU installation has a directory named `arch` 
        containing `bin` and `lib` directories and provides all expected
        libraries and commands.
        
        Returns:
            True: If the installation at `install_prefix` is working.
        
        Raises:
          SoftwarePackageError: Describes why the installation is invalid.
        """
        super(TauInstallation,self)._verify(commands=COMMANDS)

        # Open TAU makefile and check BFDINCLUDE, UNWIND_INC, PAPIDIR, etc.
        makefile = self.get_makefile()
        with open(makefile, 'r') as fin:
            for line in fin:
                if self.bfd and ('BFDINCLUDE=' in line):
                    bfd_inc = line.split('=')[1].strip().strip("-I")
                    if self.bfd.include_path != bfd_inc:
                        LOGGER.debug("BFDINCLUDE='%s' != '%s'" % (bfd_inc, self.bfd.include_path))
                        raise SoftwarePackageError("BFDINCLUDE in TAU Makefile doesn't match target BFD installation")
                if self.libunwind and ('UNWIND_INC=' in line):
                    libunwind_inc = line.split('=')[1].strip().strip("-I")
                    if self.libunwind.include_path != libunwind_inc:
                        LOGGER.debug("UNWIND_INC='%s' != '%s'" % (libunwind_inc, self.libunwind.include_path))
                        raise SoftwarePackageError("UNWIND_INC in TAU Makefile doesn't match target libunwind installation")
                if self.papi and ('PAPIDIR=' in line):
                    papi_dir = line.split('=')[1].strip()
                    if self.papi.install_prefix != papi_dir:
                        LOGGER.debug("PAPI_DIR='%s' != '%s'" % (papi_dir, self.papi.install_prefix))
                        raise SoftwarePackageError("PAPI_DIR in TAU Makefile doesn't match target PAPI installation")

        LOGGER.debug("TAU installation at '%s' is valid" % self.install_prefix)
        return True
    
    def configure(self, additional_flags=[]):
        """Configures TAU
        
        Executes TAU's configuration script with appropriate arguments to suppor the specified configuration.
        
        Args:
            additional_flags: List of additional flags to pass to TAU's configure script.
        
        Raises:
            SoftwareConfigurationError: TAU's configure script failed.
        """
        # TAU's configure script is really bad at detecting wrapped compilers
        # so don't even try.  Replace the compiler wrapper with the wrapped command.
        if self.compilers.CC.wrapped:
            cc = self.compilers.CC.wrapped
            cxx = self.compilers.CXX.wrapped
            fc = self.compilers.FC.wrapped
        else:
            cc = self.compilers.CC
            cxx = self.compilers.CXX
            fc = self.compilers.FC

        # Use `known_info()` instead of `command` to work around TAU's 
        # inability to work with compiler commands that include
        # version numbers in their names, e.g. 'gcc-4.9' becomes 'gcc'
        cc_command = cc.known_info().command
        cxx_command = cxx.known_info().command
        fc_family = fc.family

        # TAU has a really hard time detecting MPI settings in its configure script
        # so set up mpiinc, mpilib, mpilibrary when we have that information
        mpiinc = None
        if self.mpi_include_path:
            # TODO: TAU's configure script can only accept one path on -mpiinc
            for path in self.mpi_include_path:
                if os.path.exists(os.path.join(path, 'mpi.h')):
                    mpiinc = path
                    break
            if not mpiinc:
                raise ConfigurationError("mpi.h not found on MPI include path: %s" % self.mpi_include_path)
        mpilib = None
        if self.mpi_library_path:
            mpilib = self.mpi_library_path[0]
        mpilibrary = None
        if self.mpi_linker_flags:
            mpilibrary = '#'.join(self.mpi_linker_flags)
            
        # Pick the right compiler command for PDT
        if self.pdt:
            if self.pdt.compilers.CXX.wrapped:
                pdt_cxx = self.pdt.compilers.CXX.wrapped
            else:
                pdt_cxx = self.pdt.compilers.CXX

        # TAU's configure script can't detect Fortran compiler from the compiler
        # command so translate Fortran compiler command into TAU's funkey magic words
        magic_map = {GNU_FAMILY_NAME: 'gfortran', 
                     INTEL_FAMILY_NAME: 'intel', 
                     PGI_FAMILY_NAME: 'pgi',
                     SYSTEM_FAMILY_NAME: 'ftn'}
        try:
            fortran_magic = magic_map[fc_family]
        except KeyError:
            raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)

        flags = [ flag for flag in  
                 ['-prefix=%s' % self.install_prefix,
                  '-arch=%s' % self.arch,
                  '-cc=%s' % cc_command,
                  '-c++=%s' % cxx_command,
                  '-fortran=%s' % fortran_magic,
                  '-pdt=%s' % self.pdt.install_prefix if self.pdt else '',
                  '-pdt_c++=%s' % pdt_cxx.command if self.pdt else '',
                  '-bfd=%s' % self.bfd.install_prefix if self.bfd else '',
                  '-papi=%s' % self.papi.install_prefix if self.papi else '',
                  '-unwind=%s' % self.libunwind.install_prefix if self.libunwind else '',
                  '-pthread' if self.pthreads_support else '',
                  '-mpi' if self.mpi_support else '',
                  '-mpiinc=%s' % mpiinc if mpiinc else '',
                  '-mpilib=%s' % mpilib if mpilib else '',
                  '-mpilibrary=%s' % mpilibrary if mpilibrary else '']
                 if flag]
        if self.openmp_support:
            if self.measure_openmp == 'compiler_default':
                flags.append('-openmp')
            elif self.measure_openmp == 'ompt':
                if cc.family == 'Intel':
                    flags.append('-ompt')
                else:
                    raise ConfigurationError('OMPT for OpenMP measurement only works with Intel compilers')
            elif self.measure_openmp == 'opari':
                flags.append('-opari')
            else:
                raise InternalError('Unknown OpenMP measurement: %s' % self.measure_openmp)
        cmd = ['./configure'] + flags + additional_flags
        LOGGER.info("Configuring TAU with %s..." % ' '.join(additional_flags))
        if self._safe_subprocess(cmd, cwd=self._src_path, stdout=False):
            raise SoftwarePackageError('TAU configure failed')
    
    def make_install(self):
        """Installs TAU to `self.install_prefix`.
        
        Executes 'make install' to build and install TAU.
        
        Raises:
            SoftwarePackageError: 'make install' failed.
        """
        cmd = ['make', 'install'] + self._parallel_make_flags()
        LOGGER.info('Compiling and installing TAU...')
        if self._safe_subprocess(cmd, cwd=self._src_path, stdout=False):
            raise SoftwarePackageError('TAU compilation/installation failed')
    
    def install(self, force_reinstall=False):
        """Installs TAU.
        
        Configures, compiles, and installs TAU with all necessarry makefiles and libraries.
        
        Args:
            force_reinstall: Set to True to force reinstall even if TAU is already installed and working.
            
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
        LOGGER.info("Installing %s at '%s' from '%s' with arch=%s and %s compilers" %
                    (self.name, self.install_prefix, self.src, self.arch, self.compilers.CC.family))

        self._prepare_src()

        # Attempt to build TAU with I/O wrapper enabled.  If that doesn't work, disable I/O wrapper and try again.
        try:
            self.configure(['-iowrapper'])
            self.make_install()
        except SoftwarePackageError as err:
            LOGGER.warning(err)
            try:
                self.configure()
                self.make_install()
                # svwip:  need to add a command that sets an attribute to target
                # "iowrapper" to FALSE
            except Exception as err:
                LOGGER.info("TAU installation failed: %s " % err)
                raise

        # Verify the new installation
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
            A list of tags, e.g. ['papi', 'pdt', 'icpc']
        """
        tags = []
        compiler_tags = {'Intel': 'icpc', 'PGI': 'pgi'}
        try:
            tags.append(compiler_tags[self.compilers.CXX.family])
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
        LOGGER.debug("TAU tags: %s" % tags)
        return set(tags)
    
    def _incompatible_tags(self):
        """
        Returns a set of makefile tags incompatible with the specified config
        """
        tags = []
        if not self.mpi_support:
            tags.append('mpi')
        if self.source_inst == 'never':
            tags.append('pdt')
        LOGGER.debug("Incompatible tags: %s" % tags)
        return set(tags)

    def get_makefile(self):
        """Returns an absolute path to a TAU_MAKEFILE.

        The file returned *should* supply all requested measurement features 
        and application support features specified in the constructor.

        Returns:
            A file path that could be used to set the TAU_MAKEFILE environment
            variable, or None if a suitable makefile couldn't be found.
        """
        config_tags = self.get_makefile_tags()
        tau_makefiles = glob.glob(os.path.join(self.lib_path, 'Makefile.tau*'))
        LOGGER.debug('Found makefiles: %r' % tau_makefiles)
        approx_tags = None
        approx_makefile = None
        dangerous_tags = self._incompatible_tags()
        for makefile in tau_makefiles:
            tags = set(os.path.basename(makefile).split('.')[1].split('-')[1:])
            if config_tags <= tags:
                if tags <= config_tags:
                    makefile = os.path.join(self.lib_path, makefile) 
                    LOGGER.debug("Found TAU makefile %s" % makefile)
                    return makefile
                elif not (tags & dangerous_tags):
                    if not approx_tags:
                        approx_tags = tags
                    elif tags < approx_tags:
                        approx_makefile = makefile
                        approx_tags = tags
        LOGGER.debug("No TAU makefile exactly matches tags '%s'" % config_tags)
        if approx_makefile:
            makefile = os.path.join(self.lib_path, approx_makefile) 
            LOGGER.debug("Found approximate match with TAU makefile %s" % makefile)
            return makefile
        LOGGER.debug("No TAU makefile approximately matches tags '%s'" % config_tags)
        raise SoftwarePackageError("TAU Makefile not found for tags '%s' in '%s'" % 
                                   (', '.join(config_tags), self.install_prefix))

    def compiletime_config(self, opts=None, env=None):
        """Configures environment for compilation with TAU.

        Modifies incoming command line arguments and environment variables
        for the TAU compiler wrapper scripts.

        Args:
            opts: List of command line options.
            env: Dictionary of environment variables
        """
        opts, env = super(TauInstallation,self).compiletime_config(opts, env)
        if self.sample:
            # TODO: Handle compilers that don't use -g for debug symbols
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
        if self.bfd:
            self.bfd.compiletime_config(opts, env)
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
            opts: List of command line options.
            env: Dictionary of environment variables
        """
        opts, env = super(TauInstallation,self).runtime_config(opts, env)
        env['TAU_VERBOSE'] = str(int(self.verbose))
        env['TAU_PROFILE'] = str(int(self.profile))
        env['TAU_TRACE'] = str(int(self.trace))
        env['TAU_SAMPLE'] = str(int(self.sample))
        if self.measure_callpath > 0:
            env['TAU_CALLPATH'] = '1'
            env['TAU_CALLPATH_DEPTH'] = str(self.measure_callpath)
        if self.verbose:
            opts.append('-v')
        if self.sample:
            opts.append('-ebs')
        env['TAU_METRICS'] = os.pathsep.join(self.metrics)
        return list(set(opts)), env


    def compile(self, compiler, compiler_args):
        """Executes a compilation command.
        
        Sets TAU environment variables and configures TAU compiler wrapper
        command line arguments to match specified configuration, then
        executes the compiler command. 
        
        Args:
            compiler: Compiler object for a compiler command
            compiler_args: List of compiler command line arguments
        
        Raises:
            ConfigurationError: Compilation failed
        """
        opts, env = self.compiletime_config() 
        use_wrapper = (self.source_inst != 'never' or 
                       self.compiler_inst != 'never')
        if use_wrapper:
            compiler_cmd = compiler.tau_wrapper
        else:
            compiler_cmd = compiler.command
        cmd = [compiler_cmd] + opts + compiler_args
        LOGGER.info(' '.join(cmd))
        retval = util.createSubprocess(cmd, env=env, stdout=True)
        if retval != 0:
            raise ConfigurationError("TAU was unable to build the application.",
                                     "See detailed output at the end of in '%s'" % logger.LOG_FILE)

    def get_application_command(self, application_cmd, application_args):
        
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
        """
        Shows profile data in the specified file or folder
        """
        LOGGER.debug("Showing profile files at '%s'" % path)
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
            LOGGER.info("Opening %s in %s" % (path, tool))
            retval = util.createSubprocess(cmd, cwd=path, env=env, log=False)
            if retval == 0:
                return
            else:
                LOGGER.warning("%s failed" % tool)
        if retval != 0:
            raise ConfigurationError("All visualization or reporting tools failed to open '%s'" % path,
                                     "Check Java installation, X11 installation,"
                                     " network connectivity, and file permissions")
