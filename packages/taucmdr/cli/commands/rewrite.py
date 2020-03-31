# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, ParaTools, Inc.
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
"""``rewrite`` subcommand."""

import os
from taucmdr import EXIT_SUCCESS
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cf.compiler import Knowledgebase
from taucmdr.error import ConfigurationError
from taucmdr.model.project import Project

class RewriteCommand(AbstractCommand):
    """``rewrite`` subcommand."""


    def _construct_parser(self):
        usage_head = "%s --dynist|--maqao|--pebil <executable> <inst-file>" %self.command
        parser = arguments.get_parser(prog=self.command, usage=usage_head, description = self.summary)
        parser.add_argument('--dyninst',
                            help="Use dyninst to rewrite executable",
                            const=True, default=False, action='store_const')
        parser.add_argument('--maqao',
                            help="Use maqao to rewrite executable",
                            const=True, default=False, action='store_const')
        parser.add_argument('--pebil',
                            help="Use pebil to rewrite executable",
                            const=True, default=False, action='store_const')
        parser.add_argument('executable',
                            help="Executable to be rewritten",
                            metavar='<executable>')
        parser.add_argument('inst_file',
                            help="Instrumented output file",
                            metavar='<inst_file>')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        rewrite_packages = []
        if args.maqao:
            rewrite_packages.append('maqao')
        if args.dyninst:
            rewrite_packages.append('dyninst')
        if args.pebil:
            rewrite_packages.append('pebil')
        if len(rewrite_packages) == 0:
            raise ConfigurationError('Instrumentation package not specified.', 'Specify one of --dyninst, --maqao, or --pebil.')
        elif len(rewrite_packages) > 1:
            raise ConfigurationError('Only one instrumentation paclages should be specified.')
        expr = Project.selected().experiment()
        return expr.managed_rewrite(rewrite_packages[0], args.executable, args.inst_file)

COMMAND = RewriteCommand(__name__, summary_fmt="Rewrite")
