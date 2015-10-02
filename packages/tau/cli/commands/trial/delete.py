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
"""``tau trial delete`` subcommand."""

from tau import EXIT_SUCCESS
from tau.error import ConfigurationError
from tau.cli import arguments
from tau.cli.cli_view import DeleteCommand
from tau.model.trial import Trial
from tau.model.project import Project


class TrialDeleteCommand(DeleteCommand):
    """``tau trial delete`` subcommand."""

    def construct_parser(self):
        usage = "%s <trial_number> [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('number', 
                            help="Number of the trial to delete",
                            metavar='<trial_number>')
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
    
        proj_ctrl = Project.controller()
        trial_ctrl = Trial.controller(proj_ctrl.storage)

        proj = proj_ctrl.selected()
        if not proj:
            from tau.cli.commands.select import COMMAND as select_command
            raise ConfigurationError("No project selected.", "Try `%s`" % select_command.command)
        expr = proj.populate('selected')
    
        try:
            number = int(args.number)
        except ValueError:
            self.parser.error("Invalid trial number: %s" % args.number)
        fields = {'experiment': expr.eid, 'number': number}
        if not trial_ctrl.exists(fields):
            self.parser.error("No trial number %s in the current experiment.  "
                              "See `tau trial list` to see all trial numbers." % number)
        trial_ctrl.delete(fields)
        self.logger.info('Deleted trial %s', number)
        return EXIT_SUCCESS

COMMAND = TrialDeleteCommand(Trial, __name__, summary_fmt="Delete experiment trials.")
