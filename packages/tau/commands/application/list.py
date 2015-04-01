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
import arguments as args
import environment as env
from model.application import Application


LOGGER = logger.getLogger(__name__)

SHORT_DESCRIPTION = "List application configurations or show configuration details."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s [application_name] [application_name] ... [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('names',), {'help': "If given, show details for the application with this name",
                            'metavar': 'application_name', 
                            'nargs': '*',
                            'default': args.SUPPRESS}),
              (('-l','--long'), {'help': "display all information about the application",
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
  
  try:
    names = args.names
  except AttributeError:
    found = Application.all()
  else:
    found = []
    for name in names:
      t = Application.withName(name)
      if t:
        found.append(t)
      else:
        PARSER.error("No application configuration named '%s'" % name)

  title = '{:=<{}}'.format('== Applications (%s) ==' % env.USER_PREFIX, 
                           logger.LINE_WIDTH)
  if not found:
    listing = "No applications. See 'tau application create --help'"
  else:
    table = Texttable(logger.LINE_WIDTH)
    cols = [('Name', 'r', None), 
            ('OpenMP', 'c', 'openmp'), 
            ('Pthreads', 'c', 'pthreads'), 
            ('MPI', 'c', 'mpi'),
            ('CUDA', 'c', 'cuda'),
            ('SHMEM', 'c', 'shmem'),
            ('MPC', 'c', 'mpc'),
            ('In Projects', 'l', None)]
    headers = [header for header, _, _ in cols]
    rows = [headers]
    if args.long:
      parts = []
      for t in found:
        t.populate()
        parts.append(pformat(t.data))
      listing = '\n'.join(parts)
    else:
      for t in found:
        t.populate()
        name = t['name']
        projects = ', '.join([p['name'] for p in t['projects']])
        row = [name] + ['Yes' if t.get(attr, None) else '' for _, _, attr in cols if attr] + [projects]
        rows.append(row)
      table.set_cols_align([align for _, align, _ in cols])
      table.add_rows(rows)
      listing = table.draw()
    
  LOGGER.info('\n'.join([title, '', listing, '']))
  return tau.EXIT_SUCCESS

