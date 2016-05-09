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
"""``tau trial export`` subcommand."""

from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.model.project import Project

class TrialExportCommand(AbstractCommand):
    """``tau trial export`` subcommand."""
    
    def construct_parser(self):
        usage = "%s [trial_number] [trial_number] ... [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--export-location', 
                            help="specify location to export profiles",
                            metavar='export_location',
                            default=arguments.SUPPRESS)
        parser.add_argument('--profile-format', 
                            help="specify format of profiles",
                            metavar='profile_format',
                            default=arguments.SUPPRESS)
        parser.add_argument('numbers', 
                            help="show details for specified trials",
                            metavar='trial_number',
                            nargs='*',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
    
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        expr = proj.experiment()
        try:
            str_numbers = args.numbers
        except AttributeError:
            numbers = None
        else:
            numbers = []
            for num in str_numbers:
                try:
                    numbers.append(int(num))
                except ValueError:
                    self.parser.error("Invalid trial number: %s" % num)
        export_location = getattr(args, 'export_location', None)
        profile_format = getattr(args, 'profile_format', None)
        return expr.export(trial_numbers=numbers, export_location=export_location, profile_format=profile_format)

COMMAND = TrialExportCommand(__name__, summary_fmt="Export trial data.")
