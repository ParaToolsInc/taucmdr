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
from taucmd import UnknownCommandError, HELP_CONTACT
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

_KNOWN_FILES = {'makefile': ("makefile script", "See 'tau make --help' for help building with make")}

_MIME_HINTS = {None: {
                      None: ("unknown file", "See 'tau --help' or contact %s for assistance" % HELP_CONTACT),
                      'gzip': ("compressed file", "Please specify an executable file")
                      },
               'application': {
                               None: ("unknown binary file", "See 'tau --help' or contact %s for assistance" % HELP_CONTACT),
                               'sharedlib': ("shared library", "Please specify an executable file"),
                               'archive': ("archive file", "Please specify an executable file"),
                               'tar': ("archive file", "Please specify an executable file"),
                               'unknown': ("unknown binary file", "See 'tau --help' or contact %s for assistance" % HELP_CONTACT),
                               },
               'text': {
                        None: ("unknown text file", "See 'tau --help' or contact %s for assistance." % HELP_CONTACT),
                        'src': ("source code file", "See 'tau build --help' for help compiling this file"),
                        'hdr': ("source header file", "See 'tau build --help' for help instrumenting this file"),
                        'fortran': ("fortran source code file", "See 'tau build --help' for help compiling this file"),
                        'plain': ("text file", "See 'tau --help' or contact %s for assistance" % HELP_CONTACT),
                        }
               }

def _fuzzy_index(d, k):
    """Return d[key] where ((key in k) == true) or return d[None]"""
    for key in d.iterkeys():
        if key and (key in k):
            return d[key]
    return d[None]

def _guess_filetype(filename):
    """Return a (type, encoding) tuple for a file""" 
    import mimetypes
    mimetypes.init()
    type = mimetypes.guess_type(filename)
    if not type[0]:
        textchars = bytearray([7,8,9,10,12,13,27]) + bytearray(range(0x20, 0x100))
        with open(filename) as f:
            if f.read(1024).translate(None, textchars):
                type = ('application/unknown', None)
            else:
                type = ('text/plain', None)
    return type


def getUsage():
    return USAGE

def getHelp():
    return HELP


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
    
    # Is this a file?
    if not os.path.exists(cmd):
        hint = "A file named %r could not be found.\nCheck the file path and permissions." % cmd
        raise UnknownCommandError(cmd, hint)
    
    
    # Do we recognize the file name?
    try:
        desc, hint = _fuzzy_index(_KNOWN_FILES, cmd.lower())
    except KeyError:
        pass
    else:
        article = 'an' if desc[0] in 'aeiou' else 'a'
        hint = '%r is %s %s.\n%s.' % (cmd, article, desc, hint)
        raise UnknownCommandError(cmd, hint)
    
    # Get the filetype and try to be helpful.
    type, encoding = _guess_filetype(cmd)
    LOGGER.debug("%r has type (%s, %s)" % (cmd, type, encoding))
    if type:
        type, subtype = type.split('/')
        try:
            type_hints = _MIME_HINTS[type]
        except KeyError:
            hint = "TAU doesn't recognize %r.\nSee 'tau --help' and use the appropriate subcommand." % cmd
        else:
            desc, hint = _fuzzy_index(type_hints, subtype)
            article = 'an' if desc[0] in 'aeiou' else 'a'
            hint = '%r is %s %s.\n%s.' % (cmd, article, desc, hint)
        raise UnknownCommandError(cmd, hint)
    else:
        raise UnknownCommandError(cmd)
    
    return EXIT_SUCCESS