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
"""``trial show`` subcommand."""

import os
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.model.project import Project
from taucmdr.cf.software.tau_installation import TauInstallation, PROFILE_ANALYSIS_TOOLS, TRACE_ANALYSIS_TOOLS
import six


class TrialShowCommand(AbstractCommand):
    """``trial show`` subcommand."""

    def _construct_parser(self):
        usage = "%s [trial_number... | data_file...] [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('--profile-tools',
                            help="specify profile analysis tools",
                            metavar='<tool>',
                            nargs='+',
                            choices=PROFILE_ANALYSIS_TOOLS,
                            default=arguments.SUPPRESS)
        parser.add_argument('--trace-tool',
                            help="specify trace analysis tool",
                            metavar='<tool>',
                            nargs='+',
                            choices=TRACE_ANALYSIS_TOOLS,
                            default=arguments.SUPPRESS)
        parser.add_argument('trial_numbers',
                            help="Display data from trials",
                            metavar='<trial_number>',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.add_argument('data_files',
                            help="Display data from files",
                            metavar='<data_file>',
                            nargs='*',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        profile_tools = getattr(args, 'profile_tools', None)
        trace_tools = getattr(args, 'trace_tools', None)
        data_files = []
        trial_numbers = []
        for num in getattr(args, 'trial_numbers', []) + getattr(args, 'data_files', []):
            if os.path.exists(num):
                data_files.append(num)
            else:
                try:
                    trial_numbers.append(int(num))
                except ValueError:
                    self.parser.error("Invalid trial number: %s" % num)

        tau = TauInstallation.get_minimal()
        dataset = {}
        if not (data_files or trial_numbers):
            expr = Project.selected().experiment()
            for fmt, path in expr.trials()[0].get_data_files().items():
                dataset[fmt] = [path]
        elif trial_numbers:
            expr = Project.selected().experiment()
            for trial in expr.trials(trial_numbers):
                for fmt, path in trial.get_data_files().items():
                    dataset.setdefault(fmt, []).append(path)
        for path in data_files:
            fmt = tau.get_data_format(path)
            dataset.setdefault(fmt, []).append(path)
        return tau.show_data_files(dataset, profile_tools, trace_tools)


COMMAND = TrialShowCommand(__name__, summary_fmt="Display trial data from a file path or trial number.")
