"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys
import tau
from tau import commands
from tau.docopt import docopt

LOGGER = tau.getLogger(__name__)

SHORT_DESCRIPTION = "Create and manage TAU projects."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s [<subcommand>] [<args>...]
  %(command)s -h | --help

Subcommands:
%(command_descr)s
"""

HELP = """
'%(command)s' help page to be written.
""" % {'command': COMMAND}

def getUsage():
    return USAGE % {'command': COMMAND,
                    'command_descr': commands.getSubcommands(__name__)}

def getHelp():
    return HELP

def main(argv):
    """
    Program entry point
    """

    # Parse command line arguments
    usage = getUsage()
    args = docopt(usage, argv=argv, options_first=True)
    LOGGER.debug('Arguments: %s' % args)
    
    cmd = args['<subcommand>']
    cmd_args = args['<args>']
    if not cmd:
        # Show projects if no subcommand given
        cmd = 'list'

    # Check for -h | --help
    idx = cmd.find('-h')
    if (idx == 0) or (idx == 1):
        print usage
        return 0

    # Execute as a tau command
    return commands.executeCommand(['project', cmd], cmd_args)
