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

import os
import sys
import taucmd
from taucmd import UnknownCommandError
from docopt import docopt

LOGGER = taucmd.getLogger(__name__)

SHORT_DESCRIPTION = "Get help with a command."

USAGE = """
Usage:
  tau help <command>
  tau -h | --help
  
Use quotes to group commands, e.g. tau help 'project create'.
"""

HELP = """
Prints the help page for a specified command.
"""

def getUsage():
    return USAGE

def getHelp():
    return HELP


def guess_filetype(filename):
    import mimetypes
    mimetypes.init()
    return mimetypes.guess_type(filename)


def main(argv):
    """
    Program entry point
    """
    
    # Parse command line arguments
    args = docopt(USAGE, argv=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    # Try to look up a Tau command's built-in help page
    cmd = args['<command>'].replace(' ', '.')
    cmd_module = 'taucmd.commands.%s' % cmd
    try:
        __import__(cmd_module)
        print '-'*80
        print sys.modules[cmd_module].getUsage()
        print '-'*80
        print '\nHelp:',
        print sys.modules[cmd_module].getHelp()
        print '-'*80
    except ImportError:
        # Not a TAU command, but that's OK
        pass
    
    # Get the filetype and try to be helpful.
    type, encoding = guess_filetype(cmd)
    if type:
        type, subtype = type.split('/')
        if type == 'application':
            hint = "%r is a binary file.  Try 'tau run %r'" % (cmd, cmd)
        elif type == 'text':
            if subtype[-3:] == 'src' or 'fortran' in subtype:
                hint = "%r is a source code file.  Try 'tau make' to build your application." % cmd
            elif subtype[-3:] == 'hdr':
                hint = "%r is a header file.  Try 'tau make' to build your application." % cmd
            else:
                hint = "%r is an unrecognized text file.\nSee 'tau --help' and use the appropriate subcommand." % cmd
        else:
            hint = "TAU can't automatically recognize %r files.\nSee 'tau --help' and use the appropriate subcommand." % type
        raise UnknownCommandError(cmd, hint)
    else:
        raise UnknownCommandError(cmd)
    
    return EXIT_SUCCESS