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
"""TAU Commander command line program entry point.

Sets up logging verbosity and launches subcommands.  Avoid doing too much work here.
Instead, process arguments in the appropriate subcommand.
"""

import os
import sys
from tau import TAUCMDR_URL, TAU_SCRIPT
from tau import __version__ as TAU_VERSION
from tau import cli, logger
from tau.cli import UnknownCommandError, arguments
from tau.cli.command import AbstractCommand
from tau.cli.commands.build import COMMAND as build_command
from tau.cli.commands.trial.create import COMMAND as trial_create_command

LOGGER = logger.get_logger(__name__)

SUMMARY_FMT = "TAU Commander [ %s ]" % TAUCMDR_URL

HELP_PAGE_FMT = """'%(command)s' page to be written.

Hints:
 - All parameters can be specified partially e.g. these all do the same thing:
     tau target create my_new_target --device_arch=GPU
     tau targ cre my_new_target --device=GPU
     tau t c my_new_target --d=GPU"""


class MainCommand(AbstractCommand):
    """Main entry point to the command line interface."""

    def __init__(self):
        super(MainCommand, self).__init__(__name__, summary_fmt=SUMMARY_FMT, help_page_fmt=HELP_PAGE_FMT)
        self.command = os.path.basename(TAU_SCRIPT)
    
    def construct_parser(self):
        usage = "%s [arguments] <subcommand> [options]"  % self.command
        epilog = ["", cli.commands_description(), "",
                  "shortcuts:",
                  "  %(command)s <compiler>  Execute a compiler command", 
                  "                  - Example: %(command)s gcc *.c -o a.out",
                  "                  - Alias for '%(command)s build <compiler>'",
                  "  %(command)s <program>   Gather data from a program",
                  "                  - Example: %(command)s ./a.out",
                  "                  - Alias for '%(command)s trial create <program>'",
                  "  %(command)s show        Show data from the most recent trial",
                  "                  - An alias for '%(command)s trial show'",
                  "",
                  "See '%(command)s help <subcommand>' for more information on <subcommand>."]
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage,
                                      description=self.summary,
                                      epilog='\n'.join(epilog) % {'command': self.command})
        parser.add_argument('command',
                            help="See subcommand descriptions below",
                            metavar='<subcommand>')
        parser.add_argument('options',
                            help="Options to be passed to <subcommand>",
                            metavar='[options]',
                            nargs=arguments.REMAINDER)
        parser.add_argument('-V', '--version', action='version', version=self._version())
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-v', '--verbose',
                           help="show debugging messages",
                           const='DEBUG',
                           default=arguments.SUPPRESS,
                           action='store_const')
        group.add_argument('-q', '--quiet',
                           help="suppress all output except error messages",
                           const='ERROR',
                           default=arguments.SUPPRESS,
                           action='store_const')        
        return parser
    
    def _version(self):
        import platform
        import socket
        from datetime import datetime
        fmt = ("Version        : %(version)s\n"
               "Timestamp      : %(timestamp)s\n"
               "Hostname       : %(hostname)s\n"
               "Platform       : %(platform)s\n"
               "Working Dir.   : %(cwd)s\n"
               "Terminal Size  : %(termsize)s\n"
               "Frozen         : %(frozen)s\n"
               "Python         : %(python)s\n"
               "Python Version : %(pyversion)s\n"
               "Python Impl.   : %(pyimpl)s\n"
               "PYTHONPATH     : %(pythonpath)s\n")
        data = {"version": TAU_VERSION,
                "timestamp": str(datetime.now()),
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "cwd": os.getcwd(),
                "termsize": 'x'.join([str(dim) for dim in logger.TERM_SIZE]),
                "frozen": getattr(sys, 'frozen', False),
                "python": sys.executable,
                "pyversion": platform.python_version(),
                "pyimpl": platform.python_implementation(),
                "pythonpath": os.pathsep.join(sys.path)}
        return fmt % data
        
    def main(self, argv):
        """Program entry point.

        Args:
            argv (list): Command line arguments.

        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self.parser.parse_args(args=argv)

        cmd = args.command
        cmd_args = args.options

        log_level = getattr(args, 'verbose', getattr(args, 'quiet', logger.LOG_LEVEL))
        logger.set_log_level(log_level)
        LOGGER.debug('Arguments: %s', args)
        LOGGER.debug('Verbosity level: %s', logger.LOG_LEVEL)

        # Try to execute as a TAU command
        try:
            return cli.execute_command([cmd], cmd_args)
        except UnknownCommandError:
            pass

        # Check shortcuts
        shortcut = None
        if build_command.is_compatible(cmd):
            shortcut = ['build']
            cmd_args = [cmd] + cmd_args
        elif trial_create_command.is_compatible(cmd):
            shortcut = ['trial', 'create']
            cmd_args = [cmd] + cmd_args
        elif cmd == 'show':
            shortcut = ['trial', 'show']
        if shortcut:
            LOGGER.debug('Trying shortcut: %s', shortcut)
            return cli.execute_command(shortcut, cmd_args)
        else:
            LOGGER.debug('No shortcut found for %r', cmd)
     
        # Not sure what to do at this point, so advise the user and exit
        LOGGER.info("Unknown command.  Calling `tau help %s` to get advice.", cmd)
        return cli.execute_command(['help'], [cmd])


COMMAND = MainCommand()

if __name__ == '__main__':
    sys.exit(COMMAND.main(sys.argv[1:]))
