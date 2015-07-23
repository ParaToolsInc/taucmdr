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
from tau.model.measurement import Measurement


LOGGER = logger.getLogger(__name__)

COMMAND = commands.get_command(__name__)

SHORT_DESCRIPTION = "Delete measurement configurations."

USAGE = """
  %(command)s <measurement_name> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('name',), {'help': "Name of measurement configuration to delete",
                           'metavar': '<measurement_name>'})]
PARSER = arguments.getParser(_arguments,
                             prog=COMMAND,
                             usage=USAGE % {'command': COMMAND},
                             description=SHORT_DESCRIPTION)


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

    name = args.name
    if not Measurement.exists({'name': name}):
        PARSER.error(
            "'%s' is not a measurement name. Type `tau measurement list` to see valid names." % name)
    Measurement.delete({'name': name})
    LOGGER.info('Deleted measurement %r' % name)

    return commands.executeCommand(['measurement', 'list'], [])
