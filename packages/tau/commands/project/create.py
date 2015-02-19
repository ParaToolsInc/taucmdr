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
from arguments import getParser, SUPPRESS
from commands import executeCommand
from api.project import Project
from api.target import Target
from api.application import Application
from api.measurement import Measurement
from tau.arguments import getParserFromModel


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Create a new project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s <project_name> [options] [targets] [applications] [measurements]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = getParserFromModel(Project,
                            prog=COMMAND, 
                            usage=USAGE, 
                            description=SHORT_DESCRIPTION)
PARSER.add_argument('impl_targets', 
                    help="Target configurations in this project",
                    metavar='[targets]', 
                    nargs='*',
                    default=SUPPRESS)
PARSER.add_argument('impl_applications', 
                    help="Application configurations in this project",
                    metavar='[applications]', 
                    nargs='*', 
                    default=SUPPRESS)
PARSER.add_argument('impl_measurements', 
                    help="Measurement configurations in this project",
                    metavar='[measurements]',
                    nargs='*',
                    default=SUPPRESS)  
PARSER.add_argument('--add-targets',
                    help = "Target configurations in this project",
                    metavar = 't',
                    nargs = '+',
                    dest = 'targets',
                    default = SUPPRESS)
PARSER.add_argument('--add-applications', 
                    help = "Application configurations in this project",
                    metavar = 'a',
                    nargs = '+',
                    dest = 'applications',
                    default = SUPPRESS)
PARSER.add_argument('--add-measurements', 
                    help = "Measurement configurations in this project",
                    metavar = 'm',
                    nargs = '+',
                    dest = 'measurements',
                    default = SUPPRESS)


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
  
  targets = set()
  applications = set()
  measurements = set()
  
  for attr, model, dest in [('targets', Target, targets), 
                            ('applications', Application, applications), 
                            ('measurements', Measurement, measurements)]:
    for name in getattr(args, attr, []):
      found = model.withName(name)
      if not found:
        PARSER.error('There is no %s named %r' % (model.model_name, name))
      dest.add(found.eid)
  
    for name in getattr(args, 'impl_'+attr, []):
      t = Target.withName(name)
      a = Application.withName(name)
      m = Measurement.withName(name)
      tam = set([t,a,m]) - set([None])
      if len(tam) > 1:
        PARSER.error('%r is ambiguous, please use --targets, --applications,'
                     ' or --measurements to specify configuration type' % name)
      elif len(tam) == 0:
        PARSER.error('%r is not a target, application, or measurement' % name)
      elif t:
        targets.add(t.eid)
      elif a:
        applications.add(a.eid)
      elif m:
        measurements.add(m.eid)
        
    try:
      delattr(args, 'impl_'+attr)
    except AttributeError:
      pass
  
  args.targets = list(targets)
  args.applications = list(applications)
  args.measurements = list(measurements)
  
  Project.create(args.__dict__)
  
  LOGGER.info('Created a new project named %r.' % args.name)
  return executeCommand(['project', 'list'], [args.name])
