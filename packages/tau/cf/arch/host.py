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
import platform
from tau import logger
from cf.arch import TAU_ARCHITECTURES
from tau.error import InternalError

LOGGER = logger.getLogger(__name__)

def detect_arch():
    """Returns a commonly recognized string for the host architecture.
    
    This is not necessarrily TAU's magic arch keyword.
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    """
    host_arch = platform.machine()
    if not host_arch:
        raise InternalError("Cannot detect host architecture")
    return host_arch
    

def detect_os():
    """Returns a commonly recognized string for the host operating system.
    
    This is not necessarrily TAU's magic arch keyword.
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    """
    host_os = None
    if 'CRAYOS_VERSION' in os.environ or 'PE_ENV' in os.environ:
        host_os = 'CNL'
    if not host_os:
        host_os = platform.system()
    if not host_os:
        raise InternalError("Cannot detect host operating system")
    return host_os
    

def detect_host():
    """Return the TAU magic arch keyword for the host architecture.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    """
    LOGGER.debug("Detecting host architecture")
    
    host_arch = detect_arch()
    host_os = detect_os()
    try:
        return TAU_ARCHITECTURES[host_arch][host_os]
    except KeyError:
        raise InternalError("No known TAU architecture for (%s, %s)" % (host_arch, host_os))
      
