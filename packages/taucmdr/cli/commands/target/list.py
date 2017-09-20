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
"""``target list`` subcommand."""

from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.compiler.shmem import SHMEM_CC
from taucmdr.cli.cli_view import ListCommand
from taucmdr.model.target import Target
from taucmdr.model.compiler import Compiler


DASHBOARD_COLUMNS = [{'header': 'Hash', 'hash': 10, 'dtype': 't'},
                     {'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Host OS', 'value': 'host_os'},
                     {'header': 'Host Arch', 'value': 'host_arch'},
                     {'header': 'Host Compilers', 'function': 
                      lambda data: data[CC.keyword]['family']},
                     {'header': 'MPI Compilers', 'function': 
                      lambda data: data.get(MPI_CC.keyword, {'family': 'None'})['family']},
                     {'header': 'SHMEM Compilers', 'function': 
                      lambda data: data.get(SHMEM_CC.keyword, {'family': 'None'})['family']}]

class TargetListCommand(ListCommand):
    
    def _format_long_item(self, key, val):
        fmt_key, fmt_val, flags, description = super(TargetListCommand, self)._format_long_item(key, val)
        attrs = self.model.attributes[key]
        if attrs.get('model') is Compiler:
            fmt_val = '%s (%s)' % (val['path'], val['family'])
        return fmt_key, fmt_val, flags, description


COMMAND = TargetListCommand(Target, __name__, dashboard_columns=DASHBOARD_COLUMNS)
