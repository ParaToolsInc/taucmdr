#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#"""

from tau import logger, cli
from tau.cli import arguments
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Modify a project configuration."

USAGE = """
  %(command)s <project_name> [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

_arguments = [(('--rename',),
               {'help': "Rename the project configuration",
                'metavar': '<new_name>',
                'dest': 'new_name',
                'default': arguments.SUPPRESS}),
              (('--add',),
               {'help': "Add target, application, or measurement configurations to the project",
                'metavar': '<conf>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--remove',),
               {'help': "Remove target, application, or measurement configurations from the project",
                'metavar': '<conf>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--add-targets',),
               {'help': "Add target configurations to the project",
                'metavar': '<target>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--add-applications',),
               {'help': "Add application configurations to the project",
                'metavar': '<application>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--add-measurements',),
               {'help': "Add measurement configurations to the project",
                'metavar': '<measurement>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--remove-targets',),
               {'help': "Remove target configurations from the project",
                'metavar': '<target>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--remove-applications',),
               {'help': "Remove application configurations from the project",
                'metavar': '<application>',
                'nargs': '+',
                'default': arguments.SUPPRESS}),
              (('--remove-measurements',),
               {'help': "Remove measurement configurations from the project",
                'metavar': '<measurement>',
                'nargs': '+',
                'default': arguments.SUPPRESS})]

PARSER = arguments.get_parser_from_model(Project,
                                      prog=COMMAND,
                                      usage=USAGE,
                                      description=SHORT_DESCRIPTION)
for arg in _arguments:
    flags, options = arg
    PARSER.add_argument(*flags, **options)


def get_usage():
    return PARSER.format_help()


def get_help():
    return HELP


def main(argv):
    """
    Program entry point
    """
    args = PARSER.parse_args(args=argv)
    LOGGER.debug('Arguments: %s' % args)

    project_name = args.name
    project = Project.with_name(project_name)
    if not project:
        PARSER.error("'%s' is not a project name. Type `tau project list` to see valid names." % project_name)

    updates = dict(project.data)
    try:
        updates['prefix'] = args.prefix
    except AttributeError:
        pass
    updates['name'] = getattr(args, 'new_name', project_name)
    targets = set(project['targets'])
    applications = set(project['applications'])
    measurements = set(project['measurements'])

    for attr, model, dest in [('add_targets', Target, targets),
                              ('add_applications', Application, applications),
                              ('add_measurements', Measurement, measurements)]:
        names = getattr(args, attr, [])
        for name in names:
            found = model.with_name(name)
            if not found:
                PARSER.error('There is no %s named %r' %
                             (model.model_name, name))
            dest.add(found.eid)

    for name in set(getattr(args, "add", [])):
        t = Target.with_name(name)
        a = Application.with_name(name)
        m = Measurement.with_name(name)
        tam = set([t, a, m]) - set([None])
        if len(tam) > 1:
            PARSER.error('%r is ambiguous, please use --add-targets, --add-applications,'
                         ' or --add-measurements to specify configuration type' % name)
        elif len(tam) == 0:
            PARSER.error(
                '%r is not a target, application, or measurement' % name)
        elif t:
            targets.add(t.eid)
        elif a:
            applications.add(a.eid)
        elif m:
            measurements.add(m.eid)

    for attr, model, dest in [('remove_targets', Target, targets),
                              ('remove_applications',
                               Application, applications),
                              ('remove_measurements', Measurement, measurements)]:
        names = getattr(args, attr, [])
        for name in names:
            found = model.with_name(name)
            if not found:
                PARSER.error('There is no %s named %r' %
                             (model.model_name, name))
            dest.remove(found.eid)

    for name in set(getattr(args, "remove", [])):
        t = Target.with_name(name)
        a = Application.with_name(name)
        m = Measurement.with_name(name)
        tam = set([t, a, m]) - set([None])
        if len(tam) > 1:
            PARSER.error('%r is ambiguous, please use --remove-targets, --remove-applications,'
                         ' or --remove-measurements to specify configuration type' % name)
        elif len(tam) == 0:
            PARSER.error(
                '%r is not a target, application, or measurement' % name)
        elif t:
            targets.remove(t.eid)
        elif a:
            applications.remove(a.eid)
        elif m:
            measurements.remove(m.eid)

    updates['targets'] = list(targets)
    updates['applications'] = list(applications)
    updates['measurements'] = list(measurements)

    Project.update(updates, {'name': project_name})

    return cli.execute_command(['project', 'list'], [updates['name']])
