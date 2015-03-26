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

# System modules
import os
import sys

# TAU modules
import tau
import logger
import commands
import arguments as args


LOGGER = logger.getLogger(__name__)

_name_parts = __name__.split('.')[2:]
COMMAND = ' '.join(['tau'] + _name_parts)

SHORT_DESCRIPTION = "Show help for a command."

USAGE = """
  %(command)s {<command>|<file_name>}
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
Show help for a command line or file.
"""

_arguments = [ (('command',), {'help': "A TAU command, system command, or file",
                               'metavar': '{<command>|<file_name>}',
                               'nargs': args.REMAINDER})]
PARSER = args.getParser(_arguments,
                        prog=COMMAND, 
                        usage=USAGE, 
                        description=SHORT_DESCRIPTION)


_GENERIC_HELP = "See 'tau --help' or contact %s for assistance" % tau.HELP_CONTACT

_KNOWN_FILES = {'makefile': ("makefile script", 
                             "See 'tau make --help' for help building with make"),
                'a.out': ("binary executable", 
                          "See 'tau run --help' for help with profiling this program"),
                '.exe': ("binary executable", 
                         "See 'tau run --help' for help with profiling this program")}

_MIME_HINTS = {None: {None: ("unknown file", _GENERIC_HELP),
                      'gzip': ("compressed file", "Please specify an executable file")},
               'application': {None: ("unknown binary file", _GENERIC_HELP),
                               'sharedlib': ("shared library", "Please specify an executable file"),
                               'archive': ("archive file", "Please specify an executable file"),
                               'tar': ("archive file", "Please specify an executable file"),
                               'unknown': ("unknown binary file", _GENERIC_HELP)},
               'text': {None: ("unknown text file", _GENERIC_HELP),
                        'src': ("source code file", "See 'tau build --help' for help compiling this file"),
                        'hdr': ("source header file", "See 'tau build --help' for help instrumenting this file"),
                        'fortran': ("fortran source code file", "See 'tau build --help' for help compiling this file"),
                        'plain': ("text file", _GENERIC_HELP)}
               }

def _fuzzy_index(d, k):
    """
    Return d[key] where ((key in k) == true) or return d[None]
    """
    for key in d.iterkeys():
        if key and (key in k):
            return d[key]
    return d[None]


def _guess_filetype(filename):
    """
    Return a (type, encoding) tuple for a file
    """ 
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
  return PARSER.format_help() 


def getHelp():
  return HELP


def exitWithHelp(module_name):
  __import__(module_name)
  module = sys.modules[module_name]
  LOGGER.info("""
%(bar)s

%(usage)s

%(bar)s

%(help)s

%(bar)s""" % {'bar': '-'*80, 
              'usage': module.getUsage(),
              'help': module.getHelp()})
  return tau.EXIT_SUCCESS


def main(argv):
  """
  Program entry point
  """
  args = PARSER.parse_args(args=argv)
  LOGGER.debug('Arguments: %s' % args)
  
  if not args.command:
    return exitWithHelp('__main__')
    
  # Try to look up a Tau command's built-in help page
  cmd = '.'.join(args.command)
  try:
    return exitWithHelp('commands.%s' % cmd)
  except ImportError:
    pass

  # Is this a file?
  if os.path.exists(cmd): 
    # Do we recognize the file name?
    try:
      desc, hint = _fuzzy_index(_KNOWN_FILES, cmd.lower())
    except KeyError:
      pass
    else:
      article = 'an' if desc[0] in 'aeiou' else 'a'
      hint = '%r is %s %s.\n%s.' % (cmd, article, desc, hint)
      raise commands.UnknownCommandError(cmd, hint)
    
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
      raise commands.UnknownCommandError(cmd, hint)
    else:
      raise commands.UnknownCommandError(cmd)
  
  # Not a file, not a command, let's just show TAU usage and exit
  return exitWithHelp('__main__')
