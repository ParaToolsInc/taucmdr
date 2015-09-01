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
"""``tau target edit`` subcommand."""

from tau import logger, cli
from tau.cli import arguments
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily
from tau.cf.compiler.mpi import MpiCompilerFamily


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Modify an existing target configuration."

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
        usage_head = "%s <target_name> [arguments]" % COMMAND
        parser.inst = arguments.get_parser_from_model(Target,
                                                      use_defaults=False,
                                                      prog=COMMAND,
                                                      usage=usage_head,
                                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('--rename',
                                 help="Rename the target configuration",
                                 metavar='<new_name>', dest='new_name',
                                 default=arguments.SUPPRESS)
        group = parser.inst.get_group('compiler arguments')
        group.add_argument('--host-compilers',
                           help="select all host compilers automatically from the given family",
                           metavar='<family>',
                           dest='host_family',
                           default=arguments.SUPPRESS,
                           choices=CompilerFamily.family_names())
        group = parser.inst.get_group('Message Passing Interface (MPI) arguments')
        group.add_argument('--mpi-compilers', 
                           help="select all MPI compilers automatically from the given family",
                           metavar='<family>',
                           dest='mpi_family',
                           default=arguments.SUPPRESS,
                           choices=MpiCompilerFamily.family_names())
    return parser.inst


def parse_compiler_flags(args):
    """Parses host compiler flags out of the command line arguments.
     
    Args:
        args: Argument namespace containing command line arguments
         
    Returns:
        Dictionary of installed compilers by role keyword string.
         
    Raises:
        ConfigurationError: Invalid command line arguments specified
    """
    for family_attr, family_cls in [('host_family', CompilerFamily), ('mpi_family', MpiCompilerFamily)]:
        try:
            family_arg = getattr(args, family_attr)
        except AttributeError as err:
            # User didn't specify that argument, but that's OK
            LOGGER.debug(err)
            continue
        else:
            delattr(args, family_attr)
        try:
            family_comps = InstalledCompilerFamily(family_cls(family_arg))
        except KeyError:
            parser().error("Invalid compiler family: %s" % family_arg)
        for comp in family_comps:
            LOGGER.debug("args.%s=%r", comp.info.role.keyword, comp.absolute_path)
            setattr(args, comp.info.role.keyword, comp.absolute_path)
 
    compiler_keys = set(CompilerRole.keys())
    all_keys = set(args.__dict__.keys())
    given_keys = compiler_keys & all_keys
    LOGGER.debug("Given compilers: %s", given_keys)
     
    return dict([(key, InstalledCompiler(getattr(args, key))) for key in given_keys])


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (list): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    args = parser().parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    name = args.name
    if not Target.exists({'name': name}):
        parser().error("'%s' is not an target name.  Type `%s` to see valid names." % (name, COMMAND))

    compilers = parse_compiler_flags(args)
    LOGGER.debug('Arguments after parsing compiler flags: %s', args)
    fields = dict(args.__dict__)

    for keyword, comp in compilers.iteritems():
        LOGGER.debug("%s=%s (%s)", keyword, comp.absolute_path, comp.info.short_descr)
        record = Compiler.register(comp)
        fields[comp.info.role.keyword] = record.eid

    try:
        new_name = args.new_name
    except AttributeError:
        pass
    else:
        fields['name'] = new_name
        del fields['new_name']
    
    Target.update(fields, {'name': name})
    return cli.execute_command(['target', 'list'], [name])
