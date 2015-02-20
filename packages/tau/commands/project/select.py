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
from error import InternalError
from arguments import getParserFromModel, SUPPRESS
from model.project import Project
from model.target import Target
from model.application import Application
from model.measurement import Measurement
from model.experiment import Experiment


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Select project components to form a new experiment."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[1:]))

USAGE = """
  %(command)s project_name [options] [target] [application] [measurement]
  %(command)s -h | --help
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = getParserFromModel(Project,
                            prog=COMMAND, 
                            usage=USAGE, 
                            description=SHORT_DESCRIPTION)
PARSER.add_argument('impl_target', 
                    help="Target configuration to select",
                    metavar='[target]',
                    nargs='*',
                    default=SUPPRESS)
PARSER.add_argument('impl_application', 
                    help="Application configuration to select",
                    metavar='[application]',
                    nargs='*',
                    default=SUPPRESS)
PARSER.add_argument('impl_measurement', 
                    help="Measurement configuration to select",
                    metavar='[measurements]',
                    nargs='*',
                    default=SUPPRESS)  
PARSER.add_argument('--target',
                    help = "Target configuration to select",
                    metavar='<name>',
                    default = SUPPRESS)
PARSER.add_argument('--application', 
                    help = "Application configuration to select",
                    metavar='<name>',
                    default = SUPPRESS)
PARSER.add_argument('--measurement', 
                    help = "Measurement configuration to select",
                    metavar='<name>',
                    default = SUPPRESS)


def getUsage():
  return PARSER.format_help() 


def getHelp():
  return HELP


def _select(project, attr, given):
  in_project = project[attr]
  if len(given) > 1:
    names = ', '.join([m['name'] for m in list(given)])
    PARSER.error('Multiple %s given (%s). Please specify only one.' % (attr, names))
  elif len(given) == 1:
    selected = list(given)[0]
    if selected.eid not in in_project:
      PARSER.error("'%s' is not a member of project '%s'" % (selected['name'], project['name']))
    return selected.eid
  else:
    if len(in_project) > 1:
      PARSER.error("Project '%s' has multiple %s. Please specify which to use." % (project['name'], attr))
    elif len(in_project) == 1:
      return in_project[0]
    else:
      PARSER.error("Project '%s' has no %s.  See `tau project edit --help`." % (project['name'], attr))


def main(argv):
  """
  Program entry point
  """ 
  args = PARSER.parse_args(args=argv)
  LOGGER.debug('Arguments: %s' % args)
  
  project = Project.withName(args.name)
  if not project:
    PARSER.error("There is no project named %r" % args.name)
  
  given_targets = set()
  given_applications = set()
  given_measurements = set()
  
  for attr, model, dest in [('target', Target, given_targets), 
                            ('application', Application, given_applications), 
                            ('measurement', Measurement, given_measurements)]:
    try:
      name = getattr(args, attr)
    except AttributeError:
      pass
    else:
      m = model.withName(name)
      if m:
        dest.add(m)
      else:
        PARSER.error('There is no %s named %s' % (attr, name))
        
    for name in getattr(args, 'impl_'+attr, []):
      t = Target.withName(name)
      a = Application.withName(name)
      m = Measurement.withName(name)
      tam = set([t,a,m]) - set([None])
      if len(tam) > 1:
        PARSER.error("'%s' is ambiguous, please use --target, --application,"
                     " or --measurement to specify configuration type" % name)
      elif len(tam) == 0:
        PARSER.error("'%s' is not a target, application, or measurement" % name)
      elif t:
        given_targets.add(t)
      elif a:
        given_applications.add(a)
      elif m:
        given_measurements.add(m)
        
  target_eid = _select(project, 'targets', given_targets)
  application_eid = _select(project, 'applications', given_applications)
  measurement_eid = _select(project, 'measurements', given_measurements)
  data = {'project': project.eid,
          'target': target_eid,
          'application': application_eid,
          'measurement': measurement_eid}
  found = Experiment.search(data)
  if not found:
    LOGGER.debug('Creating new experiment')
    found = Experiment.create(data)
  elif len(found) > 1:
    raise InternalError('More than one experiment with data %r exists!' % data)
  else:
    LOGGER.debug('Using existing experiment')
    found = found[0]
  
  found.populate()
  found.select()
  
  LOGGER.info("Application '%s' on target '%s' measured by '%s'" % 
              (found['application']['name'],
               found['target']['name'],
               found['measurement']['name']))
  return EXIT_SUCCESS
