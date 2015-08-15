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

from operator import attrgetter
from tau import logger, commands, arguments
from tau.error import ConfigurationError
from tau.model.target import Target
from tau.model.compiler import Compiler
from tau.cf.compiler import CompilerFamily


LOGGER = logger.getLogger(__name__)

COMMAND = commands.get_command(__name__)

SHORT_DESCRIPTION = "Modify an existing target configuration."

USAGE = """
  %(command)s <target_name> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = arguments.getParserFromModel(Target,
                                      use_defaults=False,
                                      prog=COMMAND,
                                      usage=USAGE,
                                      description=SHORT_DESCRIPTION)
PARSER.add_argument('--rename',
                    help="Rename the target configuration",
                    metavar='<new_name>', dest='new_name',
                    default=arguments.SUPPRESS)
group = PARSER.getGroup('compiler arguments')
group.add_argument('--compilers',
                   help="Select all compilers automatically from the given family",
                   metavar='<family>',
                   dest='family',
                   default=arguments.SUPPRESS,
                   choices=sorted(CompilerFamily.all()))


def getUsage():
    return PARSER.format_help()


def getHelp():
    return HELP


def parse_compiler_flags(args, compilers):
    """Parses compiler flags out of the command line arguments.
    
    Args:
        args: Argument namespace containing command line arguments
        old_compilers: Dictionary mapping role keyword strings to InstalledCompiler objects.
        
    Returns:
        List of InstalledCompiler objects.
        
    Raises:
        ConfigurationError: Invalid command line arguments specified
    """
    try:
        family = InstalledCompiler.get_family(args.family)
    except AttributeError:
        # args.family missing, but that's OK since args.CC etc. are possibly given instead
        pass
    else:
        compilers = {}
        for comp in family:
            key = comp.role.keyword
            if key not in compilers:
                compilers[key] = comp
        return compilers.values()

    languages = dict([(role.keyword, role.language) for role in CompilerRole.all()])
    compiler_keys = set(languages.keys())
    all_keys = set(args.__dict__.keys())
    given_keys = compiler_keys & all_keys
    LOGGER.debug("Given keys: %s" % given_keys)

    new_compilers = [InstalledCompiler(getattr(args, key)) for key in given_keys]
    for comp in new_compilers:
        compilers[comp.role.keyword] = comp

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
                                     (comp.absolute_path, role.language, comp.role.language),
                                     "See 'compiler arguments' under `%s --help`" % COMMAND)
    return compilers.values()


def main(argv):
    """
    Program entry point
    """
    args = PARSER.parse_args(args=argv)
    LOGGER.debug('Arguments: %s' % args)

    name = args.name
    found = Target.one(keys={'name': name})
    if not found:
        PARSER.error("'%s' is not an target name." % name)

    updates = dict(args.__dict__)
    # Target model doesn't define a 'family' attribute
    try: del updates['family']
    except KeyError: pass

    try:
        name = args.new_name
    except AttributeError:
        pass
    else:
        updates['name'] = name
        del updates['new_name']
    
    old_compilers = dict([(role.keyword, CompilerCommand.one(eid=found[role.keyword]).info())
                          for role in CompilerRole.required()])
    compilers = parse_compiler_flags(args, old_compilers)
    for comp in compilers:
        record = CompilerCommand.from_info(comp)
        updates[comp.role.keyword] = record.eid

    Target.update(updates, eids=found.eid)
    return commands.executeCommand(['target', 'list'], [name])
