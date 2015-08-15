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
from tau.error import ConfigurationError
from tau.cf.target import Architecture, TauArch, OperatingSystem
from tau.cf.target import IBM_BGP_ARCH, IBM_BGQ_ARCH, CRAY_CNL_OS, IBM_CNK_OS
from tau.cf.compiler import CompilerFamily, IBM_COMPILERS, GNU_COMPILERS, CRAY_COMPILERS
from tau.cf.compiler.mpi import MpiCompilerFamily, IBM_MPI_COMPILERS, CRAY_MPI_COMPILERS, SYSTEM_MPI_COMPILERS
from tau.cf.compiler.installed import CompilerInstallation
 

LOGGER = logger.getLogger(__name__)


_HOST_ARCH = None
def architecture():
    """Detect the host's architecture.
        
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    
    Returns:
        Architecture object.
        
    Raises:
        ConfigurationError: Host architecture not yet supported.
    """
    global _HOST_ARCH
    if not _HOST_ARCH:
        # TODO: Find a better way to detect BlueGene architectures
        if os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc"):
            _HOST_ARCH = IBM_BGP_ARCH
        elif os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc"):
            _HOST_ARCH = IBM_BGQ_ARCH
        else:
            python_arch = platform.machine()
            try:
                _HOST_ARCH = Architecture.find(python_arch)
            except KeyError:
                raise ConfigurationError("Host architecture '%s' is not yet supported" % python_arch)
    return _HOST_ARCH


_HOST_OS = None
def operating_system():
    """Detect the host's operating system.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    
    Returns:
        OperatingSystem object.
        
    Raises:
        ConfigurationError: Host operating system not yet supported.
    """
    global _HOST_OS
    if not _HOST_OS:
        arch = architecture()
        if 'CRAYOS_VERSION' in os.environ or 'PE_ENV' in os.environ:
            _HOST_OS = CRAY_CNL_OS
        elif arch in [IBM_BGP_ARCH, IBM_BGQ_ARCH]:
            _HOST_OS = IBM_CNK_OS
        else:
            python_os = platform.system()
            try:
                _HOST_OS = OperatingSystem.find(python_os)
            except KeyError:
                raise ConfigurationError("Host operating system '%s' is not yet supported" % python_os)
    return _HOST_OS


_TAU_ARCH = None
def tau_arch():
    """Detect the TAU architecture "magic keyword" that matches the host.
    
    Mostly relies on Python's platform module but may also probe 
    environment variables and files in cases where the arch isn't
    immediately known to Python.
    
    Returns:
        TauArch object.
        
    Raises:
        ConfigurationError: Host architecture or operating system not yet supported.
    """
    global _TAU_ARCH
    if not _TAU_ARCH:
        host_arch = architecture()
        host_os = operating_system()
        try:
            _TAU_ARCH = TauArch.find(host_arch, host_os)
        except KeyError:
            raise ConfigurationError("%s on %s is not yet supported" % (host_os, host_arch))
    return _TAU_ARCH


_HOST_PREFERRED_COMPILERS = None
def preferred_compilers():
    """Get the preferred compiler family for the host architecture.
    
    Returns:
        A CompilerFamily object.
    """
    global _HOST_PREFERRED_COMPILERS
    if not _HOST_PREFERRED_COMPILERS: 
        host_tau_arch = tau_arch()
        if host_tau_arch == 'craycnl':
            LOGGER.debug("Prefering Cray compiler wrappers")
            _HOST_PREFERRED_COMPILERS = CRAY_COMPILERS
        elif host_tau_arch in ['bgp', 'bgq']:
            LOGGER.debug("Prefering IBM compilers")
            _HOST_PREFERRED_COMPILERS = IBM_COMPILERS
        else:
            LOGGER.debug("No preferred compilers for '%s'" % host_tau_arch)
            _HOST_PREFERRED_COMPILERS = GNU_COMPILERS
    return _HOST_PREFERRED_COMPILERS


_HOST_PREFERRED_MPI_COMPILERS = None
def preferred_mpi_compilers():
    """Get the preferred compiler family for the host architecture.
    
    Returns:
        A CompilerFamily object.
    """
    global _HOST_PREFERRED_MPI_COMPILERS
    if not _HOST_PREFERRED_MPI_COMPILERS: 
        host_tau_arch = tau_arch()
        if host_tau_arch == 'craycnl':
            LOGGER.debug("Prefering Cray MPI compiler wrappers")
            _HOST_PREFERRED_MPI_COMPILERS = CRAY_MPI_COMPILERS
        elif host_tau_arch in ['bgp', 'bgq']:
            LOGGER.debug("Prefering IBM compilers")
            _HOST_PREFERRED_MPI_COMPILERS = IBM_MPI_COMPILERS
        else:
            LOGGER.debug("No preferred compilers for '%s'" % host_tau_arch)
            _HOST_PREFERRED_MPI_COMPILERS = SYSTEM_MPI_COMPILERS
    return _HOST_PREFERRED_MPI_COMPILERS


_HOST_DEFAULT_COMPILERS = None
def default_compilers():
    """Get the default installed compilers for the host.
    
    This is most likely the installation of the host's preferred compilers, but if those
    compilers are not installed then it will be an installation of any known compiler family.
    
    Returns:
        A CompilerInstallation object.
    """
    global _HOST_DEFAULT_COMPILERS
    if not _HOST_DEFAULT_COMPILERS:
        LOGGER.debug("Detecting default host compilers")
        # CompilerFamily.all() returns the host's preferred compilers as the first element
        for family in CompilerFamily.all():
            try:
                _HOST_DEFAULT_COMPILERS = CompilerInstallation(family)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                LOGGER.debug("Found a %s compiler installation" % family.name)
                return _HOST_DEFAULT_COMPILERS 
        raise ConfigurationError("No recognized compilers installed.")
    return _HOST_DEFAULT_COMPILERS


_HOST_DEFAULT_MPI_COMPILERS = None
def default_mpi_compilers():
    """
    TODO: Docs
    """
    global _HOST_DEFAULT_MPI_COMPILERS
    if not _HOST_DEFAULT_MPI_COMPILERS:
        LOGGER.debug("Detecting default MPI compilers")
        for family in MpiCompilerFamily.all():
            try:
                _HOST_DEFAULT_MPI_COMPILERS = CompilerInstallation(family)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                LOGGER.debug("Found a %s MPI compiler installation" % family.name)
                return _HOST_DEFAULT_MPI_COMPILERS 
        raise ConfigurationError("No recognized compilers installed.")
    return _HOST_DEFAULT_MPI_COMPILERS


def default_compiler(role):
    """Get the default compiler on this host for a given role.
    
    Returns:
        InstalledCompiler object
        
    Raises:
        ConfigurationError: No compiler on this host can fill the role.
    """
    try:
        return default_compilers().preferred(role)
    except KeyError:
        try:
            return default_mpi_compilers().preferred(role)
        except KeyError:
            raise ConfigurationError("No installed compiler can fill the %s role" % role)
