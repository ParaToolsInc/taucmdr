#
# Copyright (c) 2026, ParaTools, Inc.
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

Functions used for unit tests of copy.py.
"""


from taucmdr import tests
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.measurement import Measurement
from taucmdr.cli.commands.measurement.copy import COMMAND as COPY_COMMAND

METRICS_CASES = (
    ('comma', ['--metrics', 'TIME,PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('comma_equals', ['--metrics=TIME,PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('mixed', ['--metrics', 'TIME,PAPI_L1_DCM', 'PAPI_TOT_CYC'], ['TIME', 'PAPI_L1_DCM', 'PAPI_TOT_CYC'], False),
    ('time_absent', ['--metrics', 'PAPI_TOT_CYC,PAPI_L1_DCM'], ['TIME', 'PAPI_TOT_CYC', 'PAPI_L1_DCM'], True),
)
TIME_WARNING = "'TIME' must always be present"


class CopyTest(tests.TestCase):
    """Tests for :any:`measurement.copy`."""

    def test_copy(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, COPY_COMMAND, ['profile', 'meas02'])
        self.assertIn("Added measurement 'meas02' to project configuration", stdout)
        self.assertFalse(stderr)

    def test_metrics_forms(self):
        for label, flags, expected, warns in METRICS_CASES:
            with self.subTest(label):
                self.reset_project_storage()
                name = 'meas_' + label
                stdout, stderr = self.assertCommandReturnValue(0, COPY_COMMAND, ['profile', name] + flags)
                self.assertFalse(stderr)
                self.assertEqual(TIME_WARNING in stdout, warns)
                meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
                self.assertEqual(meas['metrics'], expected)
