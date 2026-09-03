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

Functions used for unit tests of initialize.py.
"""

import os
from unittest import mock
from taucmdr import tests
from taucmdr.cf.platforms import DARWIN, LINUX
from taucmdr.cli.commands import initialize as initialize_module
from taucmdr.cli.commands.initialize import COMMAND as initialize_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.model.target import Target


class InitializeTest(tests.TestCase):
    """Unit tests for `taucmdr initialize`"""

    def test_bare(self):
        self.destroy_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, initialize_cmd, ['--bare'])
        self.assertIn('Created a new project named', stdout)
        self.assertIn('Project Configuration', stdout)
        self.assertIn('No targets', stdout)
        self.assertIn('No applications', stdout)
        self.assertIn('No measurements', stdout)
        self.assertIn('No experiments', stdout)
        self.assertFalse(stderr)

    def test_initialize(self):
        self.destroy_project_storage()
        self.assertCommandReturnValue(0, initialize_cmd, [])

    def test_init_below_project(self):
        self.reset_project_storage()
        subdir = "foo"
        os.mkdir(subdir)
        os.chdir(subdir)
        self.assertNotCommandReturnValue(0, initialize_cmd, [])

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, initialize_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, initialize_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)


class PopulateProjectTest(tests.TestCase):
    """Tests for which default measurements `tau initialize` creates and selects.

    The command objects and storage are mocked so only the decision logic runs; nothing is
    created and TAU is not built.
    """
    # pylint: disable=protected-access

    _ARGV = ['--project-name', 'proj1', '--target-name', 'targ1', '--application-name', 'app1']

    def _populate(self, argv, host_os=LINUX, binutils='download'):
        """Run _populate_project() and return (measurement args by name, selected measurement name)."""
        args = initialize_cmd.parser.parse_args(self._ARGV + argv)
        controller = mock.MagicMock()
        controller.one.return_value = {'binutils_source': binutils}
        with mock.patch.object(initialize_module, 'HOST_OS', host_os), \
                mock.patch.object(Target, 'controller', return_value=controller), \
                mock.patch.object(initialize_cmd, '_safe_execute') as execute, \
                mock.patch.object(initialize_module.select_cmd, 'main') as select:
            initialize_cmd._populate_project(args)
        measurements = {}
        for call in execute.call_args_list:
            cmd, cmd_args = call[0]
            if cmd is measurement_create_cmd:
                measurements[cmd_args.name] = cmd_args
        select.assert_called_once()
        select_argv = select.call_args[0][0]
        self.assertEqual(select_argv[:4], ['--target', 'targ1', '--application', 'app1'])
        self.assertEqual(select_argv[4], '--measurement')
        return measurements, select_argv[5]

    def test_linux_defaults(self):
        """Sampling, source, compiler, and trace measurements are all created; sampling is selected."""
        measurements, selected = self._populate([])
        self.assertEqual(set(measurements), {'baseline', 'sample', 'profile', 'source-inst', 'compiler-inst', 'trace'})
        self.assertEqual(selected, 'sample')
        baseline = measurements['baseline']
        self.assertTrue(baseline.baseline)
        self.assertEqual((baseline.profile, baseline.trace, baseline.source_inst, baseline.compiler_inst),
                         ('tau', 'none', 'never', 'never'))
        self.assertFalse(baseline.mpi)
        self.assertEqual(baseline.openmp, 'ignore')
        sample = measurements['sample']
        self.assertTrue(sample.sample)
        self.assertEqual((sample.source_inst, sample.compiler_inst), ('never', 'never'))
        profile = measurements['profile']
        self.assertEqual((profile.profile, profile.trace, profile.source_inst, profile.compiler_inst),
                         ('tau', 'none', 'automatic', 'fallback'))
        self.assertEqual((measurements['source-inst'].source_inst, measurements['source-inst'].compiler_inst),
                         ('automatic', 'never'))
        self.assertEqual((measurements['compiler-inst'].source_inst, measurements['compiler-inst'].compiler_inst),
                         ('never', 'always'))
        trace = measurements['trace']
        self.assertEqual((trace.profile, trace.trace, trace.callpath, trace.source_inst, trace.compiler_inst),
                         ('none', 'otf2', 0, 'automatic', 'fallback'))

    def test_linux_without_instrumentation(self):
        """Without sampling or instrumentation only the baseline exists, and it is selected."""
        measurements, selected = self._populate(['--sample', 'F', '--source-inst', 'never', '--compiler-inst', 'never'])
        self.assertEqual(set(measurements), {'baseline'})
        self.assertEqual(selected, 'baseline')

    def test_linux_without_compiler_instrumentation(self):
        """Disabling compiler instrumentation drops only the compiler-inst measurement."""
        measurements, selected = self._populate(['--compiler-inst', 'never'])
        self.assertEqual(set(measurements), {'baseline', 'sample', 'profile', 'source-inst', 'trace'})
        self.assertEqual(selected, 'sample')
        self.assertEqual(measurements['profile'].compiler_inst, 'never')

    def test_linux_trace_only(self):
        """Profiling disabled: no baseline, only the trace measurement, which is selected."""
        measurements, selected = self._populate(['--profile', 'none'])
        self.assertEqual(set(measurements), {'trace'})
        self.assertEqual(selected, 'trace')

    def test_linux_without_binutils(self):
        """No binutils: sampling and compiler instrumentation are disabled but source instrumentation stays."""
        measurements, selected = self._populate([], binutils=None)
        self.assertEqual(set(measurements), {'baseline', 'profile', 'source-inst', 'trace'})
        self.assertEqual(selected, 'profile')
        profile = measurements['profile']
        self.assertFalse(profile.sample)
        self.assertEqual((profile.source_inst, profile.compiler_inst), ('automatic', 'never'))
        self.assertEqual(measurements['trace'].compiler_inst, 'never')

    def test_darwin_defaults(self):
        """macOS: profile and trace use runtime instrumentation only; no source or compiler measurements."""
        measurements, selected = self._populate([], host_os=DARWIN)
        self.assertEqual(set(measurements), {'baseline', 'sample', 'profile', 'trace'})
        self.assertEqual(selected, 'sample')
        for name in ('profile', 'trace'):
            self.assertEqual((measurements[name].source_inst, measurements[name].compiler_inst),
                             ('never', 'never'))
        self.assertEqual((measurements['trace'].profile, measurements['trace'].trace), ('none', 'otf2'))

    def test_darwin_without_binutils(self):
        """macOS without binutils: sampling is gone and the runtime-only profile is selected."""
        measurements, selected = self._populate([], host_os=DARWIN, binutils=None)
        self.assertEqual(set(measurements), {'baseline', 'profile', 'trace'})
        self.assertEqual(selected, 'profile')
        self.assertEqual((measurements['profile'].source_inst, measurements['profile'].compiler_inst),
                         ('never', 'never'))

    def test_darwin_without_trace(self):
        """macOS with tracing disabled creates no trace measurement."""
        measurements, _ = self._populate(['--trace', 'none'], host_os=DARWIN)
        self.assertEqual(set(measurements), {'baseline', 'sample', 'profile'})
