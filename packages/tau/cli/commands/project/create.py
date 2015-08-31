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
"""``tau project create`` subcommand."""

from tau import logger, cli
from tau.cli import arguments
from tau.model import UniqueAttributeError
from tau.model.project import Project
from tau.model.target import Target
from tau.model.application import Application
from tau.model.measurement import Measurement


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Create a new project configuration."

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
        usage_head = "%s <project_name> [targets] [applications] [measurements] [arguments]" % COMMAND       
        parser.inst = arguments.get_parser_from_model(Project,
                                                      prog=COMMAND,
                                                      usage=usage_head,
                                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('impl_targets',
                                 help="Target configurations in this project",
                                 metavar='[targets]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('impl_applications',
                                 help="Application configurations in this project",
                                 metavar='[applications]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('impl_measurements',
                                 help="Measurement configurations in this project",
                                 metavar='[measurements]',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--targets',
                                 help="Target configurations in this project",
                                 metavar='t',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--applications',
                                 help="Application configurations in this project",
                                 metavar='a',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('--measurements',
                                 help="Measurement configurations in this project",
                                 metavar='m',
                                 nargs='+',
                                 default=arguments.SUPPRESS)
    return parser.inst


def main(argv):
    """Subcommand program entry point.
    
    Args:
        argv (list): Command line arguments.
        
    Returns:
        int: Process return code: non-zero if a problem occurred, 0 otherwise
    """
    args = parser().parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    targets = set()
    applications = set()
    measurements = set()

    for attr, model, dest in [('targets', Target, targets),
                              ('applications', Application, applications),
                              ('measurements', Measurement, measurements)]:
        for name in getattr(args, attr, []):
            found = model.with_name(name)
            if not found:
                parser().error("There is no %s named '%s'" % (model.model_name, name))
            dest.add(found.eid)

        for name in getattr(args, 'impl_' + attr, []):
            tar = Target.with_name(name)
            app = Application.with_name(name)
            mes = Measurement.with_name(name)
            tam = set([tar, app, mes]) - set([None])
            if len(tam) > 1:
                parser().error("'%s' is ambiguous, please use --targets, --applications,"
                               " or --measurements to specify configuration type" % name)
            elif len(tam) == 0:
                parser().error("'%s' is not a target, application, or measurement" % name)
            elif tar:
                targets.add(tar.eid)
            elif app:
                applications.add(app.eid)
            elif mes:
                measurements.add(mes.eid)

        try:
            delattr(args, 'impl_' + attr)
        except AttributeError:
            pass

    args.targets = list(targets)
    args.applications = list(applications)
    args.measurements = list(measurements)

    try:
        Project.create(args.__dict__)
    except UniqueAttributeError:
        parser().error("A project named '%s' already exists." % args.name)

    LOGGER.info("Created a new project named '%s'.", args.name)
    return cli.execute_command(['project', 'list'], [args.name])
