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
"""``experiment list`` subcommand."""

from taucmdr import util, EXIT_SUCCESS
from taucmdr.error import ExperimentSelectionError
from taucmdr.cli.cli_view import ListCommand
from taucmdr.model.project import Project
from taucmdr.model.experiment import Experiment
from taucmdr.cli.commands.experiment.select import COMMAND as select_cmd

def data_size(expr):
    return util.human_size(sum(int(trial.get('data_size', 0)) for trial in expr['trials']))

DASHBOARD_COLUMNS = [{'header': 'Name', 'value': 'name', 'align': 'r'},
                     {'header': 'Trials', 'function': lambda x: len(x['trials'])},
                     {'header': 'Data Size', 'function': data_size},
                     {'header': 'Target', 'function': lambda x: x['target']['name']},
                     {'header': 'Application', 'function': lambda x: x['application']['name']},
                     {'header': 'Measurement', 'function': lambda x: x['measurement']['name']},
                     {'header': 'Record Output', 'value': 'record_output'},
                     {'header': 'TAU Makefile', 'value': 'tau_makefile'}]

class ExperimentListCommand(ListCommand):
    """Base class for the `list` subcommand of command line views."""

    def _construct_parser(self):
        parser = super(ExperimentListCommand, self)._construct_parser()
        parser.add_argument('--current',
                            help="List current trial",
                            default=False,
                            const=True,
                            action="store_const")
        return parser

    def main(self, argv):
        """Command program entry point.

        Args:
            argv (list): Command line arguments.

        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self._parse_args(argv)

        proj = Project.selected()

        if args.current:
            try:
                expr = proj.experiment()
            except ExperimentSelectionError:
                print (util.color_text('No selected experiment: ', 'red') +
                       'Use `%s` to create or select an experiment.' % select_cmd)
            else:
                print expr['name']
            retval = EXIT_SUCCESS
        else:
            retval = super(ExperimentListCommand, self).main(argv)
        return retval

COMMAND = ExperimentListCommand(Experiment, __name__, dashboard_columns=DASHBOARD_COLUMNS, include_storage_flag=False)
