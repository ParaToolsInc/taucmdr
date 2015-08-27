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

from texttable import Texttable
from pprint import pformat
from tau import EXIT_SUCCESS, USER_PREFIX
from tau import logger, cli
from tau.cli import arguments
from tau.model.measurement import Measurement


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "List measurement configurations or show configuration details."

USAGE = """
  %(command)s [measurement_name] [measurement_name] ... [arguments]
""" % {'command': COMMAND}

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

PARSER = arguments.get_parser(prog=COMMAND,
                              usage=USAGE,
                              description=SHORT_DESCRIPTION)
PARSER.add_argument('names', 
                    help="If given, show details for the measurement with this name",
                    metavar='measurement_name',
                    nargs='*',
                    default=arguments.SUPPRESS)
PARSER.add_argument('-l', '--long', 
                    help="display all information about the measurement",
                    action='store_true',
                    default=False)



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

    try:
        names = args.names
    except AttributeError:
        found = Measurement.all()
    else:
        found = []
        for name in names:
            t = Measurement.with_name(name)
            if t:
                found.append(t)
            else:
                PARSER.error("No measurement configuration named '%s'" % name)

    title = '{:=<{}}'.format('== Measurements (%s) ==' % USER_PREFIX, logger.LINE_WIDTH)
    if not found:
        listing = "No measurements. See 'tau measurement create --help'"
    else:
        yesno = lambda x: 'Yes' if x else 'No'
        table = Texttable(logger.LINE_WIDTH)
        cols = [('Name', 'r', lambda t: t['name']),
                ('Profile', 'c', lambda t: yesno(t['profile'])),
                ('Trace', 'c', lambda t: yesno(t['trace'])),
                ('Sample', 'c', lambda t: yesno(t['sample'])),
                ('Source Inst.', 'c', lambda t: t['source_inst']),
                ('Compiler Inst.', 'c', lambda t: t['compiler_inst']),
                ('MPI', 'c', lambda t: yesno(t['mpi'])),
                ('OpenMP', 'c', lambda t: t['openmp']),
                ('Callpath Depth', 'c', lambda t: t['callpath']),
                ('Mem. Usage', 'c', lambda t: yesno(t['memory_usage'])),
                ('Mem. Alloc', 'c', lambda t: yesno(t['memory_alloc'])),
                ('In Projects', 'l', None)]
        headers = [header for header, _, _ in cols]
        rows = [headers]
        if args.long:
            parts = []
            for t in found:
                populated = t.populate()
                parts.append(pformat(populated))
            listing = '\n'.join(parts)
        else:
            for t in found:
                populated = t.populate()
                projects = ', '.join([p['name']
                                      for p in populated['projects']])
                row = [fnc(populated)
                       for _, _, fnc in cols if fnc] + [projects]
                rows.append(row)
            table.set_cols_align([align for _, align, _ in cols])
            table.add_rows(rows)
            listing = table.draw()

    print '\n'.join([title, '', listing, ''])
    return EXIT_SUCCESS
