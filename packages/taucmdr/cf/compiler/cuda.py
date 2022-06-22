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
"""CUDA compiler knowledgebase."""

from taucmdr.cf.compiler import Knowledgebase


CUDA_COMPILERS = Knowledgebase('CUDA', 'Compilers supporting CUDA',
                               CXX=('CUDA', 'CU'),
                               FC=('CUDA Fortran', 'CUF'))

NVHPC = CUDA_COMPILERS.add('NVHPC', CXX='nvcc')

NVIDIA = CUDA_COMPILERS.add('NVIDIA', CXX='nvcc')

IBM = CUDA_COMPILERS.add('IBM', family_regex=r'^IBM XL', version_flags=['-qversion'],
                         FC='xlcuf')

NONE = CUDA_COMPILERS.add('None', CXX='', FC='')

CUDA_CXX = CUDA_COMPILERS.roles['CXX']
CUDA_FC = CUDA_COMPILERS.roles['FC']
