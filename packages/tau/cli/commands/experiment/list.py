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
"""``tau experiment list`` subcommand."""

from tau import util
from tau.cli.cli_view import ListCommand
from tau.model.experiment import Experiment

def data_size(expr):
    return util.human_size(sum(int(trial.get('data_size', 0)) for trial in expr['trials']))

DASHBOARD_COLUMNS = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Trials', 'function': lambda x: len(x['trials'])},
                     {'header': 'Data Size', 'function': data_size},
                     {'header': 'Target', 'function': lambda x: x['target']['name']},
                     {'header': 'Application', 'function': lambda x: x['application']['name']},
                     {'header': 'Measurement', 'function': lambda x: x['measurement']['name']},
                     {'header': 'TAU Makefile', 'value': 'tau_makefile'}]

COMMAND = ListCommand(Experiment, __name__, dashboard_columns=DASHBOARD_COLUMNS, include_storage_flag=False)
