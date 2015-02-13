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
from arguments import getParser, SUPPRESS
from api.project import Project


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Modify a project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s <project_name> [options]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('name',), 
               {'help': "Name of project configuration to edit",
                'metavar': '<project_name>'}),
              (('--name',), 
               {'help': "New name of the project configuration",
                'metavar': '<new_name>',
                'dest': 'new_name',
                'default': SUPPRESS}),
              (('--add',), 
               {'help': "Add target, application, or measurement configurations to the project",
                'metavar': '<conf>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--remove',), 
               {'help': "Remove target, application, or measurement configurations from the project",
                'metavar': '<conf>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--add-targets',), 
               {'help': "Add target configurations to the project",
                'metavar': '<target>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--add-applications',), 
               {'help': "Add application configurations to the project",
                'metavar': '<application>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--add-measurements',), 
               {'help': "Add measurement configurations to the project",
                'metavar': '<measurement>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--remove-targets',), 
               {'help': "Remove target configurations from the project",
                'metavar': '<target>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--remove-applications',), 
               {'help': "Remove application configurations from the project",
                'metavar': '<application>',
                'nargs': '+',
                'default': SUPPRESS}),
              (('--remove-measurements',), 
               {'help': "Remove measurement configurations from the project",
                'metavar': '<measurement>',
                'nargs': '+',
                'default': SUPPRESS})]

PARSER = getParser(_arguments,
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

  name = args.name
  updates = {'name': getattr(args, 'new_name', name)}
  
  project = Project.withName(name)
  if not project:
    PARSER.error('There is no project named %r' % name)
  targets = set(project.targets)
  applications = set(project.applications)
  measurements = set(project.measurements)
  
  for attr, model, dest in [('add_targets', Target, targets), 
                            ('add_applications', Application, applications), 
                            ('add_measurements', Measurement, measurements)]:
    names = getattr(args, attr, [])
    for name in names:
      found = model.withName(name)
      if not found:
        PARSER.error('There is no %s named %r' % (model.model_name, name))
      dest.add(name)

  for name in set(args.add):
    t = Target.withName(name)
    a = Application.withName(name)
    m = Measurement.withName(name)
    tam = set([t,a,m]) - set([None])
    if len(tam) > 1:
      PARSER.error('%r is ambigous, please use --add-targets, --add-applications,'
                   ' or --add-measurements to specify configuration type' % name)
    elif len(tam) == 0:
      PARSER.error('%r is not a target, application, or measurement' % name)
    elif t:
      targets.add(t.name)
    elif a:
      applications.add(a.name)
    elif m:
      measurements.add(m.name)

  for attr, model, dest in [('remove_targets', Target, targets), 
                            ('remove_applications', Application, applications), 
                            ('remove_measurements', Measurement, measurements)]:
    names = getattr(args, attr, [])
    for name in names:
      found = model.withName(name)
      if not found:
        PARSER.error('There is no %s named %r' % (model.model_name, name))
      dest.remove(name)

  for name in set(args.remove):
    t = Target.withName(name)
    a = Application.withName(name)
    m = Measurement.withName(name)
    tam = set([t,a,m]) - set([None])
    if len(tam) > 1:
      PARSER.error('%r is ambigous, please use --remove-targets, --remove-applications,'
                   ' or --remove-measurements to specify configuration type' % name)
    elif len(tam) == 0:
      PARSER.error('%r is not a target, application, or measurement' % name)
    elif t:
      targets.remove(t.name)
    elif a:
      applications.remove(a.name)
    elif m:
      measurements.remove(m.name)
      
  updates['targets'] = list(targets)
  updates['applications'] = list(applications)
  updates['measurements'] = list(measurements)
    
  Target.update({'name': name}, updates)
    
  return executeCommand(['project', 'list'], [args.name])
