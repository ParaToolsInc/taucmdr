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


DASHBOARD_COLUMNS = [{'header': 'Hash', 'hash': 10, 'dtype': 't'},
                     {'header': 'Number', 'value': 'number'},
                     {'header': 'Data Size', 'function': lambda x: util.human_size(x.get('data_size', None))},
                     {'header': 'Command', 'value': 'command'},
                     {'header': 'Description', 'value': 'description'},
                     {'header': 'Status', 'value': 'phase'}]


class TrialListCommand(ListCommand):
    """``trial list`` subcommand."""
    
    def _retrieve_records(self, ctrl, keys):
        if keys:
            try:
                keys = [int(key) for key in keys]
            except ValueError:
                self.parser.error("Invalid trial number '%s'.  Trial numbers are positive integers starting from 0.")
        expr = Project.selected().experiment()
        records = super(TrialListCommand, self)._retrieve_records(ctrl, keys)
        return [rec for rec in records if rec['experiment'] == expr.eid]

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
        expr = Project.selected().experiment()
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
                elif 'hash' in col:
                    cell = record.hash_digest()[-col['hash']:]
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
