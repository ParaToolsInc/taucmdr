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
"""Project data model attributes."""

from tau.core.target.controller import Target
from tau.core.application.controller import Application
from tau.core.measurement.controller import Measurement
from tau.core.experiment.controller import Experiment

ATTRIBUTES = {
    'name': {
        'type': 'string',
        'unique': True,
        'description': 'project name',
        'argparse': {'metavar': '<project_name>'}
    },
    'targets': {
        'collection': Target,
        'via': 'projects',
        'description': 'targets used by this project'
    },
    'applications': {
        'collection': Application,
        'via': 'projects',
        'description': 'applications used by this project'
    },
    'measurements': {
        'collection': Measurement,
        'via': 'projects',
        'description': 'measurements used by this project'
    },
    'experiments': {
        'collection': Experiment,
        'via': 'project',
        'description': 'experiments formed from this project'
    },
    'prefix': {
        'type': 'string',
        'required': True,
        'description': 'location for all files and experiment data related to this project',
        'argparse': {'flags': ('--home',),
                     'metavar': 'path'}
    }
}
