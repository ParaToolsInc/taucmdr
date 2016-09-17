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
"""``tau experiment select`` subcommand."""

from tau import EXIT_SUCCESS
from tau.error import ConfigurationError
from tau.cli import arguments
from tau.model.experiment import Experiment
from tau.cli.command import AbstractCommand


class ExperimentSelectCommand(AbstractCommand):
    """``tau experiment select`` subcommand."""

    def construct_parser(self):
        usage = "%s experiment" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('experiment', help="Experiment name", metavar='<name>')
        return parser
    
    def main(self, argv):
        args = self.parse_args(argv)
        name = args.experiment

        try:
            changed = Experiment.select(name)
        except ConfigurationError as err:
            self.parser.error(str(err))        
        self.logger.info("Selected experiment '%s'.", name)
        
        if changed:
            parts = ["Application rebuild required:"]
            for attr, change in changed.iteritems():
                old, new = change
                if old is None:
                    parts.append("  - %s is now set to %s" % (attr, new))
                elif new is None:
                    parts.append("  - %s is now unset" % attr)
                else:
                    parts.append("  - %s changed from %s to %s" % (attr, old, new))
            self.logger.info('\n'.join(parts))
        
        return EXIT_SUCCESS


COMMAND = ExperimentSelectCommand(__name__, 
                                  summary_fmt=("Select a project configuration.\n"
                                               "Use `project list` to see all project configurations."))
