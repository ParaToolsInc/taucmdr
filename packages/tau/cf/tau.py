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


LOGGER = logger.getLogger(__name__)

SOURCES = {None: 'http://tau.uoregon.edu/tau.tgz'}

COMPILER_WRAPPERS = {'CC': 'tau_cc.sh',
                     'CXX': 'tau_cxx.sh',
                     'FC': 'tau_f90.sh',
                     'UPC': 'tau_upc.sh'}

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

    def __init__(self, prefix, src, arch, compilers, 
                 verbose=False,
                 pdt_source=None,
                 bfd_source=None,
                 libunwind_source=None,
                 papi_source=None,
                 openmp_support=False,
                 pthreads_support=False, 
                 mpi_support=False,
                 cuda_support=False,
                 shmem_support=False,
                 mpc_support=False,
                 source_inst='never',
                 compiler_inst='fallback',
                 link_only=False,
                 io_inst=False,
                 keep_inst_files=False,
                 reuse_inst_files=False,
                 profile=True,
                 trace=False,
                 sample=False,
                 metrics=['TIME'],
                 measure_mpi=False,
                 measure_openmp='ignore',
                 measure_pthreads=None,
                 measure_cuda=None,
                 measure_shmem=None,
                 measure_mpc=None,
                 measure_memory_usage=None,
                 measure_memory_alloc=None,
                 measure_callpath=2):
        super(TauInstallation, self).__init__('TAU', prefix, src, arch, 
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
        Installs or verifies software packages required by TAU.
        """
        if self.uses_pdt():
            self.pdt = PdtInstallation(self.prefix, self.pdt_source, self.arch, self.compilers)
            self.pdt.install()
        if self.uses_bfd():
            self.bfd = BfdInstallation(self.prefix, self.bfd_source, self.arch, self.compilers)
            self.bfd.install()
        if self.uses_libunwind():
            self.libunwind = LibunwindInstallation(self.prefix, self.libunwind_source, self.arch, self.compilers)
            self.libunwind.install()
        if self.uses_papi():
            self.papi = PapiInstallation(self.prefix, self.papi_source, self.arch, self.compilers)
            self.papi.install()
    
    def verify(self):
        """Returns true if the installation is valid.
        
        A working TAU installation has a directory named `arch` 
        containing `bin` and `lib` directories and provides all expected
        libraries and commands.
        
        Returns:
            True: If the installation at `install_prefix` is working.
        
        Raises:
          SoftwarePackageError: Describes why the installation is invalid.
        """
        self._check_dependencies()
        super(TauInstallation,self).verify(commands=COMMANDS)

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

        LOGGER.info("TAU installation at '%s' is valid" % self.install_prefix)
        return True
    
    def install(self, force_reinstall=False):
        """
        Install TAU.
        """
        if not self.src:
            return self.verify()
        elif not force_reinstall:
            try:
                return self.verify()
            except Exception as err:
                LOGGER.debug(err)
        LOGGER.debug("Installing TAU at '%s' from '%s' with arch=%s" %
                     (self.install_prefix, self.src, self.arch))

        self._prepare_src()

        # TAU's configure script has a goofy way of specifying the fortran compiler
        fc_family = self.compilers.fc.family
        family_map = {'GNU': 'gfortran',
                      'Intel': 'intel',
                      'PGI': 'pgi',
                      'MPI': 'mpif90'}
        try:
            fortran_flag = '-fortran=%s' % family_map[fc_family]
        except KeyError:
            raise InternalError("Unknown compiler family for Fortran: '%s'" % fc_family)

        # Gather TAU configuration flags
        flags = ['-prefix=%s' % self.install_prefix,
                 '-arch=%s' % self.arch,
                 '-cc=%s' % self.compilers.cc.command,
                 '-c++=%s' % self.compilers.cxx.command,
                 fortran_flag,
                 '-pdt=%s' % self.pdt.install_prefix if self.pdt else '',
                 '-bfd=%s' % self.bfd.install_prefix if self.bfd else '',
                 '-papi=%s' % self.papi.install_prefix if self.papi else '',
                 '-unwind=%s' % self.libunwind.install_prefix if self.libunwind else '',
                 '-pthread' if self.pthreads_support else '']
        if self.mpi_support:
            # TODO: -mpiinc, -mpilib, -mpilibrary
            flags.append('-mpi')           
        if self.openmp_support:
            if self.measure_openmp == 'ignore':
                flags.append('-openmp')
            elif self.measure_openmp == 'ompt':
                if self.compilers.cc.family == 'Intel':
                    flags.append('-ompt')
                else:
                    raise ConfigurationError('OMPT for OpenMP measurement only works with Intel compilers')
            elif self.measure_openmp == 'opari':
                flags.append('-opari')
            else:
                raise InternalError('Unknown OpenMP measurement: %s' % self.measure_openmp)

        # Execute configure
        cmd = ['./configure'] + flags
        try:
            LOGGER.info("Configuring TAU...")
            if util.createSubprocess(cmd + ['-iowrapper'], cwd=self._src_path, stdout=False):
                raise SoftwarePackageError('TAU configure failed. Retrying without iowrapper.')

            # Execute make
            cmd = ['make', 'install'] + self._parallel_make_flags()
            LOGGER.info('Compiling TAU...')
            if util.createSubprocess(cmd, cwd=self._src_path, stdout=False):
                raise SoftwarePackageError('TAU compilation failed. Retrying without iowrapper.')
        except SoftwarePackageError:
            LOGGER.warning("Failed to compile TAU with I/O measurement enabled.")
            
            LOGGER.info("Configuring TAU...")
            if util.createSubprocess(cmd, cwd=self._src_path, stdout=False):
                raise SoftwarePackageError('TAU configure failed.')

            # Execute make
            cmd = ['make', 'install'] + self._parallel_make_flags()
            LOGGER.info('Compiling TAU..with out iowrapper.')
            if util.createSubprocess(cmd, cwd=self._src_path, stdout=False):
                raise SoftwarePackageError('TAU compilation failed.')

            # svwip:  need to add a command that sets an attribute to target
            # "iowrapper" to FALSE

        # Verify the new installation
        try:
            return self.verify()
        except Exception as err:
            raise SoftwarePackageError('%s installation failed verification: %s' % (err, self.name))
        else:
            LOGGER.info('%s installation complete', self.name)

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
            tags.append(compiler_tags[self.compilers.cxx.family])
        except KeyError:
            pass
        if self.source_inst != 'never':
            tags.append('pdt')
        if len([met for met in self.metrics if 'PAPI' in met]):
            tags.append('papi')
        if self.openmp_support:
            openmp_tags = {'ignore': 'openmp',
                           'ompt': 'ompt',
                           'opari': 'opari'}
            tags.append(openmp_tags[self.measure_openmp])
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
            compiler: CompilerInfo for a compiler command
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
        retval = util.createSubprocess(cmd, env=env)
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


    def show_profile(self, path):
        """
        Shows profile data in the specified file or folder
        """
        LOGGER.debug("Showing profile files at '%s'" % path)
        _, env = super(TauInstallation,self).runtime_config()
        for viewer in 'paraprof', 'pprof':
            if os.path.isfile(path):
                cmd = [viewer, path]
            else:
                cmd = [viewer]
            LOGGER.info("Opening %s in %s" % (path, viewer))
            retval = util.createSubprocess(cmd, cwd=path, env=env, log=False)
            if retval == 0:
                return
            else:
                LOGGER.warning("%s failed" % viewer)
        if retval != 0:
            raise ConfigurationError("All viewers failed to open '%s'" % path,
                                     "Check that `java` is working, X11 is working,"
                                     " network connectivity, and file permissions")
