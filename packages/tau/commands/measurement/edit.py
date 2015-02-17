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
from tau import EXIT_SUCCESS
from logger import getLogger
from commands import executeCommand
from arguments import getParserFromModel, SUPPRESS
from api.measurement import Measurement


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Modify an existing measurement configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s <measurement_name> [options]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = getParserFromModel(Measurement,
                            use_defaults=False,
                            prog=COMMAND, 
                            usage=USAGE,
                            description=SHORT_DESCRIPTION)
PARSER.add_argument('--rename',
                    help="Rename the measurement configuration",
                    metavar='<new_name>', dest='new_name',
                    default=SUPPRESS)


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
  updates = args.__dict__
  try:
    new_name = args.new_name
  except AttributeError:
    pass
  else:
    updates['name'] = new_name
    del updates['new_name']
  
  Measurement.update(updates, {'name': name})
  
  return executeCommand(['measurement', 'list'], [args.name])
