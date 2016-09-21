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
"""MPI compiler detection.

MPI compilers are a special case for several reasons including:
    1) No binary compatibility guarantee among MPI compilers.
    2) They're almost always wrappers, not actual compilers.
    3) They almost always depend on system compilers.
    
We keep a separate knowledge base for MPI compilers to simplify compiler
identification and because TAU doesn't require MPI for all configurations.
"""

from tau import logger
from tau.cf.compiler import CompilerFamily, CompilerRole


LOGGER = logger.get_logger(__name__)


class MpiCompilerFamily(CompilerFamily):
    """Information about an MPI compiler family.
    
    Subclassing CompilerFamily creates a second database of compiler family 
    records and keeps MPI compilers from mixing with host etc. compilers.
    """
    
    def __init__(self, *args, **kwargs):
        if 'show_wrapper_flags' not in kwargs:
            kwargs['show_wrapper_flags'] = ['-show']
        super(MpiCompilerFamily, self).__init__(*args, **kwargs)

    @classmethod
    def preferred(cls):
        """Get the preferred MPI compiler family for the host architecture.
        
        May probe environment variables and file systems in cases where the arch 
        isn't immediately known to Python.  These tests may be expensive so the 
        detected value is cached to improve performance.
    
        Returns:
            MpiCompilerFamily: The host's preferred compiler family.
        """
        try:
            inst = cls._mpi_preferred
        except AttributeError:
            from tau.cf import target
            from tau.cf.target import host
            host_tau_arch = host.tau_arch()
            if host_tau_arch is target.TAU_ARCH_CRAYCNL:
                inst = CRAY_MPI_COMPILERS
            elif host_tau_arch in (target.TAU_ARCH_BGP, target.TAU_ARCH_BGQ, target.TAU_ARCH_IBM64_LINUX):
                inst = IBM_MPI_COMPILERS
            elif host_tau_arch is target.TAU_ARCH_MIC_LINUX:
                inst = INTEL_MPI_COMPILERS
            else:
                inst = SYSTEM_MPI_COMPILERS
            LOGGER.debug("%s prefers %s MPI compilers by default", host_tau_arch, inst.name)
            cls._mpi_preferred = inst
        return inst


MPI_CC_ROLE = CompilerRole('MPI_CC', 'MPI C', ['MPI_CC'])
MPI_CXX_ROLE = CompilerRole('MPI_CXX', 'MPI C++', ['MPI_CXX'])
MPI_FC_ROLE = CompilerRole('MPI_FC', 'MPI Fortran', ['MPI_FC', 'MPI_F77', 'MPI_F90'])
MPI_COMPILER_ROLES = MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE

SYSTEM_MPI_COMPILERS = MpiCompilerFamily('System')
SYSTEM_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpicc')
SYSTEM_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpic++', 'mpicxx', 'mpiCC')
SYSTEM_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpiftn', 'mpif90', 'mpif77')

INTEL_MPI_COMPILERS = MpiCompilerFamily('Intel')
INTEL_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpiicc')
INTEL_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpiicpc')
INTEL_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpiifort')

IBM_MPI_COMPILERS = MpiCompilerFamily('IBM')
IBM_MPI_COMPILERS.add(MPI_CC_ROLE, 'mpixlc', 'mpixlc_r', )
IBM_MPI_COMPILERS.add(MPI_CXX_ROLE, 'mpixlcxx', 'mpixlcxx_r')
IBM_MPI_COMPILERS.add(MPI_FC_ROLE, 'mpixlf95', 'mpixlf95_r', 'mpixlf90', 'mpixlf90_r', 
                      'mpixlf2003', 'mpixlf2003_r', 'mpixlf2008', 'mpixlf2008_r', 'mpixlf77', 'mpixlf77_r', )

CRAY_MPI_COMPILERS = MpiCompilerFamily('Cray', show_wrapper_flags=['-craype-verbose', '--version', '-E'])
CRAY_MPI_COMPILERS.add(MPI_CC_ROLE, 'cc')
CRAY_MPI_COMPILERS.add(MPI_CXX_ROLE, 'CC')
CRAY_MPI_COMPILERS.add(MPI_FC_ROLE, 'ftn')
