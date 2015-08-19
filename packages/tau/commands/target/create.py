#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

from tau import logger, commands, arguments
from tau.error import ConfigurationError
from tau.controller import UniqueAttributeError
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily, CompilerRole
from tau.cf.compiler.mpi import MpiCompilerFamily, MPI_CXX_ROLE, MPI_CC_ROLE, MPI_FC_ROLE
from tau.cf.compiler.installed import InstalledCompiler, InstalledCompilerFamily
from tau.cf.target import host
 

LOGGER = logger.getLogger(__name__)

COMMAND = commands.get_command(__name__)

SHORT_DESCRIPTION = "Create a new target configuration."

USAGE = """
  %(command)s <target_name> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = arguments.getParserFromModel(Target,
                                      prog=COMMAND,
                                      usage=USAGE,
                                      description=SHORT_DESCRIPTION)
group = PARSER.getGroup('compiler arguments')
group.add_argument('--host-compilers',
                   help="select all host compilers automatically from the given family",
                   metavar='<family>',
                   dest='host_family',
                   default=host.preferred_compilers().name,
                   choices=CompilerFamily.family_names())
group = PARSER.getGroup('Message Passing Interface (MPI) arguments')
group.add_argument('--mpi-compilers', 
                   help="select all MPI compilers automatically from the given family",
                   metavar='<family>',
                   dest='mpi_family',
                   default=host.preferred_mpi_compilers().name,
                   choices=MpiCompilerFamily.family_names())


def getUsage():
    return PARSER.format_help()


def getHelp():
    return HELP


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
            family_comps = InstalledCompilerFamily(family_cls.find(family_arg))
        except KeyError:
            PARSER.error("Invalid host compiler family: %s" % family_arg)
        for comp in family_comps:
            LOGGER.debug("args.%s=%r" % (comp.info.role.keyword, comp.absolute_path))
            setattr(args, comp.info.role.keyword, comp.absolute_path)
 
    compiler_keys = set(CompilerRole.keys())
    all_keys = set(args.__dict__.keys())
    given_keys = compiler_keys & all_keys
    missing_keys = compiler_keys - given_keys
    LOGGER.debug("Given compilers: %s" % given_keys)
    LOGGER.debug("Missing compilers: %s" % missing_keys)
     
    compilers = dict([(key, InstalledCompiler(getattr(args, key))) for key in given_keys])
    for key in missing_keys:
        try:
            compilers[key] = host.default_compiler(CompilerRole.find(key))
        except ConfigurationError as err:
            LOGGER.debug(err)

    # Check that all required compilers were found
    for role in CompilerRole.required():
        if role.keyword not in compilers:
            raise ConfigurationError("%s compiler could not be found" % role.language,
                                     "See 'compiler arguments' under `%s --help`" % COMMAND)
            
    # Probe MPI compilers to discover wrapper flags
    for args_attr, wrapped_attr in [('mpi_include_path', 'include_path'), 
                                    ('mpi_library_path', 'library_path'),
                                    ('mpi_libraries', 'libraries')]:
        if not hasattr(args, args_attr):
            probed = set()
            for role in MPI_CC_ROLE, MPI_CXX_ROLE, MPI_FC_ROLE:
                try:
                    comp = compilers[role.keyword]
                except KeyError:
                    LOGGER.debug("Not probing %s: not found" % role)
                else:
                    probed.update(getattr(comp.wrapped(), wrapped_attr))
            setattr(args, args_attr, list(probed))

    return compilers


def main(argv):
    """
    Program entry point
    """
    args = PARSER.parse_args(args=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    compilers = parse_compiler_flags(args)
    LOGGER.debug('Arguments after parsing compiler flags: %s' % args)
    fields = dict(args.__dict__)

    for keyword, comp in compilers.iteritems():
        LOGGER.debug("%s=%s (%s)" % (keyword, comp.absolute_path, comp.info.short_descr))
        record = Compiler.register(comp)
        fields[comp.info.role.keyword] = record.eid

    try:
        Target.create(fields)
    except UniqueAttributeError:
        PARSER.error('A target named %r already exists' % args.name)
    LOGGER.info('Created a new target named %r.' % args.name)
    return commands.executeCommand(['target', 'list'], [args.name])
