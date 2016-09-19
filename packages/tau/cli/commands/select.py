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
"""``tau select`` subcommand."""

from tau.error import ConfigurationError, UniqueAttributeError
from tau.cli.commands.experiment.create import ExperimentCreateCommand
from tau.cli.commands.experiment.select import COMMAND as experiment_select_cmd


class SelectCommand(ExperimentCreateCommand):
    """``tau select`` subcommand."""
    
    def _construct_parser(self):
        parser = super(SelectCommand, self)._construct_parser()
        parser.prog = self.command
        parser.usage = "%s [experiment] [target] [application] [measurement] [arguments]" % self.command
        parser.description = self.summary
        return parser
    
    def main(self, argv):
        args = self._parse_args(argv)
        arg_dict = dict(args.__dict__)
        
        if len(arg_dict) == 1:
            name = arg_dict[arg_dict.keys()[0]]
            if isinstance(name, list):
                name = name[0]
            try:
                return experiment_select_cmd.main([name])
            except ConfigurationError as err:
                self.logger.debug(err)

        _, _, _, _, name = self._parse_models_from_args(argv)
        try:
            super(SelectCommand, self).main(argv)
        except UniqueAttributeError as err:
            self.logger.debug(err)
        return experiment_select_cmd.main([name])

COMMAND = SelectCommand(__name__, summary_fmt="Create a new experiment or select an existing experiment.")
