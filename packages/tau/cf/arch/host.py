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
from tau import logger, util
from cf.arch import TAU_ARCHITECTURES
from tau.error import ConfigurationError
from cf.compiler import KNOWN_FAMILIES, MPI_FAMILY_NAME
from cf.compiler.role import REQUIRED_ROLES, CC_ROLE, CXX_ROLE, FC_ROLE

LOGGER = logger.getLogger(__name__)

def _detect_arch():
    """A commonly recognized string for the host architecture.
    
    This is not necessarrily TAU's magic arch keyword.
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    """
    host_arch = platform.machine()
    if not host_arch:
        raise ConfigurationError("Cannot detect host architecture")
    return host_arch
HOST_ARCH = _detect_arch()
    

def _detect_os():
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
        raise ConfigurationError("Cannot detect host operating system")
    return host_os
HOST_OS = _detect_os()

def _detect_tau_arch():
    """Return the TAU magic arch keyword for the host architecture.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    """
    LOGGER.debug("Detecting host architecture")
    
    host_arch = _detect_arch()
    host_os = _detect_os()
    try:
        return TAU_ARCHITECTURES[host_arch][host_os]
    except KeyError:
        raise ConfigurationError("No known TAU architecture for (%s, %s)" % (host_arch, host_os))
TAU_ARCH = _detect_tau_arch()

def _detect_default_compilers():
    """
    TODO: Docs
    """
    if TAU_ARCH == 'craycnl':
        return {CC_ROLE.keyword: 'cc',
                CXX_ROLE.keyword: 'CC',
                FC_ROLE.keyword: 'ftn'}
    excluded_families = [MPI_FAMILY_NAME]
    for family_name, compilers in KNOWN_FAMILIES.iteritems():
        if family_name not in excluded_families:
            missing_roles = [role.keyword for role in REQUIRED_ROLES]
            found = {}
            for comp in compilers:
                if util.which(comp.command):
                    found[comp.role.keyword] = comp.command
                    try: missing_roles.remove(comp.role.keyword)
                    except ValueError: pass
            if not missing_roles:
                return found
    raise ConfigurationError("No recognized compilers are installed")
HOST_DEFAULT_COMPILERS = _detect_default_compilers()
HOST_DEFAULT_CC = HOST_DEFAULT_COMPILERS[CC_ROLE.keyword]
HOST_DEFAULT_CXX = HOST_DEFAULT_COMPILERS[CXX_ROLE.keyword]
HOST_DEFAULT_FC = HOST_DEFAULT_COMPILERS[FC_ROLE.keyword]
