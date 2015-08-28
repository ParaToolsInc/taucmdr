# -*- coding: utf-8 -*-
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
#
"""``tau project edit`` subcommand."""

from tau import logger, cli
from tau.cli import arguments
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Modify a project configuration."

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}


def parser():
    """Construct a command line argument parser.
    
    Constructing the parser may cause a lot of imports as :py:mod:`tau.cli` is explored.
    To avoid possible circular imports we defer parser creation until afer all
    modules are imported, hence this function.  The parser instance is maintained as
    an attribute of the function, making it something like a C++ function static variable.
    """
    if not hasattr(parser, 'inst'):
        usage_head = "%s <project_name> [arguments]" % COMMAND
        parser.inst = arguments.get_parser_from_model(Project,
                                                      prog=COMMAND,
                                                      usage=usage_head,
                                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('--rename',
                                 help="Rename the project configuration",
                                 metavar='<new_name>',
                                 dest='new_name',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--add',
                                 help="Add target, application, or measurement configurations to the project",
                                 metavar='<conf>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--remove',
                                 help="Remove target, application, or measurement configurations from the project",
                                 metavar='<conf>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--add-targets',
                                 help="Add target configurations to the project",
                                 metavar='<target>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--add-applications',
                                 help="Add application configurations to the project",
                                 metavar='<application>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--add-measurements',
                                 help="Add measurement configurations to the project",
                                 metavar='<measurement>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--remove-targets',
                                 help="Remove target configurations from the project",
                                 metavar='<target>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--remove-applications',
                                 help="Remove application configurations from the project",
                                 metavar='<application>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--remove-measurements',
                                 help="Remove measurement configurations from the project",
                                 metavar='<measurement>',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
    return parser.inst


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (:py:class:`list`): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    argparser = parser()
    args = argparser.parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    project_name = args.name
    project = Project.with_name(project_name)
    if not project:
        argparser.error("'%s' is not a project name. Type `%s` to see valid names." % (project_name, COMMAND))

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
                argparser.error("There is no %s named '%s'" % (model.model_name, name))
            dest.add(found.eid)

    for name in set(getattr(args, "add", [])):
        tar = Target.with_name(name)
        app = Application.with_name(name)
        mes = Measurement.with_name(name)
        tam = set([tar, app, mes]) - set([None])
        if len(tam) > 1:
            argparser.error("'%s' is ambiguous. Use --add-targets, --add-applications,"
                            " or --add-measurements to specify configuration type" % name)
        elif len(tam) == 0:
            argparser.error("'%s' is not a target, application, or measurement" % name)
        elif tar:
            targets.add(tar.eid)
        elif app:
            applications.add(app.eid)
        elif mes:
            measurements.add(mes.eid)

    for attr, model, dest in [('remove_targets', Target, targets),
                              ('remove_applications',
                               Application, applications),
                              ('remove_measurements', Measurement, measurements)]:
        names = getattr(args, attr, [])
        for name in names:
            found = model.with_name(name)
            if not found:
                argparser.error('There is no %s named %r' % (model.model_name, name))
            dest.remove(found.eid)

    for name in set(getattr(args, "remove", [])):
        tar = Target.with_name(name)
        app = Application.with_name(name)
        mes = Measurement.with_name(name)
        tam = set([tar, app, mes]) - set([None])
        if len(tam) > 1:
            argparser.error("'%s' is ambiguous. Use --remove-targets, --remove-applications,"
                            " or --remove-measurements to specify configuration type" % name)
        elif len(tam) == 0:
            argparser.error("'%s' is not a target, application, or measurement" % name)
        elif tar:
            targets.remove(tar.eid)
        elif app:
            applications.remove(app.eid)
        elif mes:
            measurements.remove(mes.eid)

    updates['targets'] = list(targets)
    updates['applications'] = list(applications)
    updates['measurements'] = list(measurements)

    Project.update(updates, {'name': project_name})
    return cli.execute_command(['project', 'list'], [updates['name']])
