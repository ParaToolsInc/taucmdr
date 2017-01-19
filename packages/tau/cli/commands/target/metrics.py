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


from HTMLParser import HTMLParser
from texttable import Texttable
from tau import EXIT_SUCCESS
from tau import logger, util
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.model.target import Target
from tau.cf.software.papi_installation import PapiInstallation


class TargetMetricsCommand(AbstractCommand):
    """`tau target metrics` command."""
    
    def _construct_parser(self):
        usage_head = "%s <target_name>" % self.command 
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        arguments.add_storage_flag(parser, "list", "target")
        parser.add_argument('target_name', help="Target name", metavar='<target_name>')
        return parser
       
    def _format_tau_metrics(self, _, rows):
        rows.append(['TIME', 'Wallclock time'])
    
    def _format_papi_metrics(self, targ, rows):
        html_parser = HTMLParser()
        papi = PapiInstallation(targ.sources(), targ.architecture(), targ.operating_system(), targ.compilers())
        def _parse(item):
            name = item.attrib['name']
            desc = html_parser.unescape(item.attrib['desc'])
            desc = desc[0].capitalize() + desc[1:] + "."
            return [name, desc]
        for event in papi.xml_event_info().iter('event'):
            for modifier in event.iter('modifier'):
                rows.append(_parse(modifier))
            rows.append(_parse(event))
    
    def main(self, argv):
        args = self._parse_args(argv)
        storage = arguments.parse_storage_flag(args)[0]
        targ_name = args.target_name
        targ = Target.controller(storage).one({'name': targ_name})
        if not targ:
            self.parser.error("No %s-level target named '%s'." % (storage.name, targ_name))
        rows = [['Name', 'Description']]
        self._format_tau_metrics(targ, rows)
        self._format_papi_metrics(targ, rows)
        table = Texttable(logger.LINE_WIDTH)
        table.set_cols_align(['r', 'l'])
        name_width = max([len(row[0]) for row in rows])
        table.set_cols_width([name_width, logger.LINE_WIDTH-name_width-3])
        table.set_deco(Texttable.HEADER | Texttable.VLINES)
        table.add_rows(rows)
        print util.hline("Metrics on target '%s'" % targ['name'], 'cyan')
        print table.draw()
        print
        return EXIT_SUCCESS
   


COMMAND = TargetMetricsCommand(__name__, summary_fmt="Show metrics available on this target.")
