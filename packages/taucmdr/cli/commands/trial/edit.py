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
"""``trial edit`` subcommand."""

from __future__ import absolute_import
from taucmdr import EXIT_SUCCESS
from taucmdr.cli.cli_view import EditCommand
from taucmdr.model.trial import Trial
from taucmdr.model.project import Project

class TrialEditCommand(EditCommand):
    """``trial edit`` subcommand."""

    def _update_record(self, store, data, key):
        expr = Project.selected().experiment()
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        if not ctrl.exists({key_attr: key, 'experiment': expr.eid}):
            self.parser.error("No {}-level {} with {}='{}'.".format(ctrl.storage.name, self.model_name, key_attr, key))
        ctrl.update(data, {key_attr: key, 'experiment': expr.eid})
        self.logger.info("Updated %s '%s'", self.model_name, key)
        return EXIT_SUCCESS

COMMAND = TrialEditCommand(Trial, __name__, summary_fmt="Edit experiment trials.",
                           include_storage_flag=False, include_new_key_flag=False)
