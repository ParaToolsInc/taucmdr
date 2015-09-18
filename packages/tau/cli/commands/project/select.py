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
"""``tau project select`` subcommand."""


from tau import logger, cli
from tau.cli import arguments
from tau.error import InternalError
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement
from tau.model.experiment import Experiment


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Select project components for the next experiment."

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
        usage_head = "%s project_name [target] [application] [measurement] [arguments]" % COMMAND
        parser.inst = arguments.get_parser_from_model(Project,
                                                      prog=COMMAND,
                                                      usage=usage_head,
                                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('impl_target',
                                 help="Target configuration to select",
                                 metavar='[target]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('impl_application',
                                 help="Application configuration to select",
                                 metavar='[application]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('impl_measurement',
                                 help="Measurement configuration to select",
                                 metavar='[measurements]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--target',
                                 help="Target configuration to select",
                                 metavar='<name>',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--application',
                                 help="Application configuration to select",
                                 metavar='<name>',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--measurement',
                                 help="Measurement configuration to select",
                                 metavar='<name>',
                                 default=arguments.SUPPRESS)
    return parser.inst


def _select(project, attr, given):
    argparser = parser()
    in_project = project[attr]
    if len(given) > 1:
        names = ', '.join([m['name'] for m in list(given)])
        argparser.error('Multiple %s given (%s). Please specify only one.' % (attr, names))
    elif len(given) == 1:
        selected = list(given)[0]
        if selected.eid not in in_project:
            argparser.error("'%s' is not a member of project '%s'" % (selected['name'], project['name']))
        return selected.eid
    else:
        if len(in_project) > 1:
            argparser.error("Project '%s' has multiple %s. Please specify which to use." % (project['name'], attr))
        elif len(in_project) == 1:
            return in_project[0]
        else:
            argparser.error("Project '%s' has no %s.  See `tau project edit --help`." % (project['name'], attr))


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (list): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    argparser = parser()
    args = argparser.parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    project = Project.with_name(args.name)
    if not project:
        argparser.error("'%s' is not a project name . Type `%s` to see valid names." % (args.name, COMMAND))

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
            mes = model.with_name(name)
            if mes:
                dest.add(mes)
            else:
                argparser.error('There is no %s named %s' % (attr, name))

        for name in getattr(args, 'impl_' + attr, []):
            tar = Target.with_name(name)
            app = Application.with_name(name)
            mes = Measurement.with_name(name)
            tam = set([tar, app, mes]) - set([None])
            if len(tam) > 1:
                argparser.error("'%s' is ambiguous, please use --target, --application,"
                                " or --measurement to specify configuration type" % name)
            elif len(tam) == 0:
                argparser.error("'%s' is not a target, application, or measurement" % name)
            elif tar:
                given_targets.add(tar)
            elif app:
                given_applications.add(app)
            elif mes:
                given_measurements.add(mes)

    target_eid = _select(project, 'targets', given_targets)
    application_eid = _select(project, 'applications', given_applications)
    measurement_eid = _select(project, 'measurements', given_measurements)

    targ = Target.one(eid=target_eid)
    app = Application.one(eid=application_eid)
    meas = Measurement.one(eid=measurement_eid)
    
    for lhs in [targ, app, meas]:
        for rhs in [targ, app, meas]:
            lhs.check_compatibility(rhs)

    data = {'project': project.eid,
            'target': target_eid,
            'application': application_eid,
            'measurement': measurement_eid}
    matching = Experiment.search(data)
    if not matching:
        LOGGER.debug('Creating new experiment')
        found = Experiment.create(data)
    elif len(matching) > 1:
        raise InternalError('More than one experiment with data %r exists!' % data)
    else:
        LOGGER.debug('Using existing experiment')
        found = matching[0]

    populated = found.populate()
    LOGGER.debug("'%s' on '%s' measured by '%s'",
                 populated['application']['name'],
                 populated['target']['name'],
                 populated['measurement']['name'])
    found.select()

    return cli.execute_command(['trial', 'list'], ['-s'])
