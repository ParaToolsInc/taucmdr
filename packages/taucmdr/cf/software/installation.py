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
"""Software installation management."""

import os
import multiprocessing
from subprocess import CalledProcessError
from contextlib import contextmanager
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.progress import ProgressIndicator
from taucmdr.cf.storage import StorageError
from taucmdr.cf.storage.levels import ORDERED_LEVELS
from taucmdr.cf.storage.levels import highest_writable_storage 
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf import compiler
from taucmdr.cf.compiler import InstalledCompilerSet
from taucmdr.cf.platforms import Architecture, OperatingSystem, HOST_OS, DARWIN

LOGGER = logger.get_logger(__name__)


def parallel_make_flags(nprocs=None):
    """Flags to enable parallel compilation with `make`.
    
    Args:
        ncores (int): Number of parallel processes to use.  
                      Default is one less than the number of CPU cores.
                      
    Returns:
        list: Command line arguments to pass to `make`.
    """
    if not nprocs:
        try:
            nprocs = int(os.environ['__TAUCMDR_MAX_MAKE_JOBS__'])
        except (KeyError, ValueError):
            nprocs = max(1, multiprocessing.cpu_count() - 1)
        try:
            nprocs = int(nprocs)
            if nprocs < 1:
                raise ValueError
        except ValueError:
            raise ConfigurationError("Invalid parallel make job count: %s" % nprocs)
    return ['-j', str(nprocs)]


def tmpfs_prefix():
    """Path to a uniquely named directory in a temporary filesystem, ideally a ramdisk.
    
    /dev/shm is the preferred tmpfs, but if it's unavailable or mounted with noexec then
    fall back to tempfile.gettemdir(), which is usually /tmp.  If that filesystem is also
    unavailable then use the filesystem prefix of the highest writable storage container.
    
    An attempt is made to ensure that there is at least 2GiB of free space in the 
    selected filesystem.  If
    
    Returns:
        str: Path to a uniquely-named directory in the temporary filesystem. The directory 
            and all its contents **will be deleted** when the program exits if it installs
            correctly.
    """
    try:
        return tmpfs_prefix.value
    except AttributeError:
        import tempfile
        import subprocess
        from stat import S_IRUSR, S_IWUSR, S_IEXEC
        candidate = None
        for prefix in "/dev/shm", tempfile.gettempdir(), highest_writable_storage().prefix:
            try:
                tmp_prefix = util.mkdtemp(dir=prefix)
            except (OSError, IOError) as err:
                LOGGER.debug(err)
                continue
            # Check execute privilages some distros mount tmpfs with the noexec option.
            check_exe_script = None
            try:
                with tempfile.NamedTemporaryFile(dir=tmp_prefix, delete=False) as tmp_file:
                    check_exe_script = tmp_file.name
                    tmp_file.write("#!/bin/sh\nexit 0")
                os.chmod(check_exe_script, S_IRUSR | S_IWUSR | S_IEXEC)
                subprocess.check_call([check_exe_script])
            except (OSError, IOError, subprocess.CalledProcessError) as err:
                LOGGER.debug(err)
                continue
            try:
                statvfs = os.statvfs(check_exe_script)
            except (OSError, IOError) as err:
                LOGGER.debug(err)
                if candidate is None:
                    candidate = tmp_prefix
                continue
            else:
                free_mib = (statvfs.f_frsize*statvfs.f_bavail)/0x100000
                LOGGER.debug("%s: %sMB free", tmp_prefix, free_mib)
                if free_mib < 2000:
                    continue
            if check_exe_script:
                os.remove(check_exe_script)
            break
        else:
            if not candidate:
                raise ConfigurationError("No filesystem has at least 2GB free space and supports executables.")
            tmp_prefix = candidate
            LOGGER.warning("Unable to count available bytes in '%s'", tmp_prefix)
        tmpfs_prefix.value = tmp_prefix
        LOGGER.debug("Temporary prefix: '%s'", tmp_prefix)
        return tmp_prefix
    

