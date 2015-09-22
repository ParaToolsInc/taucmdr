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
"""``tau build`` subcommand."""

from tau import logger, cli
from tau.cli import arguments
from tau.error import ConfigurationError
from tau.core.experiment.controller import Experiment
from tau.cf.compiler import CompilerFamily, CompilerInfo
from tau.cf.compiler.mpi import MpiCompilerFamily


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Instrument programs during compilation and/or linking."

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}


def parser():
    """Construct a command line argument parser.
    
    Constructing the parser may cause a lot of imports as :py:mod:`tau.cli` is explored.
    To avoid possible circular imports we defer parser creation until afer all
    modules are imported, hence this function.  The parser instance is maintained as
    an attribute of the function, making it something like a C++ function static variable.
    """
    if not hasattr(parser, 'inst'):
        def _compilers_help():
            family_containers = CompilerFamily, MpiCompilerFamily
            known_compilers = [comp for container in family_containers for family in container.all() for comp in family]
            parts = ['  %s  %s' % ('{:<15}'.format(comp.command), comp.short_descr) for comp in known_compilers]
            return '\n'.join(parts)
        
        usage_head = "%s <command> [arguments]" % COMMAND
        usage_foot = "known compiler commands:\n%s\n" % _compilers_help()
        parser.inst = arguments.get_parser(prog=COMMAND,
                                           usage=usage_head,
                                           description=SHORT_DESCRIPTION,
                                           epilog=usage_foot)
        parser.inst.add_argument('cmd',
                                 help="Compiler or linker command, e.g. 'gcc'",
                                 metavar='<command>')
        parser.inst.add_argument('cmd_args', 
                                 help="Compiler arguments",
                                 metavar='[arguments]',
                                 nargs=arguments.REMAINDER)
    return parser.inst


def is_compatible(cmd):
    """Check if this subcommand can work with the given command.
    
    Args:
        cmd (str): A command from the command line, e.g. sys.argv[1].
        
    Returns:
        bool: True if this subcommand is compatible with `cmd`.
    """
    return cmd in [info.command for info in CompilerInfo.all()]


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (list): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    args = parser().parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    selection = Experiment.get_selected()
    if not selection:
        raise ConfigurationError("Nothing selected.", "See `tau project select`")
    return selection.managed_build(args.cmd, args.cmd_args)
