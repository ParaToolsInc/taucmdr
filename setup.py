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

**IMPORTANT**
It is assumed that this script is run with the same python interpreter as
TAU Commander, i.e. ``import taucmdr`` should be a safe, working operation.
"""


# Package name
from __future__ import absolute_import
from __future__ import print_function
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
    'Development Status :: 5 - Production/Stable',

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
# Distuilts defines attributes in the initialize_options() method
# pylint: disable=wrong-import-position
import os
import sys
import shutil
import pickle
import fnmatch
import tempfile
import fileinput
import subprocess
import setuptools
from setuptools import Command
from setuptools.command.test import test as TestCommand
from setuptools.command.install import install as InstallCommand
from setuptools.command.install_lib import install_lib as InstallLibCommand
from setuptools.command.sdist import sdist as SDistCommand

# Don't show `setup.py` as the root command
os.environ['__TAUCMDR_SCRIPT__'] = 'tau'

PACKAGE_TOPDIR = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(PACKAGE_TOPDIR, 'packages'))


# Customize the BuildSphinx command depending on if Sphinx is installed
try:
    from sphinx import apidoc as sphinx_apidoc
    from sphinx.setup_command import BuildDoc

except ImportError:
    from distutils import cmd as distutils_cmd
    class BuildSphinx(distutils_cmd.Command):
        """Report that Sphinx is required to build documentation."""
        description = 'Sphinx not installed!'
        user_options = []
        def initialize_options(self):
            pass
        def finalize_options(self):
            pass
        def run(self):
            print("Sphinx must be installed to generate developer documentation.")
            sys.exit(-1)

else:
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
                with open(os.devnull, 'w') as fnull:
                    subprocess.check_call(cmd, cwd=cwd or self.builder_target_dir, stderr=fnull, stdout=fnull)
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
            # Distuilts defines attributes in the initialize_options() method
            # pylint: disable=attribute-defined-outside-init
            self.source_dir = copy_source_dir

        def _generate_api_docs(self):
            package_source_dir = os.path.join(PACKAGE_TOPDIR, self.distribution.package_dir[''], 'taucmdr')
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
        # Distuilts defines attributes in the initialize_options() method
        # pylint: disable=attribute-defined-outside-init
        TestCommand.initialize_options(self)
        self.system_sandbox = False
        self.user_sandbox = False

    def run_tests(self):
        os.environ['__TAUCMDR_DISABLE_PAGER__'] = '1'
        if self.system_sandbox:
            tmp_system_prefix = tempfile.mkdtemp()
            os.environ['__TAUCMDR_SYSTEM_PREFIX__'] = tmp_system_prefix
            print("Sandboxing system storage: %s" % tmp_system_prefix)
        if self.user_sandbox:
            tmp_user_prefix = tempfile.mkdtemp()
            os.environ['__TAUCMDR_USER_PREFIX__'] = tmp_user_prefix
            print("Sandboxing user storage: %s" % tmp_user_prefix)
        args = ['--buffer']
        self.test_args = args + self.test_args
        try:
            return TestCommand.run_tests(self)
        finally:
            if self.system_sandbox:
                shutil.rmtree(tmp_system_prefix, ignore_errors=True)
            if self.user_sandbox:
                shutil.rmtree(tmp_user_prefix, ignore_errors=True)


class InstallLib(InstallLibCommand):
    """Custom install_lib command to always compile with optimization."""

    def initialize_options(self):
        InstallLibCommand.initialize_options(self)

    def finalize_options(self):
        # Distuilts defines attributes in the initialize_options() method
        # pylint: disable=attribute-defined-outside-init
        InstallLibCommand.finalize_options(self)
        self.optimize = 1

    def run(self):
        InstallLibCommand.run(self)


class Install(InstallCommand):
    """Customize the install command with new lib, script, and data installation locations."""

    def initialize_options(self):
        InstallCommand.initialize_options(self)

    def finalize_options(self):
        # Distuilts defines attributes in the initialize_options() method
        # pylint: disable=attribute-defined-outside-init
        InstallCommand.finalize_options(self)
        self.install_scripts = os.path.join(self.prefix, 'bin')
        self.install_lib = os.path.join(self.prefix, 'packages')
        self.install_data = os.path.join(self.prefix)
        self.record = os.path.join(self.prefix, 'install.log')
        self.optimize = 1

    def run(self):
        from taucmdr import util
        InstallCommand.run(self)
        util.mkdirp(os.path.join(self.prefix, 'system'))
        shutil.move(os.path.join(self.prefix, 'bin', 'system_configure'),
                    os.path.join(self.prefix, 'system', 'configure'))


class Release(SDistCommand):
    """Build release packages."""

    description = "Build release packages."

    user_options = (SDistCommand.user_options +
                    [('target-arch=', None, "Target architecture"),
                     ('target-os=', None, "Target operating system"),
                     ('web', None, "Build a web-based distribution"),
                     ('all', None, "Build all-in-one packages for all supported (arch, os) combinations")])

    def initialize_options(self):
        SDistCommand.initialize_options(self)
        self.target_arch = None
        self.target_os = None
        self.web = False
        self.all = False

    def finalize_options(self):
        # Distuilts defines attributes in the initialize_options() method
        # pylint: disable=attribute-defined-outside-init
        SDistCommand.finalize_options(self)
        from taucmdr.cf.platforms import Architecture, OperatingSystem, HOST_ARCH, HOST_OS
        if self.all and (self.web or self.target_arch or self.target_os):
            print('--all must not be used with any other arguments')
            sys.exit(-1)
        elif self.web and (self.all or self.target_arch or self.target_os):
            print('--web must not be used with any other arguments')
            sys.exit(-1)
        else:
            try:
                self.target_arch = Architecture.find(self.target_arch or str(HOST_ARCH))
            except KeyError:
                print('Invalid architecture: %s' % self.target_arch)
                print('Known architectures: %s' % list(Architecture.keys()))
                sys.exit(-1)
            try:
                self.target_os = OperatingSystem.find(self.target_os or str(HOST_OS))
            except KeyError:
                print('Invalid operating system: %s' % self.target_os)
                print('Known operating system: %s' % list(OperatingSystem.keys()))
                sys.exit(-1)

    def _software_packages(self):
        import taucmdr.cf.software
        packages = []
        for module_file in os.listdir(taucmdr.cf.software.__path__[0]):
            if module_file.endswith('_installation.py'):
                packages.append(module_file[:-16])
        return packages

    def _download(self, pkg):
        from taucmdr import util
        module_name = pkg + '_installation'
        repos = getattr(__import__('.'.join(('taucmdr', 'cf', 'software', module_name)),
                                   globals(), locals(), ['REPOS'], -1), 'REPOS')
        default = repos[None]
        try:
            arch_dct = repos[self.target_arch]
        except KeyError:
            src = default
        else:
            src = arch_dct.get(self.target_os, arch_dct.get(None, default))
        pkg = os.path.basename(src)
        cache_dir = tempfile.gettempdir()
        cache_db = os.path.join(cache_dir, 'taucmdr.setup_py.downloads')
        cache_pkg = os.path.join(cache_dir, pkg)
        try:
            with open(cache_db, 'r') as fin:
                cache = pickle.load(fin)
        except IOError:
            cache = {}
        if not os.path.exists(cache_pkg) or src != cache.get(cache_pkg):
            print("Downloading '%s' for (%s, %s)" % (pkg, self.target_arch, self.target_os))
            util.download(src, cache_pkg)
        cache[cache_pkg] = src
        with open(cache_db, 'w') as fout:
            pickle.dump(cache, fout)
        util.download(cache_pkg, os.path.join('system', 'src', pkg))

    def _download_python(self):
        from taucmdr.cf.platforms import X86_64, INTEL_KNC, INTEL_KNL, IBM64, PPC64LE, ARM64, DARWIN, LINUX
        make_arch = self.target_arch
        make_os = self.target_os
        arch_map = {X86_64: 'x86_64',
                    INTEL_KNC: 'x86_64',
                    INTEL_KNL: 'x86_64',
                    IBM64: 'ppc64le',
                    PPC64LE: 'ppc64le',
                    ARM64: 'armv71'}
        os_map = {DARWIN: 'Darwin',
                  LINUX: 'Linux'}
        try:
            make_arch = arch_map[self.target_arch]
        except KeyError:
            return
        try:
            make_os = os_map[self.target_os]
        except KeyError:
            return
        # Use `make` to download Python because we keep the Tau/Anaconda target translation in the Makefile
        subprocess.call(['make', 'python_download', 'HOST_ARCH='+make_arch, 'HOST_OS='+make_os])

    def _build_web_release(self):
        SDistCommand.run(self)
        for path in self.archive_files:
            print("Wrote '%s'" % path)

    def _build_target_release(self):
        self._download_python()
        for pkg in self._software_packages():
            self._download(pkg)
        SDistCommand.run(self)
        dist_name = self.distribution.get_fullname()
        for src in self.archive_files:
            ext = os.path.basename(src).split(dist_name)[1]
            dest = '-'.join([dist_name, str(self.target_os), str(self.target_arch)]) + ext
            dest = os.path.join(self.dist_dir, dest)
            shutil.move(src, dest)
            print("Wrote '%s'" % dest)

    def _build_all(self):
        from taucmdr.cf.platforms import TauMagic
        targets = {(magic.architecture, magic.operating_system) for magic in TauMagic.all()}
        for target in targets:
            targ_arch, targ_os = target
            # Setuptools is a dirty, stateful animal.
            # Have to create a new subprocess to hack around setuptools' stateful implementation of sdist.
            subprocess.call(['python', 'setup.py', 'release',
                             '--target-arch', str(targ_arch),
                             '--target-os', str(targ_os)])
        subprocess.call(['python', 'setup.py', 'release', '--web'])

    def run(self):
        from taucmdr import util
        util.rmtree('system', ignore_errors=True)
        # Update package version number
        for line in fileinput.input(os.path.join(PACKAGE_TOPDIR, "packages", "taucmdr", "__init__.py"), inplace=1):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write('__version__ = "%s"\n' % self.distribution.get_version()
                             if line.startswith('__version__') else line)
        if self.web:
            self._build_web_release()
        elif self.all:
            self._build_all()
        else:
            self._build_target_release()


class BuildMarkdown(Command):
    """Generate markdown documentation files for each TAU Commander command"""

    description = "Generate markdown documentation files for each TAU Commander command"

    user_options = [('dest=', None, "Directory in which to write markdown files")]

    def initialize_options(self):
        # Distuilts defines attributes outside __init__
        # pylint: disable=attribute-defined-outside-init
        self.dest = None

    def finalize_options(self):
        # Distuilts defines attributes outside __init__
        # pylint: disable=attribute-defined-outside-init
        if self.dest is None:
            build = self.get_finalized_command('build')
            self.dest = os.path.join(os.path.abspath(build.build_base), 'markdown')
            self.mkpath(self.dest)

    def run(self):
        from unidecode import unidecode
        from taucmdr import cli
        cli.USAGE_FORMAT = "markdown"
        os.environ['ANSI_COLORS_DISABLED'] = '1'
#setup toc file
        tocfilename=os.path.join(self.dest,'tau-commander-user-manual-toc.md')
        tocfile = open(tocfilename, 'w')
        usemanpath ='http://taucommander.paratools.com/tau-commander-user-manual/'
#write preliminary entries not based on commands
        tocfile.write('TAU Commander User Manual\n')
        tocfile.write('Table of Contents\n\n')

        tocfile.write('<a href="')
        tocfile.write(usemanpath)
        tocfile.write('introduction')
        tocfile.write('">')
        tocfile.write('TAU Commander User Manual Introduction')
        tocfile.write('</a>\n')

        tocfile.write('<a href="')
        tocfile.write(usemanpath)
        tocfile.write('tau-commander-installation-2')
        tocfile.write('">')
        tocfile.write('TAU Commander Installation')
        tocfile.write('</a>\n')
        indentspace=''
        bs=1
        for cmd_name in cli.get_all_commands():
            name = cli.command_from_module_name(cmd_name)
            if (name.count(' ') > bs) :
               indentspace = ': '
               bs = name.count(' ')
            if (name.count(' ') == 1) :
               if (bs > 1) :
                   bs = 1
                   indentspace=''
                   tocfile.write('\n')
            cmd_obj = cli.find_command(name.split()[1:])
            tocname=  cmd_name.replace('taucmdr.cli.commands.','tau-commander-')
            tocfile.write(indentspace)
            tocfile.write('<a href="')
            tocfile.write(usemanpath)
            tocfile.write(tocname.replace('.','-'))
            tocfile.write('">')
            tocname=  tocname.replace('tau-commander-','')

            tocname=tocname.replace('.',' ')
            tocfile.write(tocname.capitalize())
            tocfile.write('</a>\n')
            parts = [cmd_obj.help_page,
                     "", "",
                     "Command Line Usage",
                     "==================",
                     "", "",
                     cmd_obj.usage]
            filename = os.path.join(self.dest, cmd_name.replace('.', '_')+'.md')
            with open(filename, 'w') as fout:
                fout.write(unidecode('\n'.join(parts).decode('utf-8')))
            print('wrote %s' % filename)
            indentspace=''
#close tocfile
        tocfile.close


def _version():
    version_file = os.path.join(PACKAGE_TOPDIR, "VERSION")
    if os.path.exists(version_file):
        with open(version_file) as fin:
            version = fin.readline()
    else:
        try:
            version = subprocess.check_output(['./.version.sh'])
        except subprocess.CalledProcessError:
            version = "0.0.0"
    return version.strip()


def _data_files():
    """List files to be copied to the TAU Commander installation.

    Start with the files listed in MANIFEST.in, then exclude files that should not be installed.
    """
    from distutils.filelist import FileList
    from distutils.text_file import TextFile
    from distutils.errors import DistutilsTemplateError
    filelist = FileList()
    template = TextFile(os.path.join(PACKAGE_TOPDIR, 'MANIFEST.in'),
                        strip_comments=1, skip_blanks=1, join_lines=1,
                        lstrip_ws=1, rstrip_ws=1, collapse_join=1)
    try:
        while True:
            line = template.readline()
            if line is None:
                break
            try:
                filelist.process_template_line(line)
            except (DistutilsTemplateError, ValueError) as err:
                print("%s, line %d: %s" % (template.filename, template.current_line, err))
    finally:
        template.close()
    excluded = ['Makefile', 'VERSION', 'MANIFEST.in', '*Miniconda*']
    data_files = []
    for path in filelist.files:
        for excl in excluded:
            if fnmatch.fnmatchcase(path, excl):
                break
        else:
            data_files.append((os.path.dirname(path), [path]))
    return data_files


setuptools.setup(
    # Package metadata
    name=NAME,
    version=_version(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license=LICENSE,
    keywords=KEYWORDS,
    url=HOMEPAGE,
    classifiers=CLASSIFIERS,
    # Package configuration
    packages=setuptools.find_packages("packages"),
    package_dir={"": "packages"},
    scripts=['scripts/tau', 'scripts/system_configure'],
    zip_safe=False,
    data_files=_data_files(),
    # Testing
    test_suite='taucmdr',
    tests_require=['pylint>=1.9.5<2.0.0', 'backports.functools_lru_cache'],
    # Custom commands
    cmdclass={'install': Install,
              'install_lib': InstallLib,
              'test': Test,
              'build_sphinx': BuildSphinx,
              'release': Release,
              'build_markdown': BuildMarkdown}
)
