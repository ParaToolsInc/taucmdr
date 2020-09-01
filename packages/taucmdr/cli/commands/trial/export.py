# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, ParaTools, Inc.
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
"""``trial export`` subcommand."""

from __future__ import absolute_import
import os
from taucmdr import EXIT_SUCCESS
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.model.project import Project


class TrialExportCommand(AbstractCommand):
    """``trial export`` subcommand."""

    def _construct_parser(self):
        usage = "%s [trial_number...] [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--destination',
                            help="location to store exported trial data",
                            metavar='<path>',
                            default=os.getcwd())
        parser.add_argument('trial_numbers',
                            help="show details for specified trials",
                            metavar='trial_number',
                            nargs='*',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        trial_numbers = []
        for num in getattr(args, 'trial_numbers', []):
            try:
                trial_numbers.append(int(num))
            except ValueError:
                self.parser.error("Invalid trial number: %s" % num)
        expr = Project.selected().experiment()
        for trial in expr.trials(trial_numbers):
            trial.export(args.destination)
        return EXIT_SUCCESS


COMMAND = TrialExportCommand(__name__, summary_fmt="Export trial data.")
