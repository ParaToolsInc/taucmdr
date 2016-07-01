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

import os
import sys
import shutil
import fileinput
import setuptools
from sphinx import apidoc as sphinx_apidoc
from sphinx.setup_command import BuildDoc 

TAU_HOME = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))

LONG_DESCRIPTION="""
TAU Commander from ParaTools, Inc. is a production-grade performance engineering solution that makes
The TAU Performance System users more productive. It presents a simple, intuitive, and systematic interface that guides
users through performance engineering workflows and offers constructive feedback in case of error. TAU Commander also
enhances the performance engineer's ability to mine actionable information from the application performance data by
connecting to a suite of cloud-based data analysis, storage, visualization, and reporting services.
"""

def update_version():
    """Rewrite packages/tau/__init__.py to update __version__.

    Reads the version number from a file named VERSION in the top-level directory,
    then uses :any:`fileinput` to update __version__ in packages/tau/__init__.py.

    Returns:
        str: The version string to be passed to :any:`setuptools.setup`.
    """
    # Get version number from VERSION file
    try:
        fin = open(os.path.join(TAU_HOME, "VERSION"))
    except IOError:
        sys.stderr.writeln("ERROR: VERSION file is missing!")
        sys.exit(256)
    else:
        version = fin.readline().strip()
    finally:
        fin.close()
    # Set tau.__version__ to match VERSION file
    for line in fileinput.input(os.path.join(TAU_HOME, "packages", "tau", "__init__.py"), inplace=1):
        # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
        if line.startswith("__version__"):
            sys.stdout.write('__version__ = "%s"\n' % version)
        else:
            sys.stdout.write(line)
    return version


class BuildSphinx(BuildDoc):
    """Customize the build_sphinx command.
    
    Copy source files into the build directory to prevent generated files from mixing
    with content files, run sphinx-apidoc to auto-document the "tau" package, then
    proceed with normal build_sphinx behavior.
    """
    def run(self):
        copy_source_dir = os.path.join(self.build_dir, os.path.basename(self.source_dir))
        if os.path.exists(copy_source_dir):
            shutil.rmtree(copy_source_dir, ignore_errors=True)
        shutil.copytree(self.source_dir, copy_source_dir)
        self.source_dir = copy_source_dir
        package_source_dir = os.path.join(TAU_HOME,  self.distribution.package_dir[''], 'tau')
        sphinx_apidoc.main(['-M', # Put module documentation before submodule documentation
                            '-P', # Include "_private" modules
                            '-f', # Overwrite existing files
                            '-e', # Put documentation for each module on its own page
                            '-o', self.source_dir,
                            package_source_dir])
        BuildDoc.run(self)


setuptools.setup(
    name="taucmdr",
    version=update_version(),
    packages=setuptools.find_packages("packages"),
    package_dir={"": "packages"},
    scripts=['bin/tau', 'bin/.tau.py'],
    zip_safe=False,

    # Testing
    test_suite='tau.tests.run_tests',
    tests_require=['pylint'], # Because we run pylint as a unit test

    # Metadata for upload to PyPI
    author="ParaTools, Inc.",
    author_email="info@paratools.com",
    description="An intuitive interface for the TAU Performance System",
    long_description=LONG_DESCRIPTION,
    license="BSD",
    keywords="TAU performance analysis profile profiling trace tracing",
    url="http://www.taucommander.com/",

    # PyPI classifiers
    classifiers=[
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
    ],
                 
    # Custom commands
    cmdclass={
        'build_sphinx': BuildSphinx,
    },

)
