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
"""Target host hardware and software detection and defaults."""

import os
import platform
from tau import logger
from tau.error import ConfigurationError
from tau.cf.target import Architecture, TauArch, OperatingSystem
from tau.cf.target import IBM_BGP_ARCH, IBM_BGQ_ARCH
from tau.cf.target import CRAY_CNL_OS, IBM_CNK_OS
 

LOGGER = logger.get_logger(__name__)


def architecture():
    """Detect the host's architecture.
        
    Mostly relies on Python's platform module but may also probe 
    environment variables and file systems in cases where the arch 
    isn't immediately known to Python.  These tests may be expensive
    so the detected value is cached to improve performance. 
    
    Returns:
        Architecture: The matching architecture description.
        
    Raises:
        ConfigurationError: Host architecture not supported.
    """
    try:
        inst = architecture.inst
    except AttributeError:
        if os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc"):
            inst = IBM_BGP_ARCH
        elif os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc"):
            inst = IBM_BGQ_ARCH
        else:
            python_arch = platform.machine()
            try:
                inst = Architecture.find(python_arch)
            except KeyError:
                raise ConfigurationError("Host architecture '%s' is not yet supported" % python_arch)
        architecture.inst = inst
    return inst
    


def operating_system():
    """Detect the host's operating system.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and file systems in cases where the arch
    isn't immediately known to Python.  These tests may be expensive
    so the detected value is cached to improve performance.
    
    Returns:
        OperatingSystem: The matching operating system description.
        
    Raises:
        ConfigurationError: Host operating system not supported.
    """
    try:
        inst = operating_system.inst
    except AttributeError:
        arch = architecture()
        if 'CRAYOS_VERSION' in os.environ or 'PE_ENV' in os.environ:
            inst = CRAY_CNL_OS
        elif arch in [IBM_BGP_ARCH, IBM_BGQ_ARCH]:
            inst = IBM_CNK_OS
        else:
            python_os = platform.system()
            try:
                inst = OperatingSystem.find(python_os)
            except KeyError:
                raise ConfigurationError("Host operating system '%s' is not yet supported" % python_os)
        operating_system.inst = inst
    return inst


def tau_arch():
    """Detect the TAU architecture "magic keyword" that matches the host.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and file systems in cases where the arch 
    isn't immediately known to Python.  These tests may be expensive
    so the detected value is cached to improve performance.
    
    Returns:
        TauArch: The matching tau architecture description.
        
    Raises:
        ConfigurationError: Host architecture or operating system not supported.
    """
    try:
        inst = tau_arch.inst
    except AttributeError:
        host_arch = architecture()
        host_os = operating_system()
        try:
            inst = TauArch.get(host_arch, host_os)
        except KeyError:
            raise ConfigurationError("%s on %s is not supported." % (host_os, host_arch))
        tau_arch.inst = inst
    return inst
