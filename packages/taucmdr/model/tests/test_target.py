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
"""Unit tests for :py:mod:`taucmdr.model.target`."""

import os
import tempfile
from unittest import mock
from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.target.list import COMMAND as target_list_cmd
from taucmdr.model import target
from taucmdr.model.target import Target


class TargetTest(tests.TestCase):
    """Tests for :any:`taucmdr.model.target.Target`."""

    def _target_with(self, data):
        self.reset_project_storage()
        ctrl = Target.controller(PROJECT_STORAGE)
        ctrl.update(data, {'name': 'targ1'})
        return ctrl.one({'name': 'targ1'})

    def test_unknown_host_arch(self):
        """A target saved with an architecture this version doesn't know gives a clear error."""
        targ = self._target_with({'host_arch': 'NoSuchArch'})
        self.assertCommandReturnValue(0, target_list_cmd, [])
        with self.assertRaisesRegex(ConfigurationError, 'NoSuchArch'):
            targ.architecture()

    def test_unknown_host_os(self):
        """A target saved with an operating system this version doesn't know gives a clear error."""
        targ = self._target_with({'host_os': 'NoSuchOS'})
        self.assertCommandReturnValue(0, target_list_cmd, [])
        with self.assertRaisesRegex(ConfigurationError, 'NoSuchOS'):
            targ.operating_system()

    def test_legacy_ompt_source(self):
        """A target stored with a removed OMPT download variant still loads and lists."""
        self.reset_project_storage()
        PROJECT_STORAGE.update({'ompt_source': 'download-tr6'}, {'name': 'targ1'}, table_name=Target.name)
        stored = PROJECT_STORAGE.get({'name': 'targ1'}, table_name=Target.name)
        self.assertEqual(stored['ompt_source'], 'download-tr6')
        targ = Target.controller(PROJECT_STORAGE).one({'name': 'targ1'})
        self.assertEqual(targ.sources()['ompt'], 'download')
        self.assertCommandReturnValue(0, target_list_cmd, [])

    def test_tau_source_override_missing(self):
        """An override_tau_source file with a missing directory produces a warning."""
        system_prefix = tempfile.mkdtemp(dir=os.getcwd())
        missing = os.path.join(system_prefix, 'no-such-tau')
        with open(os.path.join(system_prefix, 'override_tau_source'), 'w', encoding='utf-8') as fout:
            fout.write(missing)
        with mock.patch.object(target, 'SYSTEM_STORAGE', mock.Mock(prefix=system_prefix)), \
                self.assertLogs('taucmdr.model.target', 'WARNING') as logs:
            self.assertEqual(target.tau_source_default(), 'download')
        self.assertIn(missing, logs.output[0])
