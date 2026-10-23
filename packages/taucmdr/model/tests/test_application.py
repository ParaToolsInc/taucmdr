#
# Copyright (c) 2016-2026, ParaTools, Inc.
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
"""Test functions.

Functions used for unit tests of application.py.
"""

from unittest import mock
from taucmdr import tests, EXIT_SUCCESS
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.application.copy import COMMAND as copy_cmd
from taucmdr.cli.commands.application.edit import COMMAND as edit_cmd
from taucmdr.cli.commands.application.list import COMMAND as list_cmd
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.model.application import Application
from taucmdr.model.experiment import Experiment


class ApplicationTest(tests.TestCase):
    """Tests for :any:`taucmdr.model.application.Application`."""

    def test_record_with_max_threads(self):
        """An application stored with the obsolete ``max_threads`` attribute still works with every command."""
        self.reset_project_storage()
        PROJECT_STORAGE.update({'max_threads': 64}, {'name': 'app1'}, table_name=Application.name)
        self.assertEqual(PROJECT_STORAGE.get({'name': 'app1'}, table_name=Application.name)['max_threads'], 64)
        self.assertCommandReturnValue(EXIT_SUCCESS, list_cmd, [])
        self.assertCommandReturnValue(EXIT_SUCCESS, edit_cmd, ['app1', '--mpi=False'])
        self.assertCommandReturnValue(EXIT_SUCCESS, copy_cmd, ['app1', 'app2'])
        with mock.patch.object(Experiment, 'configure'):
            self.assertCommandReturnValue(EXIT_SUCCESS, select_cmd,
                                          ['--target', 'targ1', '--application', 'app1', '--measurement', 'sample'])
