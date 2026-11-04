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

Functions used for unit tests of create.py.
"""


from taucmdr import tests
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.model.measurement import Measurement
from taucmdr.cli.commands.measurement.create import COMMAND as create_cmd

# (label, flags, expected stored list, whether the TIME warning is expected)
METRICS_CASES = (
    ('comma', ['--metrics', 'TIME,PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('comma_equals', ['--metrics=TIME,PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('space', ['--metrics', 'TIME', 'PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('mixed', ['--metrics', 'TIME,PAPI_L1_DCM', 'PAPI_TOT_CYC'], ['TIME', 'PAPI_L1_DCM', 'PAPI_TOT_CYC'], False),
    ('time_absent', ['--metrics', 'PAPI_TOT_CYC,PAPI_L1_DCM'], ['TIME', 'PAPI_TOT_CYC', 'PAPI_L1_DCM'], True),
    ('time_not_first', ['--metrics', 'PAPI_TOT_CYC,TIME'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('time_repeated', ['--metrics', 'TIME,PAPI_TOT_CYC,TIME'], ['TIME', 'PAPI_TOT_CYC'], False),
    ('repeated', ['--metrics', 'TIME,PAPI_TOT_CYC', 'papi_tot_cyc', 'PAPI_L1_DCM,PAPI_TOT_CYC'],
     ['TIME', 'PAPI_TOT_CYC', 'PAPI_L1_DCM'], False),
    ('time_lowercase', ['--metrics', 'time,PAPI_TOT_CYC'], ['TIME', 'PAPI_TOT_CYC'], False),
)
TIME_WARNING = "'TIME' must always be present"


class CreateTest(tests.TestCase):
    """Tests for :any:`measurement.create`."""

    def test_create(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, ['meas01'])
        self.assertIn('Added measurement \'meas01\' to project configuration', stdout)
        self.assertFalse(stderr)

    def test_duplicatename(self):
        self.reset_project_storage()
        self.assertCommandReturnValue(0, create_cmd, ['meas01'])
        _, stderr = self.assertNotCommandReturnValue(0, create_cmd, ['meas01'])
        self.assertIn('measurement create <measurement_name> [arguments]', stderr)
        self.assertIn('measurement create: error: A measurement with name', stderr)
        self.assertIn('already exists', stderr)

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)

    def test_trace_callpath(self):
        self.reset_project_storage()
        name = 'trace_callpath'
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, [name, '--trace'])
        self.assertFalse(stderr)
        self.assertIn("Added measurement '%s' to project" % name, stdout)
        self.assertNotIn("WARNING", stdout)
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas['callpath'], 0)

    def test_trace_callpath_0(self):
        self.reset_project_storage()
        name = 'test_trace_callpath_0'
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, [name, '--trace', '--callpath', '0'])
        self.assertFalse(stderr)
        self.assertIn("Added measurement '%s' to project" % name, stdout)
        self.assertNotIn("WARNING", stdout)
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas['callpath'], 0)

    def test_trace_callpath_10(self):
        self.reset_project_storage()
        name = 'test_discourage_callpath'
        stdout, stderr = self.assertCommandReturnValue(0, create_cmd, [name, '--trace', '--callpath', '10'])
        self.assertFalse(stderr)
        self.assertIn("Added measurement '%s' to project" % name, stdout)
        self.assertIn("WARNING", stdout)
        meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
        self.assertIsInstance(meas, Measurement)
        self.assertEqual(meas['callpath'], 10)

    def test_metrics_forms(self):
        for label, flags, expected, warns in METRICS_CASES:
            with self.subTest(label):
                self.reset_project_storage()
                name = 'meas_' + label
                stdout, stderr = self.assertCommandReturnValue(0, create_cmd, [name] + flags)
                self.assertFalse(stderr)
                self.assertEqual(TIME_WARNING in stdout, warns)
                meas = Measurement.controller(PROJECT_STORAGE).one({'name': name})
                self.assertEqual(meas['metrics'], expected)
