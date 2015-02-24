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
import sys

# TAU modules
from tau import MINIMUM_PYTHON_VERSION, EXIT_FAILURE, PROJECT_URL
from commands import getCommands, commands.getCommandsHelp, commands.executeCommand, UnknownCommandError
from commands import build
from logger import getLogger, setLogLevel, getLogLevel
from arguments import args.getParser, REMAINDER


LOGGER = logger.getLogger(__name__)

SHORT_DESCRIPTION = "TAU Commander [ %s ]" % PROJECT_URL

COMMAND = 'tau'

USAGE = """
  %(command)s <command> [options]
  %(command)s -h | --help
"""  % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.

Hints:
 - All parameters can be specified partially e.g. these all do the same thing:
     tau target create my_new_target --device_arch=GPU
     tau targ cre my_new_target --device=GPU
     tau t c my_new_target --d=GPU
""" % {'command': COMMAND}

USAGE_EPILOG = """
commands:
%(command_descr)s
  <compiler>    A compiler command, e.g. gcc, mpif90, upcc, nvcc, etc. 
                An alias for 'tau build <compiler>'
  <executable>  A program executable, e.g. ./a.out
                An alias for 'tau execute <executable>'

See 'tau help <command>' for more information on <command>.
"""  % {'command_descr': commands.getCommandsHelp()}

_arguments = [ (('command',), {'help': "See 'commands' below",
                               'metavar': '<command>'}),
              (('options',), {'help': "Options to be passed to <command>",
                               'metavar': '[options]',
                               'nargs': REMAINDER}),
              (('-v', '--verbose'), {'help': "Set logging level to DEBUG",
                                     'metavar': '', 
                                     'const': 'DEBUG', 
                                     'default': 'INFO', 
                                     'action': 'store_const'})]
PARSER = args.getParser(_arguments,
                   prog=COMMAND, 
                   usage=USAGE, 
                   description=SHORT_DESCRIPTION,
                   epilog=USAGE_EPILOG)


def getUsage():
  return PARSER.format_help()

def getHelp():
  return HELP


def main():
  """
  Program entry point
  """

  # Check Python version
  if sys.version_info < MINIMUM_PYTHON_VERSION:
    version = '.'.join(map(str, sys.version_info[0:3]))
    expected = '.'.join(map(str, MINIMUM_PYTHON_VERSION))
    LOGGER.error("Your Python version is %s but Python %s or later is required. Please update Python." % 
                 (version, sys.argv[0], expected))

  args = PARSER.parse_args()
  cmd = args.command
  cmd_args = args.options

  
  # Set verbosity level
  setLogLevel(args.verbose)
  LOGGER.debug('Arguments: %s' % args)
  LOGGER.debug('Verbosity level: %s' % getLogLevel())
  
  # Try to execute as a TAU command
  try:
      return commands.executeCommand([cmd], cmd_args)
  except UnknownCommandError:
      pass

  # Check shortcuts
  shortcut = None
  if build.isKnownCompiler(cmd):
    shortcut = 'build'
#   elif show.isKnownFileFormat(cmd):
#     shortcut = 'show'
#   elif run.isExecutable(cmd):
#     shortcut = 'run'
  if shortcut:
    LOGGER.debug('Trying shortcut %r' % shortcut)
    return commands.executeCommand([shortcut], [cmd] + cmd_args)
  else:
    LOGGER.debug('No shortcut found for %r' % cmd)

  # Not sure what to do at this point, so advise the user and exit
  LOGGER.info("Unknown command.  Calling 'tau help %s' to get advice." % cmd)
  return commands.executeCommand(['help'], [cmd])
  
# Command line execution
if __name__ == "__main__":
    exit(main())
