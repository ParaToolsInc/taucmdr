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

# System modules
import os
import sys
from tau import EXIT_FAILURE


def get_env(name):
    """Returns the value of an environment variable.
    
    If the named environment variable is not set then write a message to
    stderr and exit the process with status code tau.EXIT_FAILURE.
    
    Args:
        name: Environment variable name.
    
    Returns:
        Value of the named environment variable.
    """
    try:
        return os.environ[name]
    except KeyError:
        sys.stderr.write("""
%(bar)s
!
! CRITICAL ERROR: %(name)s environment variable not set.
!
%(bar)s
  """ % {'bar': '!' * 80,
         'name': name})
        sys.exit(EXIT_FAILURE)


# TAU Commander home path
try:
    TAU_HOME = os.environ['__TAU_HOME__']
except KeyError:
    from tempfile import gettempdir
    SYSTEM_PREFIX = gettempdir()
    TAU_HOME = None
else:
    SYSTEM_PREFIX = os.path.realpath(os.path.join(TAU_HOME, '.system'))

# The script that launched TAU Commander
TAU_SCRIPT = get_env('__TAU_SCRIPT__')

# User-level TAU files
USER_PREFIX = os.path.join(os.path.expanduser('~'), '.tau')
