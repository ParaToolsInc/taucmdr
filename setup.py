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
"""TAU Commander packaging.

Program entry point for all activities related to packaging.  Distributions,
documentation, and unit testing are all handled from this script. 
"""

#######################################################################################################################
# PACKAGE CONFIGURATION
#######################################################################################################################

# Package name
NAME = "taucmdr"

# Package author information
AUTHOR = "ParaTools, Inc."
AUTHOR_EMAIL = "info@paratools.com"

# Package short description
DESCRIPTION = "An intuitive interface for the TAU Performance System"

# Package long description
LONG_DESCRIPTION = \
"""TAU Commander from ParaTools, Inc. is a production-grade performance engineering solution that makes
The TAU Performance System users more productive. It presents a simple, intuitive, and systematic 
interface that guides users through performance engineering workflows and offers constructive 
feedback in case of error. TAU Commander also enhances the performance engineer's ability to mine
actionable information from the application performance data by connecting to a suite of cloud-based 
data analysis, storage, visualization, and reporting services."""

# Package software license
LICENSE = "BSD"

# Package keywords
KEYWORDS = ["TAU", "performance analysis", "profile", "profiling", "trace", "tracing"]

# Package homepage
HOMEPAGE = "http://www.taucommander.com/"

# PyPI classifiers
CLASSIFIERS = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: User Interfaces',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: BSD License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
]

#######################################################################################################################
# END PACKAGE CONFIGURATION (probably shouldn't change anything after this line)
#######################################################################################################################


import os
import sys
import shutil
import tempfile
import fileinput
import setuptools
import subprocess
from setuptools import Command
from setuptools.command.test import test as TestCommand
from setuptools.command.install import install as InstallCommand


PACKAGE_TOPDIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))

# Check if sphinx is installed
try:
    from sphinx import apidoc as sphinx_apidoc
    from sphinx.setup_command import BuildDoc
except ImportError:
    HAVE_SPHINX = False
else:
    HAVE_SPHINX = True 

if HAVE_SPHINX:
    class BuildSphinx(BuildDoc):
        """Customize the build_sphinx command.
        
        Copy source files into the build directory to prevent generated files from mixing
        with content files, run sphinx-apidoc to auto-document the "taucmdr" package, then
        proceed with normal build_sphinx behavior.
        """
        
        _custom_user_options = [('update-gh-pages', None, 'Commit documentation to gh-pages branch and push.'),
                                ('gh-origin-url=', None, 'Git repo origin URL'),
                                ('gh-user-name=', None, 'user.name in git config'),
                                ('gh-user-email=', None, 'user.email in git config'),
                                ('gh-commit-msg=', None, 'Commit message for gh-pages log')]
        user_options = BuildDoc.user_options + _custom_user_options
        
        def initialize_options(self):
            BuildDoc.initialize_options(self)
            self.update_gh_pages = False
            self.gh_origin_url = "git@github.com:ParaToolsInc/taucmdr.git"
            self.gh_user_name = None # Use github global conf
            self.gh_user_email = None # Use github global conf
            self.gh_commit_msg = "Updated documentation via build_sphinx"
    
        def _shell(self, cmd, cwd=None):
            try:
                FNULL = open(os.devnull, 'w')
                subprocess.check_call(cmd, cwd=cwd or self.builder_target_dir, stderr=FNULL, stdout=FNULL)
            except subprocess.CalledProcessError as err:
                sys.stderr.write('%s\nFAILURE: Return code %s' % (' '.join(cmd[:2]) + ' ...', err.returncode))
                sys.exit(err.returncode)
    
        def _clone_gh_pages(self):
            shutil.rmtree(self.builder_target_dir, ignore_errors=True)
            cmd = ['git', 'clone', self.gh_origin_url, 
                   '-q', '-b', 'gh-pages', '--single-branch', self.builder_target_dir]
            self._shell(cmd, cwd=self.build_dir)
            if self.gh_user_name:
                self._shell(['git', 'config', 'user.name', self.gh_user_name])
            if self.gh_user_email:
                self._shell(['git', 'config', 'user.email', self.gh_user_email])
        
        def _push_gh_pages(self):
            self._shell(['git', 'add', '-A', '.'])
            self._shell(['git', 'commit', '-q', '-m', self.gh_commit_msg])
            self._shell(['git', 'push', '-q'])
            
        def _copy_docs_source(self):
            copy_source_dir = os.path.join(self.build_dir, os.path.basename(self.source_dir))
            shutil.rmtree(copy_source_dir, ignore_errors=True)
            shutil.copytree(self.source_dir, copy_source_dir)
            self.source_dir = copy_source_dir
    
        def _generate_api_docs(self):
            package_source_dir = os.path.join(PACKAGE_TOPDIR,  self.distribution.package_dir[''], 'taucmdr')
            sphinx_apidoc.main(['-M', # Put module documentation before submodule documentation
                                '-P', # Include "_private" modules
                                '-f', # Overwrite existing files
                                '-e', # Put documentation for each module on its own page
                                '-o', self.source_dir, package_source_dir])
    
        def run(self):
            if self.update_gh_pages:
                self._clone_gh_pages()
            self._copy_docs_source()
            self._generate_api_docs()
            BuildDoc.run(self)
            if self.update_gh_pages:
                self._push_gh_pages()


