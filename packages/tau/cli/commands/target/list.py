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
"""``tau target list`` subcommand."""


from texttable import Texttable
from pprint import pformat
from tau import EXIT_SUCCESS, USER_PREFIX, EXIT_WARNING
from tau import logger, cli
from tau.cli import arguments
from tau.core.target.controller import Target


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "List target configurations or show configuration details."

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
        usage_head = "%s [target_name] [target_name] ... [arguments]" % COMMAND
        parser.inst = arguments.get_parser(prog=COMMAND,
                                           usage=usage_head,
                                           description=SHORT_DESCRIPTION)
        parser.inst.add_argument('names', 
                                 help="If given, show details for the target with this name",
                                 metavar='target_name',
                                 nargs='*',
                                 default=arguments.SUPPRESS)
        parser.inst.add_argument('-l', '--long', 
                                 help="display all information about the target",
                                 action='store_true',
                                 default=False)
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

    try:
        names = args.names
    except AttributeError:
        found = Target.all()
    else:
        found = []
        for name in names:
            record = Target.with_name(name)
            if not record:
                parser().error("No target configuration named '%s'" % name)
            found.append(record)

    print '{:=<{}}\n'.format('== Targets (%s) ==' % USER_PREFIX, logger.LINE_WIDTH)
    if not found:
        print "No targets. See `%s --help`.\n" % COMMAND
        return EXIT_WARNING
    
    table = Texttable(logger.LINE_WIDTH)
    cols = [('Name', 'r', 'name'),
            ('Host OS', 'c', 'host_os'),
            ('Host Arch', 'c', 'host_arch'),
            ('C', 'l', None),
            ('C++', 'l', None),
            ('Fortran', 'l', None),
            ('In Projects', 'l', None)]
    headers = [header for header, _, _ in cols]
    rows = [headers]
    if args.long:
        listing = '\n'.join([pformat(record.populate()) for record in found])
    else:
        for record in found:
            populated = record.populate()
            projects = ', '.join([p['name'] for p in populated['projects']])
            cc_path = populated['CC']['path']
            cxx_path = populated['CXX']['path']
            fc_path = populated['FC']['path']
            row = [populated.get(attr, '')
                   for _, _, attr in cols if attr] + [cc_path, cxx_path, fc_path, projects]
            rows.append(row)
        table.set_cols_align([align for _, align, _ in cols])
        table.add_rows(rows)
        listing = table.draw()

    print listing
    print 
    return EXIT_SUCCESS
