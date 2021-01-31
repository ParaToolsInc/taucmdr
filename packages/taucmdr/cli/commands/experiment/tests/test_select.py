#
# Copyright (c) 2016, ParaTools, Inc.
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

Functions used for unit tests of select.py.
"""


from taucmdr import tests
from taucmdr.cli.commands.experiment.select import COMMAND as SELECT_COMMAND
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd


class SelectTest(tests.TestCase):

    def test_noargs(self):
        self.reset_project_storage()
        stdout, stderr = self.assertNotCommandReturnValue(0, SELECT_COMMAND, [])
        self.assertIn('the following arguments are required', stderr)
        self.assertFalse(stdout)

    def test_invalid_metric(self):
        self.reset_project_storage()
        self.assertCommandReturnValue(0, measurement_create_cmd,
                                      ['meas1', '--metrics', 'PAPI_TAUCMDR_INVALID_METRIC'])
        self.assertCommandReturnValue(0, experiment_create_cmd,
                                      ['exp2', '--application', 'app1', '--measurement', 'meas1', '--target', 'targ1'])
        stdout, _ = self.assertCommandReturnValue(0, SELECT_COMMAND, ['exp2'])
        self.assertIn('WARNING', stdout)

    def test_check_rebuild_required(self):
        self.reset_project_storage()
        self.assertCommandReturnValue(0, measurement_create_cmd,
                                      ['meas1', '--metrics', 'TIME', 'PAPI_TOT_CYC'])
        self.assertCommandReturnValue(0, measurement_create_cmd,
                                      ['meas2', '--metrics', 'TIME', 'PAPI_TOT_INS'])
        self.assertCommandReturnValue(0, experiment_create_cmd,
                                      ['exp2', '--application', 'app1', '--measurement', 'meas1', '--target', 'targ1'])
        self.assertCommandReturnValue(0, experiment_create_cmd,
                                      ['exp3', '--application', 'app1', '--measurement', 'meas2', '--target', 'targ1'])
        stdout, _ = self.assertCommandReturnValue(0, SELECT_COMMAND, ['exp2'])
        self.assertIn('rebuild required', stdout)
        stdout, _ = self.assertCommandReturnValue(0, SELECT_COMMAND, ['exp3'])
        if "not compatible" not in stdout:
            self.assertNotIn('rebuild required', stdout)
