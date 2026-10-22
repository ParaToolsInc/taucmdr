#
# Copyright (c) 2026, ParaTools, Inc.
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
"""``system`` subcommand."""

from taucmdr import cli
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand

HELP_PAGE = """
TAU Commander System:
========================================================================

Commands to manage system-level storage. The system level holds shared 
TAU builds and source packages that all users of a system can use.
When installing a shared TAU Commander installation on a cluster, this
can be used to allow users to share sources and installations. The path
for system storage is set in the $TAUCMDR_SYSTEM_PREFIX environment variable.
This could be set in, for example, a module file.

Building TAU configurations in system-level storage:
Enter: `tau system configure --tau-config=minimal`
or:    `tau system configure --tau-config=full`

_________________________________________________________________________
"""


class SystemCommand(AbstractCommand):
    """A command with subcommands that manage system-level storage."""

    def _construct_parser(self):
        usage = "%s <subcommand> [arguments]" % self.command
        epilog = ['', cli.commands_description(self.module_name), '',
                  "See `%s <subcommand> --help` for more information on a subcommand." % self.command]
        parser = arguments.get_parser(prog=self.command, usage=usage,
                                      description=self.summary, epilog='\n'.join(epilog))
        parser.add_argument('subcommand',
                            help="See 'subcommands' below",
                            metavar='<subcommand>')
        parser.add_argument('options',
                            help="Arguments to be passed to <subcommand>",
                            metavar='[arguments]',
                            nargs=arguments.REMAINDER)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        return cli.execute_command([args.subcommand], args.options, self.module_name)


COMMAND = SystemCommand(__name__, group="system", summary_fmt="Manage shared TAU builds and source packages.",
                        help_page_fmt=HELP_PAGE)
