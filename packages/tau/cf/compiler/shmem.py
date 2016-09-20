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
"""SHMEM compiler detection.

Keep a separate knowledge base for SHMEM compilers to simplify compiler
identification and because TAU doesn't require SHMEM for all configurations.
"""

from tau import logger
from tau.cf.compiler import CompilerFamily, CompilerRole


LOGGER = logger.get_logger(__name__)


class ShmemCompilerFamily(CompilerFamily):
    """Information about a SHMEM compiler family.
    
    Subclassing CompilerFamily creates a second database of compiler family 
    records and keeps SHMEM compilers from mixing with host etc. compilers.
    """

    @classmethod
    def preferred(cls):
        """Get the preferred SHMEM compiler family for the host architecture.
        
        May probe environment variables and file systems in cases where the arch 
        isn't immediately known to Python.  These tests may be expensive so the 
        detected value is cached to improve performance.
    
        Returns:
            ShmemCompilerFamily: The host's preferred compiler family.
        """
        try:
            inst = cls._shmem_preferred
        except AttributeError:
            from tau.cf import target
            from tau.cf.target import host
            var_roles = {'SHMEM_CC': SHMEM_CC_ROLE, 'SHMEM_CXX': SHMEM_CXX_ROLE, 'SHMEM_FC': SHMEM_FC_ROLE, 
                         'SHMEM_F77': SHMEM_FC_ROLE, 'SHMEM_F90': SHMEM_FC_ROLE}
            inst = cls._env_preferred_compilers(var_roles)
            if inst:
                LOGGER.debug("Preferring %s SHMEM compilers by environment", inst.name)
            else:
                host_tau_arch = host.tau_arch()
                if host_tau_arch is target.TAU_ARCH_CRAYCNL:
                    inst = CRAY_SHMEM_COMPILERS
                else:
                    inst = OPENSHMEM_SHEM_COMPILERS
            LOGGER.debug("%s prefers %s SHMEM compilers by default", host_tau_arch, inst.name)
            cls._shmem_preferred = inst
        return inst

SHMEM_CC_ROLE = CompilerRole('SHMEM_CC', 'SHMEM C')
SHMEM_CXX_ROLE = CompilerRole('SHMEM_CXX', 'SHMEM C++')
SHMEM_FC_ROLE = CompilerRole('SHMEM_FC', 'SHMEM Fortran')
SHMEM_COMPILER_ROLES = SHMEM_CC_ROLE, SHMEM_CXX_ROLE, SHMEM_FC_ROLE

OPENSHMEM_SHEM_COMPILERS = ShmemCompilerFamily('OpenSHMEM')
OPENSHMEM_SHEM_COMPILERS.add(SHMEM_CC_ROLE, 'oshcc')
OPENSHMEM_SHEM_COMPILERS.add(SHMEM_CXX_ROLE, 'oshcxx', 'oshc++')
OPENSHMEM_SHEM_COMPILERS.add(SHMEM_FC_ROLE, 'oshfort')

CRAY_SHMEM_COMPILERS = ShmemCompilerFamily('Cray', show_wrapper_flags=['-craype-verbose', '--version', '-E'])
CRAY_SHMEM_COMPILERS.add(SHMEM_CC_ROLE, 'cc')
CRAY_SHMEM_COMPILERS.add(SHMEM_CXX_ROLE, 'CC')
CRAY_SHMEM_COMPILERS.add(SHMEM_FC_ROLE, 'ftn')
