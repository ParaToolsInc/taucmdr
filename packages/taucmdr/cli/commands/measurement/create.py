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
"""``measurement create`` subcommand."""

import os
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CreateCommand
from taucmdr.model.measurement import Measurement


class MeasurementCreateCommand(CreateCommand):
    """``measurement create`` subcommand."""

    def _parse_args(self, argv):
        args = super(MeasurementCreateCommand, self)._parse_args(argv)
        if hasattr(args, 'select_file'):
            absolute_path = os.path.abspath(args.select_file)
            if args.select_file.lower() == 'none':
                args.select_file = None
        return args

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}

        # Set callpath depth to 0 unless the user specified a non-default callpath depth on the command line
        if data.get('trace', 'none') != 'none' and data['callpath'] == self.model.attributes['callpath']['default']:
            data['callpath'] = 0

        return self._create_record(store, data)


COMMAND = MeasurementCreateCommand(Measurement, __name__)