@contextmanager
def new_os_environ():
    old_environ = os.environ
    try:
        os.environ = dict(os.environ)
        yield os.environ
    finally:
        os.environ = old_environ
        

class Installation(object):
    """Encapsulates a software package installation.
    
    Attributes:
        name (str): The package name, lowercase, alphanumeric with underscores.  All packages have a
                    corresponding ``taucmdr.cf.software.<name>_installation`` module. 
        title (str): Human readable name of the software package, e.g. 'TAU Performance System' or 'Score-P'.
        src (str): Path or URL to a source archive file, 
                   or a path to a directory where the software is installed, 
                   or the special keyword 'download'.
        target_arch (str): Target architecture name.
        target_os (str): Target operating system name.
        compilers (InstalledCompilerSet): Compilers to use if software must be compiled.
        verify_commands (list): List of commands that are present in a valid installation.
        verify_libraries (list): List of libraries that are present in a valid installation.
        verify_headers (list): List of header files that are present in a valid installation.
    """
    
    def __init__(self, name, title, sources, target_arch, target_os, compilers, 
                 repos, commands, libraries, headers):
        """Initializes the installation object.
        
        To set up a new installation, pass a URL, file path, or the special keyword 'download' as the package source.       
        To set up an interface to an existing installation, pass the path to that installation as the package source. 
        
        Args:
            name (str): The package name, lowercase, alphanumeric with underscores.  All packages have a
                        corresponding ``taucmdr.cf.software.<name>_installation`` module. 
            title (str): Human readable name of the software package, e.g. 'TAU Performance System' or 'Score-P'.
            sources (dict): Packages sources as strings indexed by package names as strings.  A source may be a 
                            path to a directory where the software has already been installed, or a path to a source
                            archive file, or the special keyword 'download'.
            target_arch (Architecture): Target architecture.
            target_os (OperatingSystem): Target operating system.
            compilers (InstalledCompilerSet): Compilers to use if software must be compiled.
            repos (dict): Dictionary of URLs for source code archives indexed by architecture and OS.  
                          The None key specifies the default (i.e. universal) source.
            commands (dict): Dictionary of commands, indexed by architecture and OS, that must be installed.
            libraries (dict): Dictionary of libraries, indexed by architecture and OS, that must be installed.
            headers (dict): Dictionary of headers, indexed by architecture and OS, that must be installed.
        """
        # pylint: disable=too-many-arguments
        assert isinstance(name, basestring)
        assert isinstance(title, basestring)
        assert isinstance(sources, dict)
        assert isinstance(target_arch, Architecture)
        assert isinstance(target_os, OperatingSystem)
        assert isinstance(compilers, InstalledCompilerSet)
        assert isinstance(repos, dict) or repos is None
        assert isinstance(commands, dict) or commands is None
        assert isinstance(libraries, dict) or libraries is None
        assert isinstance(headers, dict) or headers is None
        self._src_prefix = None
        self._install_prefix = None
        self._include_subdir = 'include'
        self._bin_subdir = 'bin'
        self._lib_subdir = 'lib'
        self._uid = None
        self.dependencies = {}
        self.name = name
        self.title = title
        self.target_arch = target_arch
        self.target_os = target_os
        self.compilers = compilers
        self.verify_commands = self._lookup_target_os_list(commands)
        self.verify_libraries = self._lookup_target_os_list(libraries)
        self.verify_headers = self._lookup_target_os_list(headers)
        src = sources[name]
        if src.lower() == 'download':
            self.src = self._lookup_target_os_list(repos)
            if isinstance(self.src, list):
                self.srcs = self.src
                self.srcs_avail = self.srcs[:]
                self.src = self.srcs.pop(0)
            else:
                self.srcs = []
                self.srcs_avail = [self.src]
        elif src.lower() == 'download-tr6':
            raise ConfigurationError("download-tr6 is not a valid source for %s" % self.title)
        else:
            self.src = src
        self.unmanaged = os.path.isdir(self.src)

    def uid_items(self):
        """List items affecting this installation's UID.
        
        Most packages only care about changes in source archive, target, or C/C++ compilers.
        More sensitive packages (e.g. Score-P or TAU) can override this function.
        
        Returns:
            list: An **ordered** list of items affecting this installation's UID.
                  Changing the order of this list will change the UID.
        """
        return [self.src, self.target_arch.name, self.target_os.name,
                self.compilers[compiler.host.CC].uid, self.compilers[compiler.host.CXX].uid]
    
    @property
    def uid(self):
        if self._uid is None:
            self._uid = util.calculate_uid(self.uid_items())
        return self._uid

    def _get_install_tag(self):
        return self.uid
    
    def _get_install_prefix(self):
        if not self._install_prefix:
            if self.unmanaged:
                self._set_install_prefix(self.src)
            else:
                tag = self._get_install_tag()
                # Search the storage hierarchy for an existing installation
                for storage in reversed(ORDERED_LEVELS):
                    try:
                        self._set_install_prefix(os.path.join(storage.prefix, self.name, tag))
                        self.verify()
                    except (StorageError, SoftwarePackageError) as err:
                        LOGGER.debug(err)
                        continue
                    else:
                        break
                else:
                    # No existing installation found, install at highest writable storage level
                    self._set_install_prefix(os.path.join(highest_writable_storage().prefix, self.name, tag))
                LOGGER.debug("%s installation prefix is %s", self.name, self._install_prefix)
        return self._install_prefix
    
    def _set_install_prefix(self, value):
        assert value is not None
        self._install_prefix = value

    @property
    def install_prefix(self):
        return self._get_install_prefix()
    
    @property
    def include_path(self):
        return os.path.join(self._get_install_prefix(), self._include_subdir)
    
    @property
    def bin_path(self):
        return os.path.join(self._get_install_prefix(), self._bin_subdir)
    
    @property
    def lib_path(self):
        return os.path.join(self._get_install_prefix(), self._lib_subdir)
    
    def _lookup_target_os_list(self, dct):
        if not dct:
            return []
        default = dct[None]
        try:
            arch_dct = dct[self.target_arch]
        except KeyError:
            return default
        else:
            return arch_dct.get(self.target_os, arch_dct.get(None, default))
        
    def set_group(self, gid=None):
        """Sets the group for all files in the installation.
        
        Args:
            gid (int): Group ID number.  If not given the use the group ID of the folder containing the installation.
        """
        if gid is None:
            parent_stat = os.stat(os.path.dirname(self.install_prefix))
            gid = parent_stat.st_gid
        paths = [self.install_prefix]
        LOGGER.info("Checking installed files...")
        with ProgressIndicator(""):
            for root, dirs, _ in os.walk(self.install_prefix):
                paths.extend((os.path.join(root, x) for x in dirs))
        LOGGER.info("Setting file permissions...")
        with ProgressIndicator("", total_size=len(paths)) as progress_bar:
            for i, path in enumerate(paths):
                try:
                    os.chown(path, -1, gid)
                except OSError as err:
                    LOGGER.debug("Cannot set group on '%s': %s", path, err)
                progress_bar.update(i)
                
    def _acquire_source(self, reuse_archive):
        archive_file = os.path.basename(self.src)
        if reuse_archive:
            for storage in ORDERED_LEVELS:
                try:
                    archive = os.path.join(storage.prefix, "src", archive_file)
                except StorageError:
                    continue
                if os.path.exists(archive):
                    return archive
        archive_prefix = os.path.join(highest_writable_storage().prefix, "src")
        archive = os.path.join(archive_prefix, os.path.basename(self.src))
        try:
            util.download(self.src, archive)
        except IOError:
            hints = ("If a firewall is blocking access to this server, use another method to download "
                     "'%s' and copy that file to '%s' before trying this operation." % (self.src, archive_prefix),
                     "Check that the file or directory is accessible")
            raise ConfigurationError("Cannot acquire source archive '%s'." % self.src, *hints)
        return archive
    
    def acquire_source(self, reuse_archive=True):
        """Acquires package source code archive file via download or file copy.

        If the package is configured to use an existing installation as the source then
        this routine does nothing.
        
        Args:
            reuse_archive (bool): If True don't download, just confirm that the archive exists.
            
        Returns:
            str: Absolute path to the source archive.
            
        Raises:
            ConfigurationError: Package source code not provided or couldn't be acquired.
        """
        if not self.src:
            raise ConfigurationError("No source code provided for %s" % self.title)
        if self.unmanaged:
            return self.src
        # Check that archive is valid by getting archive top-level directory
        while self.src:
            archive = self._acquire_source(reuse_archive)
            try:
                util.archive_toplevel(archive)
            except IOError:
                if reuse_archive:
                    archive = self.acquire_source(reuse_archive=False)
                    try:
                        util.archive_toplevel(archive)
                        return archive
                    except IOError:
                        pass
                try:
                    LOGGER.warning("Unable to acquire %s source package '%s'" % (self.name, self.src))
                    self.src = self.srcs.pop(0)
                    LOGGER.warning("falling back to '%s'" % self.src)
                except IndexError:
                    self.src = None
            else:
                return archive
        if self.src is None:
            raise ConfigurationError("Unable to acquire %s source package '%s'" % (self.name, ', '.join(self.srcs_avail)))
        else:
            return archive

    def _prepare_src(self, reuse_archive=True):
        """Prepares source code for installation.
        
        Acquires package source code archive file via download or file copy,
        unpacks the archive, and verifies that required paths exist.
        
        Args:
            reuse_archive (bool): If True, attempt to reuse archive files.
            
        Returns:
            str: The path to the unpacked source code files.

        Raises:
            ConfigurationError: The source code couldn't be acquired or unpacked.
        """
        archive = self.acquire_source(reuse_archive)
        LOGGER.info("Using %s source archive '%s'", self.title, archive)
        try:
            return util.extract_archive(archive, tmpfs_prefix())
        except IOError as err:
            if reuse_archive:
                LOGGER.info("Unable to extract source archive '%s'.  Downloading a new copy.", archive)
                return self._prepare_src(reuse_archive=False)
            raise ConfigurationError("Cannot extract source archive '%s': %s" % (archive, err),
                                     "Check that the file or directory is accessible")

    def verify(self):
        """Check if the installation at :any:`installation_prefix` is valid.
        
        A valid installation provides all expected files and commands.
        Subclasses may wish to perform additional checks.
        
        Raises:
          SoftwarePackageError: Describs why the installation is invalid.
        """
        LOGGER.debug("Verifying %s installation at '%s'", self.title, self.install_prefix)
        if not os.path.exists(self.install_prefix):
            raise SoftwarePackageError("'%s' does not exist" % self.install_prefix)
        for cmd in self.verify_commands:
            path = os.path.join(self.bin_path, cmd)
            if not os.path.exists(path):
                raise SoftwarePackageError("'%s' is missing" % path)
            if not os.access(path, os.X_OK):
                raise SoftwarePackageError("'%s' exists but is not executable" % path)
        for lib in self.verify_libraries:
            path = os.path.join(self.lib_path, lib)
            if not util.path_accessible(path):
                # Some systems (e.g. SuSE) append the machine bitwidth to the library path
                path = os.path.join(self.lib_path+'64', lib)
                if not util.path_accessible(path):
                    raise SoftwarePackageError("'%s' is not accessible" % path)
        for header in self.verify_headers:
            path = os.path.join(self.include_path, header)
            if not util.path_accessible(path):
                raise SoftwarePackageError("'%s' is not accessible" % path)
        LOGGER.debug("%s installation at '%s' is valid", self.name, self.install_prefix)
        
    def add_dependency(self, name, sources, *args, **kwargs):
        """Adds a new package to the list of packages this package depends on.
        
        Args:
            name (str): The name of the package.  There must be a corresponding 
                        ``taucmdr.cf.software.<name>_installation`` module.
            sources (dict): Packages sources as strings indexed by package names as strings.  A source may be a 
                            path to a directory where the software has already been installed, or a path to a source
                            archive file, or the special keyword 'download'.
        """
        from taucmdr.cf import software
        cls = software.get_installation(name)
        self.dependencies[name] = cls(sources, self.target_arch, self.target_os, self.compilers, *args, **kwargs)

    def install(self, force_reinstall=False):
        """Execute the installation sequence in a sanitized environment.
        
        Modifies the system by building and installing software.
        
        Args:
            force_reinstall (bool): If True, reinstall even if the software package passes verification.
            
        Raises:
            SoftwarePackageError: Installation failed.
        """
        for pkg in self.dependencies.itervalues():
            pkg.install(force_reinstall)
        if self.unmanaged or not force_reinstall:
            try:
                return self.verify()
            except SoftwarePackageError as err:
                if self.unmanaged:
                    raise SoftwarePackageError("%s source package is unavailable and the installation at '%s' "
                                               "is invalid: %s" % (self.title, self.install_prefix, err),
                                               "Specify source code path or URL to enable package reinstallation.")
                elif not force_reinstall:
                    LOGGER.debug(err)
        LOGGER.info("Installing %s to '%s'", self.title, self.install_prefix)
        if os.path.isdir(self.install_prefix):
            LOGGER.info("Cleaning %s installation prefix '%s'", self.title, self.install_prefix)
            util.rmtree(self.install_prefix, ignore_errors=True)
        with new_os_environ(), util.umask(0o002):
            try:
                self._src_prefix = self._prepare_src()
                self.installation_sequence()
                self.set_group()
            except Exception as err:
                LOGGER.info("%s installation failed: %s", self.title, err)
                #util.add_error_stack(self._src_prefix)
                raise
            else:
                # Delete the decompressed source code to save space. The source archive is retained.
                LOGGER.debug("Deleting '%s'", self._src_prefix)
                util.rmtree(self._src_prefix, ignore_errors=True)
                self._src_prefix = None
        # Verify the new installation
        LOGGER.info("Verifying %s installation...", self.title)
        return self.verify()

    def installation_sequence(self):
        raise NotImplementedError

    def compiletime_config(self, opts=None, env=None):
        """Configure compilation environment to use this software package. 

        Returns command line options and environment variables required by this
        software package **when it is used to compile other software packages**.
        The default behavior, to be overridden by subclasses as needed, is to 
        prepend ``self.bin_path`` to the PATH environment variable.
        
        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.
            
        Returns: 
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env if env else os.environ)
        if os.path.isdir(self.bin_path):
            try:
                env['PATH'] = os.pathsep.join([self.bin_path, env['PATH']])
            except KeyError:
                env['PATH'] = self.bin_path
        return opts, env

    def runtime_config(self, opts=None, env=None):
        """Configure runtime environment to use this software package.
        
        Returns command line options and environment variables required by this 
        software package **when other software packages depending on it execute**.
        The default behavior, to be overridden by subclasses as needed, is to 
        prepend ``self.bin_path`` to the PATH environment variable and 
        ``self.lib_path`` to the system library path (e.g. LD_LIBRARY_PATH).
        
        Args:
            opts (list): Optional list of command line options.
            env (dict): Optional dictionary of environment variables.
            
        Returns: 
            tuple: opts, env updated for the new environment.
        """
        opts = list(opts) if opts else []
        env = dict(env if env else os.environ)
        if os.path.isdir(self.bin_path):
            try:
                env['PATH'] = os.pathsep.join([self.bin_path, env['PATH']])
            except KeyError:
                env['PATH'] = self.bin_path
        if os.path.isdir(self.lib_path):
            library_path = 'DYLD_LIBRARY_PATH' if HOST_OS is DARWIN else 'LD_LIBRARY_PATH'   
            try:
                env[library_path] = os.pathsep.join([self.lib_path, env[library_path]])
            except KeyError:
                env[library_path] = self.lib_path
        return opts, env


class MakeInstallation(Installation):
    """Base class for installations that follows the process:
          make [flags] all [options]
          make [flags] install [options]
    """

    def make(self, flags):
        """Invoke `make`.
        
        Args:
            flags (list): Command line flags to pass to `make`.
            
        Raises:
            SoftwarePackageError: Compilation failed.
        """
        assert self._src_prefix
        LOGGER.debug("Making %s at '%s'", self.name, self._src_prefix)
        cmd = ['make'] + parallel_make_flags() + flags
        LOGGER.info("Compiling %s...", self.title)
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            cmd = ['make'] + flags
            if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
                util.add_error_stack(self._src_prefix)
                raise SoftwarePackageError('%s compilation failed' % self.title)

    def make_install(self, flags):
        """Invoke `make install`.
        
        Args:
            flags (list): Command line flags to pass to `make`.
            
        Raises:
            SoftwarePackageError: Configuration failed.
        """
        assert self._src_prefix
        LOGGER.debug("Installing %s to '%s'", self.name, self.install_prefix)
        cmd = ['make', 'install'] + parallel_make_flags() + flags
        LOGGER.info("Installing %s...", self.title)
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            cmd = ['make', 'install'] + flags
            if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
                util.add_error_stack(self._src_prefix)
                raise SoftwarePackageError('%s installation failed' % self.title)
        # Some systems use lib64 instead of lib
        if os.path.isdir(self.lib_path+'64') and not os.path.isdir(self.lib_path):
            os.symlink(self.lib_path+'64', self.lib_path)

    def installation_sequence(self):
        self.make([])
        self.make_install([])


class AutotoolsInstallation(MakeInstallation):
    """Base class for installations that follow the GNU Autotools installation process.
    
    The GNU Autotools installation process is::
        ./configure [options]
        make [flags] all [options] 
        make [flags] install [options]
    """
    
    def configure(self, flags):
        """Invoke `configure`.
        
        Args:
            flags (list): Command line flags to pass to `configure`.
            
        Raises:
            SoftwarePackageError: Configuration failed.
        """
        assert self._src_prefix
        LOGGER.debug("Configuring %s at '%s'", self.name, self._src_prefix)
        cmd = ['./configure', '--prefix=%s' % self.install_prefix] + flags
        LOGGER.info("Configuring %s...", self.title)
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            util.add_error_stack(self._src_prefix)
            raise SoftwarePackageError('%s configure failed' % self.title)   
    
    def installation_sequence(self):
        self.configure([])
        self.make([])
        self.make_install([])
    

class CMakeInstallation(MakeInstallation):
    """Base class for installations that follow the CMake installation process.
    
    The CMake installation process is::
        cmake [options]
        make [flags] all [options] 
        make [flags] install [options]
    """

    def _get_cmake(self):
        cmake = util.which('cmake')
        if not cmake:
            raise ConfigurationError("'cmake' not found in PATH.")
        try:
            stdout = util.get_command_output([cmake, '--version'])
        except (CalledProcessError, OSError) as err:
            raise ConfigurationError("Failed to get CMake version: %s" % err)
        for line in stdout.split('\n'):
            if 'cmake version' in line:
                verstr = (line.split('cmake version ')[1]).split('-')[0]
                version = tuple(int(x) for x in verstr.split('.'))
                if version < (2, 8):
                    raise ConfigurationError("CMake version 2.8 or higher required.")
                break
        else:
            LOGGER.warning("Cannot determine CMake version.  CMake 2.8 or higher is required.")
        return cmake

    def cmake(self, flags):
        """Invoke `cmake`.
        
        Args:
            flags (list): Command line flags to pass to `cmake`.
            
        Raises:
            SoftwarePackageError: Configuration failed.
	"""
        assert self._src_prefix
        cmake = self._get_cmake()
        cmd = [cmake, '-DCMAKE_INSTALL_PREFIX=%s' % self.install_prefix] + flags
        LOGGER.info("Executing CMake for %s...", self.title)
        if util.create_subprocess(cmd, cwd=self._src_prefix, stdout=False, show_progress=True):
            util.add_error_stack(self._src_prefix)
            raise SoftwarePackageError('CMake failed for %s' %self.title)
    
    def installation_sequence(self):
        self.cmake([])
        self.make([])
        self.make_install([])
