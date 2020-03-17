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
"""SHMEM compiler knowledgebase.

Keep a separate knowledge base for SHMEM compilers to simplify compiler
identification and because TAU doesn't require SHMEM for all configurations.
"""
from taucmdr.cf.compiler import Knowledgebase


SHMEM_COMPILERS = Knowledgebase('SHMEM', 'Compilers supporting Symmetric Hierarchical Memory',
                                CC=('SHMEM C', 'SHMEM_CC'),
                                CXX=('SHMEM C++', 'SHMEM_CXX'),
                                FC=('SHMEM Fortran', ('SHMEM_FC', 'SHMEM_F77', 'SHMEM_F90')))

OPENSHMEM = SHMEM_COMPILERS.add('OpenSHMEM',
                                CC='oshcc', CXX=('oshcxx', 'oshc++', 'oshCC'), FC='oshfort')

SOS = SHMEM_COMPILERS.add('SOS',
                          show_wrapper_flags=['-show'],
                          CC='oshcc', CXX=('oshc++', 'oshCC'), FC='oshfort')

CRAY_SHMEM = SHMEM_COMPILERS.add('Cray', family_regex=r'-I.*cray',
                                 version_flags=['-craype-verbose', '--version', '-E'],
                                 show_wrapper_flags=['-craype-verbose', '--version', '-E'],
                                 CC='cc', CXX='CC', FC='ftn')

SHMEM_CC = SHMEM_COMPILERS.roles['CC']
SHMEM_CXX = SHMEM_COMPILERS.roles['CXX']
SHMEM_FC = SHMEM_COMPILERS.roles['FC']
