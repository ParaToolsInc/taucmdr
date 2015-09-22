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
"""Application data model attributes."""

# pylint: disable=invalid-name

from tau.cli.arguments import ParseBooleanAction
from tau.schema.project.controller import Project
from tau.schema.target.controller import Target
from tau.schema.measurement.controller import Measurement


projects = { 
    'collection': Project,
    'via': 'applications',
    'description': 'projects using this application'
}

name = {
    'type': 'string',
    'description': 'application configuration name',
    'unique': True,
    'argparse': {'metavar': '<application_name>'}
}

openmp = {
    'type': 'boolean', 
    'description': 'application uses OpenMP',
    'default': False, 
    'argparse': {'flags': ('--openmp',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction},
}

pthreads = {
    'type': 'boolean',
    'description': 'application uses pthreads',
    'default': False,
    'argparse': {'flags': ('--pthreads',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction}
}

mpi = {
    'type': 'boolean',
    'default': False,
    'description': 'application uses MPI',
    'argparse': {'flags': ('--mpi',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction},
    'compat': {True: Measurement.encourage('mpi', True)}
}

cuda = {
    'type': 'boolean',
    'default': False,
    'description': 'application uses NVIDIA CUDA',
    'argparse': {'flags': ('--cuda',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction},
    'compat': {True: Target.require('cuda')}
}

shmem = {
    'type': 'boolean',
    'default': False,
    'description': 'application uses SHMEM',
    'argparse': {'flags': ('--shmem',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction},
}

mpc = {
    'type': 'boolean',
    'default': False,
    'description': 'application uses MPC',
    'argparse': {'flags': ('--mpc',),
                 'metavar': 'yes/no',
                 'nargs': '?',
                 'const': True,
                 'action': ParseBooleanAction}
}