class Test(TestCommand):
    """Customize the test command to always run in buffered mode."""

    _custom_user_options = [('system-sandbox', 'S', "Sandbox system storage when testing"),
                            ('user-sandbox', 'U', "Sandbox user storage when testing")]
    user_options = TestCommand.user_options + _custom_user_options
    
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.system_sandbox = False
        self.user_sandbox = False
    
    def run_tests(self):
        if self.system_sandbox:
            tmp_system_prefix = tempfile.mkdtemp()
            os.environ['__TAUCMDR_SYSTEM_PREFIX__'] = tmp_system_prefix
            print "Sandboxing system storage: %s" % tmp_system_prefix
        if self.user_sandbox:
            tmp_user_prefix = tempfile.mkdtemp()
            os.environ['__TAUCMDR_USER_PREFIX__'] = tmp_user_prefix
            print "Sandboxing user storage: %s" % tmp_user_prefix
        args = ['--buffer']
        self.test_args = args + self.test_args
        try:
            return TestCommand.run_tests(self)
        finally:
            if self.system_sandbox:
                shutil.rmtree(tmp_system_prefix, ignore_errors=True)
            if self.user_sandbox:
                shutil.rmtree(tmp_user_prefix, ignore_errors=True)


class Install(InstallCommand):

    _custom_user_options = [('initialize', None, "Initialize default TAU project dependencies")]
    user_options = InstallCommand.user_options + _custom_user_options

    def initialize_options(self):
        InstallCommand.initialize_options(self)
        self.initialize = False
    
    def finalize_options(self):
        InstallCommand.finalize_options(self)
        self.install_scripts = os.path.join(self.prefix, 'bin')
        self.install_lib = os.path.join(self.prefix, 'packages')
        self.install_data = os.path.join(self.prefix)
        self.record = os.path.join(self.prefix, 'install.log')

    def _import_system_config(self):
        sys.path.insert(0, os.path.join(self.prefix, 'packages'))
        from taucmdr import configuration
        from taucmdr.cf.storage.levels import SYSTEM_STORAGE
        SYSTEM_STORAGE.connect_filesystem()
        configuration.import_from_file(os.path.join(PACKAGE_TOPDIR, 'defaults.cfg'), SYSTEM_STORAGE)

    def _configure_project(self, init_args):
        from taucmdr import EXIT_SUCCESS 
        from taucmdr.cf.software import SoftwarePackageError
        from taucmdr.cf.storage.levels import PROJECT_STORAGE
        from taucmdr.cli.commands.initialize import COMMAND as init_command
        from taucmdr.cli.commands.select import COMMAND as select_command
        from taucmdr.model.project import Project

        # Call `tau initialize` to configure system-level packages supporting default experiments
        if init_command.main(init_args) != EXIT_SUCCESS:
            raise SoftwarePackageError("`tau initialize` failed with arguments %s." % init_args,
                                       "Check that the values specified in 'defaults.cfg' are valid.")
        # Iterate through default configurations and configure system-level packages for each
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected().populate()
        for targ in proj['targets']:
            for app in proj['applications']:
                for meas in proj['measurements']:
                    argv = ['--target', targ['name'], '--application', app['name'], '--measurement', meas['name']]
                    if select_command.main(argv) != EXIT_SUCCESS:
                        raise SoftwarePackageError("`%s %s` failed." % (select_command, ' '.join(argv)),
                                                   "Check that the values specified in 'defaults.cfg' are valid.")
        # Clean up
        PROJECT_STORAGE.destroy()

    def _configure_new_installation(self):
        sys.path.insert(0, os.path.join(self.prefix, 'packages'))
        import taucmdr
        from taucmdr import logger, util, configuration
        from taucmdr.cli.commands.configure import COMMAND as configure_command

        # Clean up the build directory
        os.chdir(self.build_base)
        util.rmtree('.tau', ignore_errors=True)

        # Show system-level configuration
        configure_command.main(['-@', 'system'])

        # Get configuration
        defaults_cfg = configuration.default_config('defaults.cfg')
        target_cfg = defaults_cfg['Target']
        have_mpi = (target_cfg['MPI_CC'] and target_cfg['MPI_CXX'] and target_cfg['MPI_FC'])
        have_shmem = (target_cfg['SHMEM_CC'] and target_cfg['SHMEM_CXX'] and target_cfg['SHMEM_FC'])

        # Configure TAU and all dependencies in various combinations
        self._configure_project([])
        if have_mpi:
            self._configure_project(['--mpi=True'])
        if have_shmem:
            self._configure_project(['--shmem=True'])
        if have_mpi and have_shmem:
            self._configure_project(['--mpi=True', '--shmem=True'])

        # Indicate success
        print taucmdr.version_banner()
    
    def run(self):
        if not self.force:
            print ("Whoops, this script is used internally by the TAU Commander installer.\n"
                   "Calling it directly can (probably will) break things.\n"
                   "Try this instead:\n"
                   "  ./configure\n"
                   "  make install")
        elif self.initialize:
            self._configure_new_installation()
        else:
            try:
                retval = InstallCommand.run(self)
            except:
                retval = -1
            if not retval:
                self._import_system_config()
                

