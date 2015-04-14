#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
#This file is part of TAU Commander
#
#@section COPYRIGHT
#
#Copyright (c) 2015, ParaTools, Inc.
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without 
#modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice, 
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice, 
#     this list of conditions and the following disclaimer in the documentation 
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
#     be used to endorse or promote products derived from this software without 
#     specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#"""

# TAU modules
import logger
import commands
import arguments as args


LOGGER = logger.getLogger(__name__)

_name_parts = __name__.split('.')[1:]
COMMAND = ' '.join(['tau'] + _name_parts)

SHORT_DESCRIPTION = "Create and manage application configurations."

GROUP = "configuration"

USAGE = """
  %(command)s <subcommand> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

USAGE_EPILOG = """
%(command_descr)s

See '%(command)s <subcommand> --help' for more information on <subcommand>.
""" % {'command': COMMAND,
       'command_descr': commands.getCommandsHelp(__name__)}



_arguments = [ (('subcommand',), {'help': "See 'subcommands' below",
                                  'metavar': '<subcommand>'}),
               (('options',), {'help': "Arguments to be passed to <subcommand>",
                               'metavar': '[arguments]',
                               'nargs': args.REMAINDER})]
PARSER = args.getParser(_arguments,
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
  
  subcommand = args.subcommand
  options = args.options
  return commands.executeCommand(_name_parts + [subcommand], options)
