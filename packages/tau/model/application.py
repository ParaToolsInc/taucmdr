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

# System modules
import string

# TAU modules
import controller as ctl
import arguments as args
import requisite


class Application(ctl.Controller, ctl.ByName):

    """
    Application data model controller
    """

    attributes = {
        'projects': {
            'collection': 'Project',
            'via': 'applications'
        },
        'name': {
            'type': 'string',
            'unique': True,
            'argparse': {'help': 'Application configuration name',
                         'metavar': '<application_name>'}
        },
        'openmp': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--openmp',),
                         'help': 'application uses OpenMP',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction},
        },
        'pthreads': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--pthreads',),
                         'help': 'application uses pthreads',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction}
        },
        'mpi': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--mpi',),
                         'help': 'application uses MPI',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction},
            'compat': {'Measurement': {'mpi': requisite.Required}}
        },
        'cuda': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--cuda',),
                         'help': 'application uses NVIDIA CUDA',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction},
            'compat': {'Target': {'cuda': requisite.Required}}
        },
        'shmem': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--shmem',),
                         'help': 'application uses SHMEM',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction},
        },
        'mpc': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--mpc',),
                         'help': 'application uses MPC',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction}
        },
        'mic-linux': {
            'type': 'boolean',
            'defaultsTo': False,
            'argparse': {'flags': ('--with-mic',),
                         'help': 'application uses MICs',
                         'metavar': 'yes/no',
                         'nargs': '?',
                         'const': True,
                         'action': args.ParseBooleanAction},
            'compat': {'Target': {'mic-linux': requisite.Required}}
      }
    }

    _valid_name = set(string.digits + string.letters + '-_.')

    def onCreate(self):
        if set(self['name']) > Application._valid_name:
            raise ctl.ModelError('%r is not a valid application name.' % self['name'],
                                 'Use only letters, numbers, dot (.), dash (-), and underscore (_).')
