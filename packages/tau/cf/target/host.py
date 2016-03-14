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
from tau.cf.target import TAU_ARCH_CRAYCNL, TAU_ARCH_BGP, TAU_ARCH_BGQ, TAU_ARCH_IBM64_LINUX, TAU_ARCH_MIC_LINUX
from tau.cf.compiler.installed import InstalledCompilerFamily
 

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


def preferred_compilers():
    """Get the preferred compiler family for the host architecture.
    
    May probe environment variables and file systems in cases where the arch 
    isn't immediately known to Python.  These tests may be expensive so the 
    detected value is cached to improve performance.

    Returns:
        CompilerFamily: The host's preferred compiler family.
    """
    try:
        inst = preferred_compilers.inst
    except AttributeError:
        from tau.cf.compiler import IBM_COMPILERS, GNU_COMPILERS, CRAY_COMPILERS, INTEL_COMPILERS
        host_tau_arch = tau_arch()
        if host_tau_arch is TAU_ARCH_CRAYCNL:
            LOGGER.debug("Prefering Cray compiler wrappers")
            inst = CRAY_COMPILERS
        elif host_tau_arch in (TAU_ARCH_BGP, TAU_ARCH_BGQ, TAU_ARCH_IBM64_LINUX):
            LOGGER.debug("Prefering IBM compilers")
            inst = IBM_COMPILERS
        elif host_tau_arch is TAU_ARCH_MIC_LINUX:
            LOGGER.debug("Preferring Intel compilers")
            inst = INTEL_COMPILERS
        else:
            LOGGER.debug("No preferred compilers for '%s'", host_tau_arch)
            inst = GNU_COMPILERS
        preferred_compilers.inst = inst
    return inst


def preferred_mpi_compilers():
    """Get the preferred MPI compiler family for the host architecture.
    
    May probe environment variables and file systems in cases where the arch 
    isn't immediately known to Python.  These tests may be expensive so the 
    detected value is cached to improve performance.

    Returns:
        MpiCompilerFamily: The host's preferred compiler family.
    """
    try:
        inst = preferred_mpi_compilers.inst
    except AttributeError:
        from tau.cf.compiler.mpi import IBM_MPI_COMPILERS, CRAY_MPI_COMPILERS, SYSTEM_MPI_COMPILERS 
        host_tau_arch = tau_arch()
        if host_tau_arch is TAU_ARCH_CRAYCNL:
            LOGGER.debug("Prefering Cray MPI compilers")
            inst = CRAY_MPI_COMPILERS
        elif host_tau_arch in (TAU_ARCH_BGP, TAU_ARCH_BGQ, TAU_ARCH_IBM64_LINUX):
            LOGGER.debug("Prefering IBM MPI compilers")
            inst = IBM_MPI_COMPILERS
        elif host_tau_arch is TAU_ARCH_MIC_LINUX:
            LOGGER.debug("Preferring Intel compilers")
            inst = INTEL_MPI_COMPILERS
        else:
            LOGGER.debug("No preferred MPI compilers for '%s'", host_tau_arch)
            inst = SYSTEM_MPI_COMPILERS
        preferred_mpi_compilers.inst = inst
    return inst


def default_compilers():
    """Get the default installed compilers for the host.
    
    This is most likely the installation of the host's preferred compilers, 
    (see :any:`preferred_compilers`) but if those compilers are not installed
    then it will be an installation of any known compiler family. May probe 
    environment variables and file systems in cases where the arch isn't 
    immediately known to Python. These tests may be expensive so the detected 
    value is cached to improve performance.
    
    Raises:
        ConfigurationError: No recognized compilers are installed.
    
    Returns:
        InstalledCompilerFamily: The default compilers.
    """
    try:
        inst = default_compilers.inst
    except AttributeError:
        from tau.cf.compiler import CompilerFamily
        LOGGER.debug("Detecting default host compilers")
        # CompilerFamily.all() returns the host's preferred compilers as the first element
        for family in CompilerFamily.all():
            try:
                inst = InstalledCompilerFamily(family)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                LOGGER.debug("Found a %s compiler installation", family.name)
                default_compilers.inst = inst
                break
        else: 
            raise ConfigurationError("No recognized compilers installed.")
    return inst


def default_mpi_compilers():
    """Get the default installed MPI compilers for the host.
    
    This is most likely the installation of the host's preferred MPI compilers, 
    (see :any:`preferred_mpi_compilers`) but if those compilers are not installed
    then it will be an installation of any known compiler family. May probe 
    environment variables and file systems in cases where the arch isn't 
    immediately known to Python. These tests may be expensive so the detected 
    value is cached to improve performance.
    
    Raises:
        ConfigurationError: No recognized compilers are installed.
    
    Returns:
        InstalledCompilerFamily: The default compilers.
    """
    try:
        inst = default_mpi_compilers.inst
    except AttributeError:
        from tau.cf.compiler.mpi import MpiCompilerFamily
        LOGGER.debug("Detecting default MPI compilers")
        for family in MpiCompilerFamily.all():
            try:
                inst = InstalledCompilerFamily(family)
            except ConfigurationError as err:
                LOGGER.debug(err)
            else:
                LOGGER.debug("Found a %s MPI compiler installation", family.name)
                default_mpi_compilers.inst = inst
                break
        else: 
            raise ConfigurationError("No recognized compilers installed.")
    return inst


def default_compiler(role):
    """Get the default compiler on this host for a given role.
    
    Args:
        role (CompilerRole): The role we need to fill.
    
    Returns:
        InstalledCompiler: The installed compiler that can fill the role.

    Raises:
        ConfigurationError: No installed compiler can fill the role.
    """
    try:
        return default_compilers().preferred(role)
    except KeyError:
        try:
            return default_mpi_compilers().preferred(role)
        except KeyError:
            raise ConfigurationError("No installed compiler can fill the %s role" % role)
