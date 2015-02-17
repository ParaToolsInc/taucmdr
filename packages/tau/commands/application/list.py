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

# TAU modules
from tau import USER_PREFIX, EXIT_SUCCESS
from logger import getLogger
from util import pformatList, pformatDict
from error import ConfigurationError
from arguments import getParser, SUPPRESS
from api.application import Application


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "List application configurations or show configuration details."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
Usage:
  %(command)s [application_name] [application_name] ...
  %(command)s -h | --help
"""

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('names',), {'help': "If given, show details for the application with this name",
                           'metavar': 'application_name', 
                           'nargs': '*',
                           'default': SUPPRESS})]
PARSER = getParser(_arguments,
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
  
  try:
    names = args.names
  except AttributeError:
    found = ['%s %s' % (t['name'], t['projects'] if t['projects'] else '')
             for t in Application.search()]
    listing = pformatList(found,
                          empty_msg="No applications. See 'tau application create --help'", 
                          title='Applications (%s)' % USER_PREFIX)
    LOGGER.info(listing)
  else:
    for name in names:
      found = Application.withName(name)
      if not found:
        raise ConfigurationError('There is no application named %r.' % name,
                                 'Try `tau application list` to see all application names.')
      else:
        found.populate()
        listing = pformatDict(found.data, title='Application "%s"' % found['name'])
        LOGGER.info(listing)
  return EXIT_SUCCESS
