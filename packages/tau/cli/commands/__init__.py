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
from tau import PROJECT_URL, TAU_SCRIPT
from tau import cli, logger
from tau.cli import UnknownCommandError, arguments
from tau.cli.commands import build, trial


LOGGER = logger.get_logger(__name__)

COMMAND = os.path.basename(TAU_SCRIPT)

SHORT_DESCRIPTION = "TAU Commander [ %s ]" % PROJECT_URL

HELP = """
'%(command)s' page to be written.

Hints:
 - All parameters can be specified partially e.g. these all do the same thing:
     tau target create my_new_target --device_arch=GPU
     tau targ cre my_new_target --device=GPU
     tau t c my_new_target --d=GPU
""" % {'command': COMMAND}


def parser():
    """Construct a command line argument parser.
    
    Constructing the parser may cause a lot of imports as :py:mod:`tau.cli` is explored.
    To avoid possible circular imports we defer parser creation until afer all
    modules are imported, hence this function.  The parser instance is maintained as
    an attribute of the function, making it something like a C++ function static variable.
    """
    if not hasattr(parser, 'inst'):
        usage_head = "%s [arguments] <subcommand> [options]"  % COMMAND
        usage_foot = """
%(command_descr)s

shortcuts:
  tau <compiler>     Execute a compiler command 
                     - Example: tau gcc *.c -o a.out
                     - Alias for 'tau build <compiler>'
  tau <program>      Gather data from a program
                     - Example: tau ./a.out
                     - Alias for 'tau trial create <program>'
  tau run <program>  Gather data from a program
                     - Example: tau ./a.out
                     - Alias for 'tau trial create <program>'
  tau show           Show data from the most recent trial                    
                     - An alias for 'tau trial show'

See 'tau help <subcommand>' for more information on <subcommand>.
"""  % {'command_descr': cli.get_commands_description()}
        
        parser.inst = arguments.get_parser(prog=COMMAND,
                                     usage=usage_head,
                                     description=SHORT_DESCRIPTION,
                                     epilog=usage_foot)
        parser.inst.add_argument('command',
                            help="See subcommand descriptions below",
                            metavar='<subcommand>')
        parser.inst.add_argument('options',
                            help="Options to be passed to <subcommand>",
                            metavar='[options]',
                            nargs=arguments.REMAINDER)
        parser.inst.add_argument('-v', '--verbose',
                            help="Set logging level to DEBUG",
                            metavar='',
                            const='DEBUG',
                            default='INFO',
                            action='store_const')
    return parser.inst


def main():
    """Subcommand program entry point.
    
    Args:
        argv (:py:class:`list`): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    args = parser().parse_args()
    cmd = args.command
    cmd_args = args.options

    logger.set_log_level(args.verbose)
    LOGGER.debug('Arguments: %s', args)
    LOGGER.debug('Verbosity level: %s', logger.LOG_LEVEL)

    # Try to execute as a TAU command
    try:
        return cli.execute_command([cmd], cmd_args)
    except UnknownCommandError:
        pass

    # Check shortcuts
    shortcut = None
    if build.is_compatible(cmd):
        shortcut = ['build']
        cmd_args = [cmd] + cmd_args
    elif trial.create.is_compatible(cmd):
        shortcut = ['trial', 'create']
        cmd_args = [cmd] + cmd_args
    elif cmd == 'run' and build.is_compatible(cmd):
        shortcut = ['build']
    elif cmd == 'show':
        shortcut = ['trial', 'show']
    if shortcut:
        LOGGER.debug('Trying shortcut: %s', shortcut)
        return cli.execute_command(shortcut, cmd_args)
    else:
        LOGGER.debug('No shortcut found for %r', cmd)

    # Not sure what to do at this point, so advise the user and exit
    LOGGER.info("Unknown command.  Calling 'tau help %s' to get advice.", cmd)
    return cli.execute_command(['help'], [cmd])

# Command line execution
if __name__ == '__main__':
    sys.exit(main())