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
from tau import EXIT_SUCCESS
from logger import getLogger
from arguments import getParserFromModel
from commands import executeCommand
from api.application import Application


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Create a new application configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
  %(command)s <application_name> [options]
  %(command)s -h | --help
"""

HELP = """
'%(command)s' page to be written.
"""

def getUsage():
  return USAGE % {'command': COMMAND}

def getHelp():
  return HELP  % {'command': COMMAND}


def main(argv):
  """
  Program entry point
  """
  parser = getParserFromModel(Application,
                              prog=COMMAND,
                              usage=USAGE % {'command': COMMAND}, 
                              description=SHORT_DESCRIPTION) 
  args = parser.parse_args(args=argv)
  LOGGER.debug('Arguments: %s' % args)
  
  Application.create(args.__dict__)
  
  LOGGER.info('Created a new application named %r.' % args.name)
  return executeCommand(['application', 'list'], [args.name])