def update_version():
    """Rewrite packages/taucmdr/__init__.py to update __version__.

    Reads the version number from a file named VERSION in the top-level directory,
    then uses :any:`fileinput` to update __version__ in packages/taucmdr/__init__.py.

    Returns:
        str: The version string to be passed to :any:`setuptools.setup`.
    """
    # Get version number from VERSION file
    try:
        fin = open(os.path.join(PACKAGE_TOPDIR, "VERSION"))
    except IOError:
        sys.stderr.write("ERROR: VERSION file is missing!\n")
        sys.exit(-1)
    else:
        version = fin.readline().strip()
    finally:
        fin.close()
    # Set taucmdr.__version__ to match VERSION file
    for line in fileinput.input(os.path.join(PACKAGE_TOPDIR, "packages", "taucmdr", "__init__.py"), inplace=1):
        # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
        if line.startswith("__version__"):
            sys.stdout.write('__version__ = "%s"\n' % version)
        else:
            sys.stdout.write(line)
    return version


def get_commands():
    cmdclass = {}
    cmdclass['install'] = Install
    cmdclass['test'] = Test
    if HAVE_SPHINX:
        cmdclass['build_sphinx'] = BuildSphinx
    return cmdclass


def get_data_files():
    data_files = [("", ["LICENSE", "README.md", "VERSION"])]
    for root, dirs, files in os.walk("examples"):
        dst_src = (root, [os.path.join(root, i) for i in files])
        data_files.append(dst_src)
    return data_files


setuptools.setup(
    # Package configuration
    name=NAME,
    version=update_version(),
    packages=setuptools.find_packages("packages"),
    package_dir={"": "packages"},
    scripts=['bin/tau'],
    zip_safe=False,
    data_files=get_data_files(),

    # Testing
    test_suite='taucmdr',
    tests_require=['pylint==1.6.4', 'backports.functools_lru_cache'],

    # Metadata for upload to PyPI
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license=LICENSE,
    keywords=KEYWORDS,
    url=HOMEPAGE,
    classifiers=CLASSIFIERS,
    
    # Custom commands
    cmdclass=get_commands(),
)
