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
"""``trial list`` subcommand."""

from texttable import Texttable
from taucmdr import util, logger
from taucmdr.error import InternalError
from taucmdr.cli.cli_view import ListCommand
from taucmdr.model.project import Project
from taucmdr.model.trial import Trial


DASHBOARD_COLUMNS = [{'header': 'Number', 'value': 'number'},
                     {'header': 'Data Size', 'function': lambda x: util.human_size(x.get('data_size', None))},
                     {'header': 'Command', 'value': 'command'},
                     {'header': 'Description', 'value': 'description'},
                     {'header': 'Status', 'value': 'phase'},
                     {'header': 'Elapsed Seconds', 'value': 'elapsed'}]

class TrialListCommand(ListCommand):
    """``trial list`` subcommand."""

    def _retrieve_records(self, ctrl, keys, context=True):
        if keys:
            try:
                keys = [int(key) for key in keys]
            except ValueError:
                self.parser.error("Invalid trial number '%s'.  Trial numbers are positive integers starting from 0.")
        proj = Project.selected()
        if proj is None:
            self.parser.error("No project is selected")
        expr = proj.experiment()

        records = super(TrialListCommand, self)._retrieve_records(ctrl, keys, context=context)
        recs = [rec for rec in records if rec['experiment'] == expr.eid]
        return sorted(recs, key=lambda recs: recs['number'])

    def _format_long_item(self, key, val):
        key, val, flags, description = super(TrialListCommand, self)._format_long_item(key, val)
        if key == 'environment' or key == 'output':
            val = '(base64 encoded, %d bytes)' % len(val)
        return [key, val, flags, description]

    def dashboard_format(self, records):
        """Format modeled records in dashboard format.

        Args:
            records: Modeled records to format.

        Returns:
            str: Record data in dashboard format.
        """
        self.logger.debug("Dashboard format")
        title = util.hline(self.title_fmt % {'model_name': records[0].name.capitalize(),
                                             'storage_path': records[0].storage}, 'cyan')
        proj = Project.selected()
        if proj is None:
            self.parser.error("No project is selected")
        expr = proj.experiment()
        subtitle = util.color_text("Selected experiment: ", 'cyan') + expr['name']
        header_row = [col['header'] for col in self.dashboard_columns]
        rows = [header_row]
        for record in records:
            populated = record.populate()
            row = []
            for col in self.dashboard_columns:
                if 'value' in col:
                    try:
                        cell = populated[col['value']]
                    except KeyError:
                        cell = 'N/A'
                elif 'yesno' in col:
                    cell = 'Yes' if populated.get(col['yesno'], False) else 'No'
                elif 'function' in col:
                    cell = col['function'](populated)
                else:
                    raise InternalError("Invalid column definition: %s" % col)
                row.append(cell)
            rows.append(row)
        table = Texttable(logger.LINE_WIDTH)
        table.set_cols_align([col.get('align', 'c') for col in self.dashboard_columns])
        table.add_rows(rows)
        return [title, table.draw(), '', subtitle, '']

COMMAND = TrialListCommand(Trial, __name__, dashboard_columns=DASHBOARD_COLUMNS,
                           summary_fmt="Show trial data.")
