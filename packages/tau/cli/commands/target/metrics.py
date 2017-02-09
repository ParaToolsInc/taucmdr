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
"""``tau target`` subcommand."""


from texttable import Texttable
from tau import EXIT_SUCCESS
from tau import logger, util
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.model.target import Target

class TargetMetricsCommand(AbstractCommand):
    """`tau target metrics` command."""
    
    _measurement_systems = ['TAU', 'PAPI_PRESET', 'PAPI_NATIVE', 'CUPTI']
    
    def _construct_parser(self):
        usage_head = "%s <target_name> [arguments]" % self.command 
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        arguments.add_storage_flag(parser, "use", "target")
        parser.add_argument('target_name', help="Target name", metavar='<target_name>')
        parser.add_argument('--systems', help="List metrics from these measurement systems", 
                            metavar='system', 
                            nargs="+", 
                            choices=self._measurement_systems,
                            default=['TAU', 'PAPI_PRESET'])
        parser.add_argument('--all', help="Show all metrics and their modifiers", default=False,
                            const=True, action="store_const")
        parser.add_argument('--modifiers', help="Show metric modifiers", default=False,
                            const=True, action="store_const")
       
        return parser
       
    def _draw_table(self, targ, metric, rows):
        parts = [util.hline("%s Metrics on Target '%s'" % (metric, targ['name']), 'cyan')]
        table = Texttable(logger.LINE_WIDTH)
        table.set_cols_align(['r', 'l'])
        name_width = max([len(row[0]) for row in rows])
        table.set_cols_width([name_width+1, logger.LINE_WIDTH-name_width-4])
        table.set_deco(Texttable.HEADER | Texttable.VLINES)
        table.add_rows(rows)
        parts.extend([table.draw(), ''])
        return parts
    
    def _format_tau_metrics(self, targ):
        rows = [['Name', 'Description']]
        rows.extend(list(metric) for metric in sorted(targ.tau_metrics()))
        return self._draw_table(targ, 'TAU', rows)
        
    def _format_cupti_metrics(self, targ):
        rows = [['Name', 'Description']]
        rows.extend(list(metric) for metric in sorted(targ.cupti_metrics()))
        return self._draw_table(targ, 'CUPTI', rows)
    
    def _format_papi_metrics(self, targ, event_type, include_modifiers):
        rows = [['Name', 'Description']]
        rows.extend(list(metric) for metric in sorted(targ.papi_metrics(event_type, include_modifiers)))
        return self._draw_table(targ, 'PAPI ' + event_type.capitalize(), rows)
    
    def main(self, argv):
        args = self._parse_args(argv)
        storage = arguments.parse_storage_flag(args)[0]
        targ_name = args.target_name
        targ = Target.controller(storage).one({'name': targ_name})
        if not targ:
            self.parser.error("No %s-level target named '%s'." % (storage.name, targ_name))
        if args.all:
            args.systems = self._measurement_systems
            args.modifiers = True
        parts = []
        if 'CUPTI' in args.systems:
            parts.extend(self._format_cupti_metrics(targ))
        if 'PAPI_PRESET' in args.systems:
            parts.extend(self._format_papi_metrics(targ, 'PRESET', args.modifiers))
        if 'PAPI_NATIVE' in args.systems:
            parts.extend(self._format_papi_metrics(targ, 'NATIVE', args.modifiers))
        if 'TAU' in args.systems:
            parts.extend(self._format_tau_metrics(targ))
        print '\n'.join(parts)
        return EXIT_SUCCESS
   


COMMAND = TargetMetricsCommand(__name__, summary_fmt="Show metrics available on this target.")
