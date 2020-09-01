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
"""``experiment select`` subcommand."""

from __future__ import absolute_import
from taucmdr import EXIT_SUCCESS
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.model.experiment import Experiment


class ExperimentSelectCommand(AbstractCommand):
    """``experiment select`` subcommand."""

    def _construct_parser(self):
        usage = "%s <experiment_name>" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        parser.add_argument('name', help="Experiment name", metavar='<experiment_name>')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        name = args.name
        Experiment.select(name)
        self.logger.info("Selected experiment '%s'.", name)
        rebuild_required = Experiment.rebuild_required()
        if rebuild_required:
            self.logger.info(rebuild_required)
        return EXIT_SUCCESS


COMMAND = ExperimentSelectCommand(__name__, summary_fmt=("Select an experiment.\n"
                                                         "Use `experiment list` to see all experiment configurations."))
