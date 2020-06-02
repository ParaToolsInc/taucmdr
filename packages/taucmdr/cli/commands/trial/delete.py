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
"""``trial delete`` subcommand."""

from __future__ import absolute_import
from taucmdr import EXIT_SUCCESS
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import DeleteCommand
from taucmdr.model.trial import Trial
from taucmdr.model.project import Project


class TrialDeleteCommand(DeleteCommand):
    """``trial delete`` subcommand."""

    def _construct_parser(self):
        usage = "%s <trial_number> [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('number',
                            help="Number of the trial to delete",
                            nargs='+',
                            metavar='<trial_number>')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        proj_ctrl = Project.controller()
        trial_ctrl = Trial.controller(proj_ctrl.storage)
        proj = proj_ctrl.selected()
        expr = proj.experiment()
        try:
            numbers = [int(number) for number in args.number]
        except ValueError:
            self.parser.error("Invalid trial number: %s" % args.number)
        fields = [{'experiment': expr.eid, 'number': number} for number in numbers]
        if not any([trial_ctrl.exists(field) for field in fields]):
            self.parser.error("No trial number %s in the current experiment.  "
                              "See `trial list` to see all trial numbers." % number)
        for i, _ in enumerate(fields):
            trial_ctrl.delete(fields[i])
            self.logger.info('Deleted trial %s', numbers[i])
        return EXIT_SUCCESS

COMMAND = TrialDeleteCommand(Trial, __name__, summary_fmt="Delete experiment trials.")
