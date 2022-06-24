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
"""MPI compiler knowledgebase.

MPI compilers are a special case for several reasons including:
    1) No binary compatibility guarantee among MPI compilers.
    2) They're almost always wrappers, not actual compilers.
    3) They almost always depend on CPU compilers.

We keep a separate knowledge base for MPI compilers to simplify compiler
identification and because TAU doesn't require MPI for all configurations.
"""
from taucmdr.cf.compiler import Knowledgebase


MPI_COMPILERS = Knowledgebase('MPI', 'Compilers supporting the Message Passing Interface (MPI)',
                              CC=('MPI C', 'MPI_CC'),
                              CXX=('MPI C++', 'MPI_CXX'),
                              FC=('MPI Fortran', ('MPI_FC', 'MPI_F77', 'MPI_F90')))

NVHPC = MPI_COMPILERS.add('NVHPC', family_regex=r'NVIDIA CORPORATION', show_wrapper_flags=['-show'],
                           CC='mpicc',
                           CXX=('mpic++', 'mpicxx', 'mpiCC'),
                           FC=('mpiftn', 'mpif90', 'mpif77', 'mpifort'))

SYSTEM = MPI_COMPILERS.add('System', show_wrapper_flags=['-show'],
                           CC='mpicc',
                           CXX=('mpic++', 'mpicxx', 'mpiCC'),
                           FC=('mpiftn', 'mpif90', 'mpif77', 'mpifort'))

INTEL = MPI_COMPILERS.add('Intel', show_wrapper_flags=['-show'],
                          CC='mpiicc',
                          CXX='mpiicpc',
                          FC='mpiifort')

IBM = MPI_COMPILERS.add('IBM', family_regex=r'^IBM XL',
                        version_flags=['-qversion'],
                        show_wrapper_flags=['-show'],
                        CC=('mpixlc_r', 'mpixlc', 'mpicc'),
                        CXX=('mpixlcxx_r', 'mpixlcxx', 'mpixlC_r', 'mpic++', 'mpicxx', 'mpiCC'),
                        FC=('mpixlf_r', 'mpixlf', 'mpixlf90_r', 'mpixlf90', 'mpixlf95_r', 'mpixlf95',
                            'mpixlf2003_r', 'mpixlf2003', 'mpixlf2008_r', 'mpixlf2008', 'mpixlf77_r', 'mpixlf77',
                            'mpifort', 'mpif90', 'mpif77'))

CRAY = MPI_COMPILERS.add('Cray', family_regex=r'-I.*cray',
                         version_flags=['-craype-verbose', '--version', '-E'],
                         show_wrapper_flags=['-craype-verbose', '--version', '-E'],
                         CC='cc', CXX='CC', FC='ftn')

NONE = MPI_COMPILERS.add('None', #family_regex='',
                         CC='', CXX='', FC='')


MPI_CC = MPI_COMPILERS.roles['CC']
MPI_CXX = MPI_COMPILERS.roles['CXX']
MPI_FC = MPI_COMPILERS.roles['FC']
