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
"""``application edit`` subcommand."""

import os
from taucmdr.error import ImmutableRecordError, IncompatibleRecordError
from taucmdr.cli.cli_view import EditCommand
from taucmdr.cli.commands.application.copy import COMMAND as application_copy_cmd
from taucmdr.cli.commands.experiment.delete import COMMAND as experiment_delete_cmd
from taucmdr.model.application import Application
from taucmdr.model.experiment import Experiment


class ApplicationEditCommand(EditCommand):
    """``application edit`` subcommand."""
    
    def _parse_args(self, argv):
        args = super(ApplicationEditCommand, self)._parse_args(argv)
        if hasattr(args, 'select_file'):
            absolute_path = os.path.abspath(args.select_file)
            if args.select_file.lower() == 'none':
                absolute_path = None
            elif not os.path.exists(absolute_path):
                self.parser.error("Selective instrumentation file '%s' not found" % absolute_path)
            args.select_file = absolute_path
        return args

    def _update_record(self, store, data, key):
        try:
            retval = super(ApplicationEditCommand, self)._update_record(store, data, key)
        except (ImmutableRecordError, IncompatibleRecordError) as err:
            err.hints = ["Use `%s` to create a modified copy of the application" % application_copy_cmd,
                         "Use `%s` to delete the experiments." % experiment_delete_cmd]
            raise err
        if not retval:
            rebuild_required = Experiment.rebuild_required()
            if rebuild_required: 
                self.logger.info(rebuild_required)
        return retval       


COMMAND = ApplicationEditCommand(Application, __name__)
