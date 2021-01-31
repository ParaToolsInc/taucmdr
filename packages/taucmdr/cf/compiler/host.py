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
"""Host CPU compiler knowledgebase.

These are the principal compilers used by the system and **must** be identified
to successfully configure and install TAU.
"""
from taucmdr.cf.compiler import Knowledgebase

HOST_COMPILERS = Knowledgebase('Host', 'Compilers targeting the host CPU',
                               CC=('C', 'CC'),
                               CXX=('C++', 'CXX'),
                               FC=('Fortran', ('FC', 'F77', 'F90')),
                               UPC=('Universal Parallel C', 'UPC'))

SYSTEM = HOST_COMPILERS.add('System', CC='cc', CXX=('c++', 'cxx', 'CC'), FC=('ftn', 'f90', 'f77'), UPC='upc')

GNU = HOST_COMPILERS.add('GNU', family_regex=r'Free Software Foundation, Inc',
                         CC='gcc', CXX='g++', FC=('gfortran', 'g77'), UPC='gupc')

INTEL = HOST_COMPILERS.add('Intel', family_regex=r'Intel Corporation',
                           CC='icc', CXX='icpc', FC='ifort')

PGI = HOST_COMPILERS.add('PGI', family_regex=r'The Portland Group|NVIDIA CORPORATION',
                         CC='pgcc', CXX=('pgCC', 'pgc++', 'pgcxx'), FC=('pgfortran', 'pgf90', 'pgf77'))

IBM = HOST_COMPILERS.add('IBM', family_regex=r'^IBM XL',
                         version_flags=['-qversion'],
                         CC=('xlc_r', 'xlc'),
                         CXX=('xlc++_r', 'xlc++', 'xlC_r', 'xlC', 'xlcuf'),
                         FC=('xlf_r', 'xlf', 'xlf90_r', 'xlf90', 'xlf95_r', 'xlf95',
                             'xlf2003_r', 'xlf2003', 'xlf2008_r', 'xlf2008'))

IBM_BG = HOST_COMPILERS.add('BlueGene',
                            CC=('bgxlc', 'bgxlc_r', 'bgcc', 'bgcc_r', 'bgc89', 'bgc89_r', 'bgc99', 'bgc99_r'),
                            CXX=('bgxlc++', 'bgxlc++_r', 'bgxlC', 'bgxlC_r'),
                            FC=('bgxlf', 'bgxlf_r', 'bgf77', 'bgfort77', 'bgxlf90', 'bgxlf90_r', 'bgf90',
                                'bgxlf95', 'bgxlf95_r', 'bgf95', 'bgxlf2003', 'bgxlf2003_r', 'bgf2003',
                                'bgxlf2008', 'bgxlf2008_r', 'bgf2008'))

CRAY = HOST_COMPILERS.add('Cray', family_regex=r'-I.*cray',
                          version_flags=['-craype-verbose', '--version', '-E'],
                          show_wrapper_flags=['-craype-verbose', '--version', '-E'],
                          CC='cc', CXX='CC', FC='ftn', UPC='cc')

APPLE_LLVM = HOST_COMPILERS.add('Apple', family_regex=r'Apple',
                                CC='cc', CXX='c++')

ARM = HOST_COMPILERS.add('Arm', family_regex=r'Arm C/C\+\+/Fortran Compiler',
                         CC='armclang', CXX='armclang++', FC='armflang')

NEC_SX = HOST_COMPILERS.add('NEC', family_regex=r'NEC Corporation',
                            CC='ncc', CXX='nc++', FC='nfort')

CC = HOST_COMPILERS.roles['CC']
CXX = HOST_COMPILERS.roles['CXX']
FC = HOST_COMPILERS.roles['FC']
UPC = HOST_COMPILERS.roles['UPC']
