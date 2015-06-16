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

# TAU modules
import logger
import commands
import controller
import error
import arguments as args
from model.target import Target
from model.compiler import Compiler, KNOWN_FAMILIES

LOGGER = logger.getLogger(__name__)

SHORT_DESCRIPTION = "Create a new target configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s <target_name> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = args.getParserFromModel(Target,
                                 prog=COMMAND,
                                 usage=USAGE,
                                 description=SHORT_DESCRIPTION)
group = PARSER.getGroup('compiler arguments')
group.add_argument('--compilers',
                   help="Select all compilers automatically from the given family",
                   metavar='<family>',
                   dest='family',
                   default=args.SUPPRESS,
                   choices=KNOWN_FAMILIES.keys())


def getUsage():
    return PARSER.format_help()


def getHelp():
    return HELP


def main(argv):
    """
    Program entry point
    """
    args = PARSER.parse_args(args=argv)
    LOGGER.debug('Arguments: %s' % args)

    try:
        family = KNOWN_FAMILIES[args.family]
    except AttributeError:
        # --compilers not specified but that's OK
        pass
    except KeyError:
        raise error.ConfigurationError("Invalid compiler family: %s" % args.family,
                                       "See 'compiler arguments' under `tau target create --help`")
    else:
        LOGGER.debug("Using %s compilers by default" % args.family)
        for comp_info in family:
            setattr(args, comp_info.role, comp_info.command)
        del args.family
    LOGGER.debug('Arguments: %s' % args)

    languages = {'CC': 'C', 'CXX': 'C++', 'FC': 'Fortran'}
    compiler_keys = set(languages.keys())
    all_keys = set(args.__dict__.keys())
    given_keys = compiler_keys & all_keys
    missing_keys = compiler_keys - given_keys
    compilers = {}

    LOGGER.debug("Given keys: %s" % given_keys)
    LOGGER.debug("Missing keys: %s" % missing_keys)

    if not missing_keys:
        LOGGER.debug("All compilers specified by user")
        for key in compiler_keys:
            compilers[key] = Compiler.identify(getattr(args, key))
    elif not given_keys:
        LOGGER.debug("No compilers specified by user, using defaults")
        for key in compiler_keys:
            comp = Compiler.identify(getattr(args, key))
            LOGGER.info("%s compiler not specified, using default: %s" %
                        (comp['language'], comp.absolutePath()))
            compilers[key] = comp
    else:
        LOGGER.debug(
            "Some compilers specified by user, using compiler family defaults")
        siblings = set()
        for key in given_keys:
            comp = Compiler.identify(getattr(args, key))
            siblings |= set(Compiler.getSiblings(comp))
            compilers[key] = comp
        for key in missing_keys:
            for comp in siblings:
                if comp['role'] == key:
                    LOGGER.info("%s compiler not specified, using default: %s" %
                                (comp['language'], comp.absolutePath()))
                    compilers[key] = comp

    # Check that all compilers were found
    for key in compiler_keys:
        if key not in compilers:
            raise error.ConfigurationError("%s compiler could not be found" % languages[key],
                                           "See 'compiler arguments' under `tau target create --help`")

    # Check that all compilers are from the same compiler family
    # This is a TAU requirement.  When this is fixed in TAU we can remove this
    # check
    families = list(set([comp['family'] for comp in compilers.itervalues()]))
    if len(families) != 1:
        raise error.ConfigurationError("Compilers from different families specified",
                                       "TAU requires all compilers to be from the same family, e.g. GNU or Intel")
    LOGGER.info("Using %s compilers" % families[0])

    # Check that each compiler is in the right role
    for role, comp in compilers.iteritems():
        if comp['role'] != role:
            raise error.ConfigurationError("'%s' specified as %s compiler but it is a %s compiler" %
                                           (comp.absolutePath(), languages[
                                            role], comp['language']),
                                           "See 'compiler arguments' under `tau target create --help`")

    # Show compilers to user
    for comp in compilers.itervalues():
        LOGGER.info("  %s compiler: '%s'" %
                    (comp['language'], comp.absolutePath()))

    flags = dict(args.__dict__)
    for key, comp in compilers.iteritems():
        flags[key] = comp.eid
    try:
        Target.create(flags)
    except controller.UniqueAttributeError:
        PARSER.error('A target named %r already exists' % args.name)

    LOGGER.info('Created a new target named %r.' % args.name)
    return commands.executeCommand(['target', 'list'], [args.name])
