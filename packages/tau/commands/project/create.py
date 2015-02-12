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


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Create a new project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
  %(command)s <project_name> [targets] [applications] [measurements]
  %(command)s <project_name> [--targets targets] [--applications applications] [--measurements measurements]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

HELP_EPILOG = ""

_arguments = [ (('name',), {'help': "Project name",
                            'metavar': '<project_name>'}),
               (('targets',), {'help': "Target configurations in this project",
                               'metavar': '[targets]',
                               'nargs': '*',
                               'default': SUPPRESS}),
               (('applications',), {'help': "Application configurations in this project",
                                    'metavar': '[applications]',
                                    'nargs': '*',
                                    'default': SUPPRESS}),
               (('measurements',), {'help': "Measurement configurations in this project",
                                    'metavar': '[measurements]',
                                    'nargs': '*',
                                    'default': SUPPRESS}),  
               (('--targets',), {'help': "Indicates that the following objects are targets",
                                 'metavar': 'target',
                                 'nargs': '+',
                                 'default': SUPPRESS,
                                 'dest': 'expl_targets'}),
               (('--applications',), {'help': "Application configurations in this project",
                                      'metavar': 'application',
                                      'nargs': '+',
                                      'default': SUPPRESS,
                                      'dest': 'expl_applications'}),
               (('--measurements',), {'help': "Measurement configurations in this project",
                                      'metavar': 'measurement',
                                      'nargs': '+',
                                      'default': SUPPRESS,
                                      'dest': 'expl_measurements'}) ]  
PARSER = getParser(_arguments,
                   prog=COMMAND, 
                   usage=USAGE, 
                   description=SHORT_DESCRIPTION,
                   epilog=HELP_EPILOG)


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
  
  targets = []
  applications = []
  measurements = []
  
  implicit = getattr(args, 'targets', []) + getattr(args, 'applications', []) + getattr(args, 'measurements', [])
  for name in implicit:
    target = Target.search({'name': name})
    if not target:
      application = Application.search({'name': name})
      if not application:
        measurement = Measurement.search({'name': name})
        if not measurement:
          PARSER.error('There is not target, application, or measurement named %r' % name)
        else:
          measurements.append(measurement)
      else:
        applications.append(application)
    else:
      targets.append(target)
  
  for target_name in getattr(args, 'expl_targets', []):
    target = Target.search({'name': target_name})
    if not target:
      PARSER.error('There is no target named %r' % target_name)
    else:
      targets.append(target)
      
  print targets

#   for application_name in args.expl_applications:
#     if not Application.exists({'name': application_name}):
#       PARSER.error('There is no application named %r' % application_name)
#   
#   for measurement_name in args.expl_measurements:
#     if not Measurement.exists({'name': measurement_name}):
#       PARSER.error('There is no measurement named %r' % measurement_name)

  
  
  
  LOGGER.info('Created a new project named %r.' % args.name)
  return executeCommand(['project', 'list'], [args.name])
