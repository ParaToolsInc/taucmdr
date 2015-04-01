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
from texttable import Texttable
from pprint import pformat

# TAU modules
import tau
import logger
import commands
import error
import arguments as args
import environment as env
from model.experiment import Experiment
from model.trial import Trial


LOGGER = logger.getLogger(__name__)

SHORT_DESCRIPTION = "List experiment trials."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s [trial_number] [trial_number] ... [arguments]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('numbers',), {'help': "If given, show details for trial with this number",
                              'metavar': 'trial_number', 
                              'nargs': '*',
                              'default': args.SUPPRESS}),
              (('-l','--long'), {'help': "Display all information about the trial",
                                 'action': 'store_true',
                                 'default': False})]
PARSER = args.getParser(_arguments,
                        prog=COMMAND, 
                        usage=USAGE, 
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
  
  selection = Experiment.getSelected()
  if not selection:
    raise error.ConfigurationError("No experiment configured.", "See `tau project select`") 
  
  try:
    numbers = args.numbers
  except AttributeError:
    found = Trial.search({'experiment': selection.eid})
  else:
    found = []
    for num in number:
      t = Trial.search({'number': num})
      if t:
        found.append(t)
      else:
        PARSER.error("No trial number %d in the current experiment" % num)

  title = '{:=<{}}'.format('== Trials of %s ==' % selection.name(), 
                           logger.LINE_WIDTH)
  if not found:
    listing = "No trials. Use 'tau <command>' or 'tau trial create <command>' to create a new trial"
  else:
    table = Texttable(logger.LINE_WIDTH)
    cols = [('Number', 'c', 'number'),
            ('Data Size', 'c', 'data_size'), 
            ('Command', 'l', 'command'), 
            ('In Directory', 'l', 'cwd'),
            ('Began at', 'c', 'begin_time'),
            ('Ended at', 'c', 'end_time'),
            ('Return Code', 'c', 'return_code')]
    headers = [header for header, _, _ in cols]
    rows = [headers]
    if args.long:
      parts = []
      for t in found:
        parts.append(pformat(t.data))
      listing = '\n'.join(parts)
    else:
      for t in found:
        row = [t.get(attr, '') for _, _, attr in cols if attr]
        rows.append(row)
      table.set_cols_align([align for _, align, _ in cols])
      table.add_rows(rows)
      listing = table.draw()
    
  LOGGER.info('\n'.join([title, '', listing, '']))
  return tau.EXIT_SUCCESS

