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

import os
from tau import logger, commands, arguments 
from tau.error import ConfigurationError
from tau.controller import UniqueAttributeError
from tau.model.target import Target
from tau.model.compiler_command import CompilerCommand
from tau.cf.compiler import KNOWN_FAMILIES, KNOWN_ROLES, MPI_FAMILY_NAME
from tau.cf.compiler.installed import InstalledCompiler
from tau.cf.compiler.role import REQUIRED_ROLES
from cf.compiler.role import CC_ROLE

 

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
group.add_argument('--compilers',
                   help="Select all compilers automatically from the given family",
                   metavar='<family>',
                   dest='family',
                   default=arguments.SUPPRESS,
                   choices=KNOWN_FAMILIES.keys())


def getUsage():
    return PARSER.format_help()


def getHelp():
    return HELP


def parse_compiler_flags(args):
    """Parses compiler flags out of the command line arguments.
    
    Args:
        args: Argument namespace containing command line arguments
        
    Returns:
        Dictionary of installed compilers by role keyword string.
        
    Raises:
        ConfigurationError: Invalid command line arguments specified
    """
    try:
        family = InstalledCompiler.get_family(args.family)
    except AttributeError as err:
        # args.family missing, but that's OK since args.CC etc. are possibly given instead
        LOGGER.debug(err)
    else:
        compilers = {}
        for comp in family:
            key = comp.role.keyword
            if key not in compilers:
                compilers[key] = comp
        return compilers

    languages = dict([(role.keyword, role.language) for role in REQUIRED_ROLES])
    compiler_keys = set(languages.keys())
    all_keys = set(args.__dict__.keys())
    given_keys = compiler_keys & all_keys
    missing_keys = compiler_keys - given_keys
    LOGGER.debug("Given keys: %s" % given_keys)
    LOGGER.debug("Missing keys: %s" % missing_keys)

    compilers = {}
    if not given_keys:
        LOGGER.debug("No compilers specified by user, using defaults")
        for key in compiler_keys:
            comp = InstalledCompiler.get_default(KNOWN_ROLES[key])
            LOGGER.debug("%s compiler not specified, defaulting to: %s" %
                         (comp.role.language, comp.absolute_path))
            compilers[key] = comp
    else:
        for key in given_keys:
            compilers[key] = InstalledCompiler(getattr(args, key))
        siblings = compilers.itervalues().next().get_siblings()
        for comp in siblings:
            key = comp.role.keyword
            if key not in compilers:
                compilers[key] = comp

    # Check that all compilers were found
    for key in compiler_keys:
        if key not in compilers:
            raise ConfigurationError("%s compiler could not be found" % languages[key],
                                     "See 'compiler arguments' under `%s --help`" % COMMAND)

    # Check that all compilers are from the same compiler family
    # TODO: This is a TAU requirement.  When this is fixed in TAU we can remove this check
    families = list(set([comp.family for comp in compilers.itervalues()]))
    if len(families) != 1:
        raise ConfigurationError("Compilers from different families specified: %s" % families,
                                 "TAU requires all compilers to be from the same family")

    # Check that each compiler is in the right role
    for role, comp in compilers.iteritems():
        if comp.role.keyword != role:
            raise ConfigurationError("'%s' specified as %s compiler but it is a %s compiler" %
                                     (comp.absolute_path, languages[role], comp.role.language),
                                     "See 'compiler arguments' under `%s --help`" % COMMAND)
    return compilers


def main(argv):
    """
    Program entry point
    """
    args = PARSER.parse_args(args=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    flags = dict(args.__dict__)
    # Target model doesn't define a 'family' attribute
    try: del flags['family']
    except KeyError: pass
    
    compilers = parse_compiler_flags(args)
    if compilers[CC_ROLE.keyword].family == MPI_FAMILY_NAME:
        mpi_include_path = set()
        mpi_library_path = set()
        mpi_compiler_flags = set()
        mpi_linker_flags = set()
        for comp in compilers.itervalues():
            mpi_include_path |= set(comp.wrapped.include_path)
            mpi_library_path |= set(comp.wrapped.library_path)
            mpi_compiler_flags |= set(comp.wrapped.compiler_flags)
            mpi_linker_flags |= set(comp.wrapped.linker_flags)
        if 'mpi_include_path' not in flags:
            flags['mpi_include_path'] = list(mpi_include_path) 
            LOGGER.info("Autodetected MPI include path: %s" % os.pathsep.join(mpi_include_path))
        if 'mpi_library_path' not in flags:
            flags['mpi_library_path'] = list(mpi_library_path)
            LOGGER.info("Autodetected MPI library path: %s" % os.pathsep.join(mpi_library_path))
        if 'mpi_compiler_flags' not in flags:
            flags['mpi_compiler_flags'] = list(mpi_compiler_flags)
            LOGGER.info("Autodetected MPI compiler flags: %s" % ' '.join(mpi_compiler_flags))
        if 'mpi_linker_flags' not in flags:
            flags['mpi_linker_flags'] = list(mpi_linker_flags)
            LOGGER.info("Autodetected MPI linker flags: %s" % ' '.join(mpi_linker_flags))
    
    for role, comp in compilers.iteritems():
        LOGGER.debug("%s=%s (%s)" % (role, comp.absolute_path, comp.short_descr))
        record = CompilerCommand.from_info(comp)
        flags[comp.role.keyword] = record.eid
        
    try:
        Target.create(flags)
    except UniqueAttributeError:
        PARSER.error('A target named %r already exists' % args.name)
    LOGGER.info('Created a new target named %r.' % args.name)
    return commands.executeCommand(['target', 'list'], [args.name])
