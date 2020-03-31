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
"""TAU Commander package initialization.

The first line of this file is the first thing to be executed whenever TAU Commander
is invoked in any way. This module establishes global constants and checks the Python version.
It should be as short and simple.
"""

import os
import sys
# Python3 compatibility
try:
    basestring
except NameError:
    # pylint: disable=invalid-name
    basestring = str

__version__ = "0.0.0"
"""str: TAU Commander Version"""

TAUCMDR_VERSION = __version__
"""str: TAU Commander Version"""

EXIT_FAILURE = -100
"""int: Process exit code indicating unrecoverable failure."""

EXIT_WARNING = 100
"""int: Process exit code indicating non-optimal condition on exit."""

EXIT_SUCCESS = 0
"""int: Process exit code indicating successful operation."""

HELP_CONTACT = '<support@paratools.com>'
"""str: E-mail address users should contact for help."""

TAUCMDR_URL = 'www.taucommander.com'
"""str: URL of the TAU Commander project."""

REQUIRED_PYTHON_VERSION = (2, 7)
"""tuple: Required Python version for TAU Comamnder.

A tuple of at least (MAJOR, MINOR) directly comparible to :any:`sys.version_info`
"""

if sys.version_info[0:2] != REQUIRED_PYTHON_VERSION:
    VERSION = '.'.join([str(x) for x in sys.version_info[0:3]])
    EXPECTED = '.'.join([str(x) for x in REQUIRED_PYTHON_VERSION])
    sys.stderr.write("""%s
%s
%s
Your Python version is %s but Python %s is required.
Please install the required Python version or contact %s for support.
""" % (TAUCMDR_URL, sys.executable, sys.version, VERSION, EXPECTED, HELP_CONTACT))
    sys.exit(EXIT_FAILURE)

TAUCMDR_HOME = os.path.realpath(os.path.abspath(os.environ.get('__TAUCMDR_HOME__',
                                                               os.path.join(os.path.dirname(__file__), '..', '..'))))
"""str: Absolute path to the top-level TAU Commander directory.

This directory contains at least `bin`, `docs`, and `packages` directories and is the root
for system-level package installation paths. **Do not** change it once it is set.
"""

TAUCMDR_SCRIPT = os.environ.get('__TAUCMDR_SCRIPT__', sys.argv[0] or 'tau')
"""str: Script that launched TAU Commander.

Mainly used for help messages. **Do not** change it once it is set.
"""

SYSTEM_PREFIX = os.path.realpath(os.path.abspath(os.environ.get('__TAUCMDR_SYSTEM_PREFIX__',
                                                                os.path.join(TAUCMDR_HOME, 'system'))))
"""str: System-level TAU Commander files."""

USER_PREFIX = os.path.realpath(os.path.abspath(os.environ.get('__TAUCMDR_USER_PREFIX__',
                                                              os.path.join(os.path.expanduser('~'),
                                                                           '.local', 'taucmdr'))))
"""str: User-level TAU Commander files."""

PROJECT_DIR = '.tau'
"""str: Name of the project-level directory containing TAU Commander project files."""

def version_banner():
    """Return a human readable text banner describing the TAU Commander installation."""
    import platform
    import socket
    from datetime import datetime
    import taucmdr.logger
    fmt = ("TAU Commander [ %(url)s ]\n"
           "\n"
           "Prefix         : %(prefix)s\n"
           "Version        : %(version)s\n"
           "Timestamp      : %(timestamp)s\n"
           "Hostname       : %(hostname)s\n"
           "Platform       : %(platform)s\n"
           "Working Dir.   : %(cwd)s\n"
           "Terminal Size  : %(termsize)s\n"
           "Frozen         : %(frozen)s\n"
           "Python         : %(python)s\n"
           "Python Version : %(pyversion)s\n"
           "Python Impl.   : %(pyimpl)s\n"
           "PYTHONPATH     : %(pythonpath)s\n")
    data = {"url": TAUCMDR_URL,
            "prefix": TAUCMDR_HOME,
            "version": TAUCMDR_VERSION,
            "timestamp": str(datetime.now()),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "termsize": 'x'.join([str(dim) for dim in taucmdr.logger.TERM_SIZE]),
            "frozen": getattr(sys, 'frozen', False),
            "python": sys.executable,
            "pyversion": platform.python_version(),
            "pyimpl": platform.python_implementation(),
            "pythonpath": os.pathsep.join(sys.path)}
    return fmt % data
