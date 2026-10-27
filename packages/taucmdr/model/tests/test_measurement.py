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

Functions used for unit tests of measurement.py.
"""


from unittest import mock
from taucmdr import tests, EXIT_SUCCESS
from taucmdr.error import IncompatibleRecordError
from taucmdr.cf.platforms import DARWIN, HOST_OS
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.cli.commands.target.create import COMMAND as target_create_cmd
from taucmdr.model.experiment import Experiment
from taucmdr.model.measurement import Measurement


@tests.not_implemented
class MeasurementTest(tests.TestCase):
    pass


class InstrumentationTest(tests.TestCase):
    """Tests for the instrumentation defaults and requirements on other operating systems."""

    @tests.skipIf(HOST_OS is DARWIN, "Checks the defaults of other operating systems")
    def test_defaults(self):
        self.assertEqual(Measurement.attributes['source_inst']['default'], 'never')
        self.assertEqual(Measurement.attributes['compiler_inst']['default'], 'never')

    @tests.skipIf(HOST_OS is DARWIN, "Checks the requirements of other operating systems")
    def test_compiler_inst_requires_binutils(self):
        self.reset_project_storage()
        self.assertCommandReturnValue(EXIT_SUCCESS, target_create_cmd, ['targ2', '--binutils', 'None'])
        self.assertCommandReturnValue(EXIT_SUCCESS, measurement_create_cmd,
                                      ['meas2', '--sample', 'False', '--compiler-inst', 'always'])
        with mock.patch.object(Experiment, 'configure'), \
             self.assertRaisesRegex(IncompatibleRecordError, 'compiler_inst'):
            select_cmd.main(['--target', 'targ2', '--application', 'app1', '--measurement', 'meas2'])


class DarwinInstrumentationTest(tests.DarwinTestCase):
    """Tests for the instrumentation defaults and requirements on macOS."""

    def setUp(self):
        super().setUp()
        self.assertSucceeded(self.tau('initialize', '--bare'))
        self.assertSucceeded(self.tau('target', 'create', 'targ1'))
        self.assertSucceeded(self.tau('application', 'create', 'app1'))

    def _select(self, *measurement_args, name='meas1'):
        self.assertSucceeded(self.tau('measurement', 'create', name, *measurement_args))
        return self.tau('select', '--target', 'targ1', '--application', 'app1', '--measurement', name)

    def test_defaults(self):
        out = self.python("from taucmdr.model.measurement import Measurement\n"
                          "print(Measurement.attributes['source_inst']['default'],\n"
                          "      Measurement.attributes['compiler_inst']['default'],\n"
                          "      Measurement.attributes['sample']['default'])")
        self.assertEqual(out, 'never always True')

    def test_source_inst_refused(self):
        proc = self._select('--source-inst', 'automatic')
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('pdt', (proc.stdout + proc.stderr).lower())

    def test_sample_without_binutils(self):
        self.assertSucceeded(self._select('--sample', 'True'))

    def test_io_with_instrumentation_refused(self):
        for compiler_inst in 'always', 'fallback':
            with self.subTest(compiler_inst=compiler_inst):
                proc = self._select('--io', '--source-inst', 'never', '--compiler-inst', compiler_inst,
                                    name=compiler_inst)
                self.assertNotEqual(proc.returncode, 0)
                output = proc.stdout + proc.stderr
                self.assertIn('io = True', output)
                self.assertIn('Darwin', output)

    def test_io_under_tau_exec(self):
        self.assertSucceeded(self._select('--io', '--source-inst', 'never', '--compiler-inst', 'never'))

    def test_memory_alloc_refused(self):
        proc = self._select('--memory-alloc')
        self.assertNotEqual(proc.returncode, 0)
        output = proc.stdout + proc.stderr
        self.assertIn('memory_alloc', output)
        self.assertIn('Darwin', output)

    def test_compiler_inst_without_binutils(self):
        self.assertSucceeded(self._select('--compiler-inst', 'always'))
