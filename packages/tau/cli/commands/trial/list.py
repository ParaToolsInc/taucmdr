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
"""``tau trial list`` subcommand."""


import os
from texttable import Texttable
from pprint import pformat
from tau import EXIT_SUCCESS, EXIT_WARNING, TAU_SCRIPT
from tau import logger, util, cli
from tau.cli import arguments
from tau.model.experiment import Experiment
from tau.model.trial import Trial


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "List experiment trials."

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
        usage_head = "%s [trial_number] [trial_number] ... [arguments]" % COMMAND
        parser.inst = arguments.get_parser(prog=COMMAND,
                                      usage=usage_head,
                                      description=SHORT_DESCRIPTION)
        parser.inst.add_argument('numbers', 
                            help="If given, show details for trial with this number",
                            metavar='trial_number',
                            nargs='*',
                            default=arguments.SUPPRESS)
        parser.inst.add_argument('-l', '--long',
                            help="Display all information about the trial",
                            action='store_true',
                            default=False)
        parser.inst.add_argument('-s', '--short', 
                            help="Summarize trial information",
                            action='store_true',
                            default=False)
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

    selection = Experiment.get_selected()
    if not selection:
        print "No experiment configured. See `tau project select`\n"
        return EXIT_WARNING

    longflag = args.long
    shortflag = args.short
    if longflag and shortflag:
        argparser.error("Please specify either '--long' or '--short', not both")

    try:
        numbers = [int(n) for n in args.numbers]
    except AttributeError:
        found = Trial.search({'experiment': selection.eid})
    except ValueError:
        argparser.error("Invalid trial number")
    else:
        found = []
        for num in numbers:
            record = Trial.search({'number': num})
            if not record:
                argparser.error("No trial number %d in the current experiment" % num)
            found.extend(record)

    print '{:=<{}}\n'.format('== %s Trials ==' % selection.name(), logger.LINE_WIDTH)
    if not found:
        script_name = os.path.basename(TAU_SCRIPT)
        print ("No trials. Use `%s <command>` or `%s trial create <command>`"
               " to create a new trial.\n" % (script_name, script_name))
        return EXIT_WARNING

    table = Texttable(logger.LINE_WIDTH)
    cols = [('Number', 'c', 'number'),
            ('Data Size', 'c', 'data_size'),
            ('Command', 'l', 'command'),
            ('In Directory', 'l', 'cwd'),
            ('Began at', 'c', 'begin_time'),
            ('Ended at', 'c', 'end_time'),
            ('Return Code', 'c', 'return_code')]
    headers = [header for header, _, _ in cols]
    rows = [headers]
    if longflag:
        listing = '\n'.join([pformat(record.data) for record in found])
    elif shortflag:
        parts = []
        trials_by_cmd = {}
        for trial in found:
            trials_by_cmd.setdefault(trial['command'], []).append(trial)
        for key, val in trials_by_cmd.iteritems():
            count = len(val)
            data_size = util.human_size(sum([trial['data_size'] for trial in val]))
            if count == 1:
                msg = "  1 trial of '%s' (%s)." % (os.path.basename(key), data_size)
            else:
                msg = "  %d trials of '%s' (%s)." % (len(val), os.path.basename(key), data_size)
            parts.append(msg + '  Use `tau trial list` to see details.')
        listing = '\n'.join(parts)
    else:
        for record in found:
            row = [record.get(attr, '') for _, _, attr in cols if attr]
            row[1] = util.human_size(row[1])
            rows.append(row)
        table.set_cols_align([align for _, align, _ in cols])
        table.add_rows(rows)
        listing = table.draw()

    print listing
    print
    return EXIT_SUCCESS
