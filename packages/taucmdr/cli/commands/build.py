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
"""``build`` subcommand."""

import os
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cf.compiler import Knowledgebase
from taucmdr.model.project import Project


class BuildCommand(AbstractCommand):
    """``build`` subcommand."""
    
    @staticmethod
    def is_compatible(cmd):
        """Check if this subcommand can work with the given command.
        
        Args:
            cmd (str): A command from the command line, e.g. sys.argv[1].

        Returns:
            bool: True if this subcommand is compatible with `cmd`.
        """
        return os.path.basename(cmd) in [info.command for info in Knowledgebase.all_compilers()]

    def _construct_parser(self):
        parts = ['  %s  %s' % ('{:<15}'.format(comp.command), comp.short_descr) 
                 for comp in Knowledgebase.all_compilers()]
        epilog = "known compiler commands and their roles:\n%s\n" % '\n'.join(sorted(parts))
        usage = "%s <command> [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary, epilog=epilog)
        parser.add_argument('cmd',
                            help="Compiler or linker command, e.g. 'gcc'",
                            metavar='<command>')
        parser.add_argument('cmd_args', 
                            help="Compiler arguments",
                            metavar='[arguments]',
                            nargs=arguments.REMAINDER)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        expr = proj.experiment()
        return expr.managed_build(args.cmd, args.cmd_args)


COMMAND = BuildCommand(__name__, summary_fmt="Instrument programs during compilation and/or linking.")
