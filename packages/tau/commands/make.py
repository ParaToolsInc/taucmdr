# """
# @file
# @author John C. Linford (jlinford@paratools.com)
# @version 1.0
##
# @brief
##
# This file is part of TAU Commander
##
# @section COPYRIGHT
##
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
##
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
##
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
# """

from tau import logger, commands, arguments, util
from tau.error import ConfigurationError
from tau.commands import SCRIPT_COMMAND
from tau.model.experiment import Experiment
from tau.cf.compiler import KNOWN_COMPILERS
from tau.cf.compiler.role import *


LOGGER = logger.getLogger(__name__)

COMMAND = commands.get_command(__name__)


def _compilersHelp():
    parts = ['  %s  %s' % ('{:<15}'.format(comp.command), comp.short_descr)
             for comp in KNOWN_COMPILERS.itervalues()]
    parts.sort()
    return '\n'.join(parts)


SHORT_DESCRIPTION = "Instrument programs during compilation and/or linking with `make`."

USAGE = """
  %(command)s <command> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

USAGE_EPILOG = """
compiler commands:
%(simple_descr)s
%(command_descr)s
""" % {'simple_descr': _compilersHelp(),
       'command_descr': commands.getCommandsHelp(__name__)}


_arguments = [(('cmd_args',), {'help': "`make` arguments",
                               'metavar': '[arguments]',
                               'nargs': arguments.REMAINDER})]
PARSER = arguments.getParser(_arguments,
                             prog=COMMAND,
                             usage=USAGE,
                             description=SHORT_DESCRIPTION,
                             epilog=USAGE_EPILOG)


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

    selection = Experiment.getSelected()
    if not selection:
        raise ConfigurationError("Nothing selected.", "See `tau project select`")
    
    target = selection.populate('target')
    compilers = target.get_compilers()

    env = {}
    cmd_args = [arg 
                for arg in args.cmd_args 
                for role in ALL_ROLES 
                if not arg.startswith(role.keyword)]

    # Fill roles from command line arguments
    missing = list(ALL_ROLES)
    for role in ALL_ROLES:
        keyword = role.keyword
        keyword_assign = "%s=" % keyword
        for arg in args.cmd_args:
            if arg.startswith(keyword_assign):
                given_comp = arg.replace(keyword_assign, "")
                cmd_args.append("%s=%s %s" % (keyword, SCRIPT_COMMAND, given_comp))
                env[keyword] = "%s %s" % (SCRIPT_COMMAND, given_comp)
                missing.remove(role)
    LOGGER.debug("Missing roles after parsing command line args: %s" % missing)
                
    # Fill remaining roles from target compiler information
    for role in missing:
        keyword = role.keyword
        try:
            comp = getattr(compilers, keyword)
        except AttributeError:
            # TODO: Define primary / alternate compiler roles to solve 
            # this problem more generally
            if role in [F77_ROLE, F90_ROLE]:
                comp = getattr(compilers, FC_ROLE.keyword)
            else:
                LOGGER.info("No %s compiler defined, not setting %s" % (role.language, keyword))
                continue
        env[keyword] = "%s %s" % (SCRIPT_COMMAND, comp.absolute_path)
        cmd_args.append("%s=%s %s" % (keyword, SCRIPT_COMMAND, comp.absolute_path))
    
    cmd = ['make'] + cmd_args
    return util.createSubprocess(cmd, env=env)
