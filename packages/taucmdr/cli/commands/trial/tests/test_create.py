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

Functions used for unit tests of create.py.
"""

import os
import tempfile
from taucmdr import tests
from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, DARWIN
from taucmdr.cf.compiler.host import CC, NVHPC
from taucmdr.cli.commands.select import COMMAND as select_cmd
from taucmdr.cli.commands.trial.list import COMMAND as trial_list_cmd
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_cmd
from taucmdr.cli.commands.measurement.create import COMMAND as measurement_create_cmd
from taucmdr.cli.commands.measurement.edit import COMMAND as measurement_edit_cmd
from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd
from taucmdr.cli.commands.experiment.select import COMMAND as experiment_select_cmd
from taucmdr.model.project import Project
from taucmdr import util

class CreateTest(tests.TestCase):
    """Tests for :any:`trial.create`."""

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_create(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn('BEGIN targ1-app1', stdout)
        self.assertIn('END targ1-app1', stdout)
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertFalse(stderr)

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, trial_create_cmd, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, trial_create_cmd, ['--help'])
        self.assertIn('Show this help message and exit', stdout)

    def test_no_time_metric(self):
        self.reset_project_storage()
        argv = ['meas_no_time', '--metrics', 'PAPI_L2_DCM', '--source-inst', 'never']
        self.assertCommandReturnValue(0, measurement_create_cmd, argv)
        argv = ['exp2', '--target', 'targ1', '--application', 'app1', '--measurement', 'meas_no_time']
        self.assertCommandReturnValue(0, experiment_create_cmd, argv)
        self.assertCommandReturnValue(0, experiment_select_cmd, ['exp2'])
        self.assertManagedBuild(0, CC, [], 'hello.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn("TAU_METRICS=TIME,", stdout)
        self.assertFalse(stderr)

    @tests.skipIf(HOST_OS is DARWIN, "Sampling not supported on Darwin")
    def test_heap_usage_memory_alloc_sample(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/14"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, measurement_edit_cmd,
                                                       ['sample', '--heap-usage', '--memory-alloc'])
        self.assertIn("Updated measurement 'sample'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select_cmd, ['sample'])
        self.assertIn("Selected experiment 'targ1-app1-sample'", stdout)
        self.assertFalse(stderr)
        ccflags = ['-g']
        # The NVHPC compilers do not accept the -no-pie option
        if (not (util.which('nvc') and self.assertCompiler(CC) == util.which('nvc'))) :
            ccflags.append('-no-pie')
        self.assertManagedBuild(0, CC, ccflags, 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn("Trial 0 produced 1 profile files", stdout)
        self.assertIn("TAU_SHOW_MEMORY_FUNCTIONS=1", stdout)
        self.assertIn("TAU_TRACK_HEAP=1", stdout)
        self.assertFalse(stderr)
        self.assertInLastTrialData("<attribute><name>TAU_SHOW_MEMORY_FUNCTIONS</name><value>on</value></attribute>")
        self.assertInLastTrialData("<attribute><name>TAU_TRACK_HEAP</name><value>on</value></attribute>")
        self.assertInLastTrialData("Heap Memory Used (KB) at Entry")
        self.assertInLastTrialData("Heap Memory Used (KB) at Exit")
        self.assertInLastTrialData("compute_interchange")
        self.assertInLastTrialData("compute")
        # TAU bug: the dynamic malloc wrapper (e.g. tau_exec -memory) doesn't always capture malloc().
        #self.assertInLastTrialData("Heap Allocate")
        #self.assertInLastTrialData("malloc")

    def test_heap_usage_memory_alloc_profile(self):
        """https://github.com/ParaToolsInc/taucmdr/issues/14"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, measurement_edit_cmd,
                                                       ['profile', '--heap-usage', '--memory-alloc'])
        self.assertIn("Updated measurement 'profile'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select_cmd, ['profile'])
        self.assertIn("Selected experiment 'targ1-app1-profile'", stdout)
        self.assertFalse(stderr)
        meas = Project.selected().experiment().populate('measurement')
        self.assertTrue(meas['heap_usage'])
        self.assertTrue(meas['memory_alloc'])
        self.assertManagedBuild(0, CC, [], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn("Trial 0 produced 1 profile files", stdout)
        self.assertIn("TAU_SHOW_MEMORY_FUNCTIONS=1", stdout)
        self.assertIn("TAU_TRACK_HEAP=1", stdout)
        self.assertFalse(stderr)
        self.assertInLastTrialData("<attribute><name>TAU_SHOW_MEMORY_FUNCTIONS</name><value>on</value></attribute>")
        self.assertInLastTrialData("<attribute><name>TAU_TRACK_HEAP</name><value>on</value></attribute>")
        self.assertInLastTrialData("Heap Memory Used (KB) at Entry")
        self.assertInLastTrialData("Heap Memory Used (KB) at Exit")
        self.assertInLastTrialData("Heap Allocate")
        self.assertInLastTrialData("compute_interchange")
        self.assertInLastTrialData("compute")
        self.assertInLastTrialData("malloc")

    def test_without_libelf(self):
        self.reset_project_storage(['--libelf', 'none'])
        self.assertManagedBuild(0, CC, [], 'hello.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn('BEGIN targ1-app1', stdout)
        self.assertIn('END targ1-app1', stdout)
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertFalse(stderr)

    def test_without_libdwarf(self):
        self.reset_project_storage(['--libdwarf', 'none'])
        self.assertManagedBuild(0, CC, [], 'hello.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn('BEGIN targ1-app1', stdout)
        self.assertIn('END targ1-app1', stdout)
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertFalse(stderr)

    def sample_resolution_helper(self, option):
        self.reset_project_storage()
        self.assertIn(option, ['file', 'line', 'function'])
        stdout, stderr = self.assertCommandReturnValue(0, measurement_edit_cmd,
                                            ['sample', '--sample-resolution', option])
        self.assertIn("Updated measurement 'sample'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select_cmd, ['sample'])
        self.assertIn("Selected experiment 'targ1-app1-sample'", stdout)
        self.assertFalse(stderr)
        self.assertManagedBuild(0, CC, [], 'matmult.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        self.assertIn("Trial 0 produced 1 profile files", stdout)
        self.assertIn("TAU_EBS_RESOLUTION="+option, stdout)
        self.assertFalse(stderr)

    def test_sample_resolution_file(self):
        self.sample_resolution_helper('file')

    def test_sample_resolution_function(self):
        self.sample_resolution_helper('function')

    def test_sample_resolution_line(self):
        self.sample_resolution_helper('line')

    @tests.skipIf(HOST_OS is DARWIN, "Sampling not supported on Darwin")
    def test_system_load_sample(self):
        """Test TAU_TRACK_LOAD w/ sampling"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, measurement_edit_cmd,
                                                       ['sample', '--system-load'])
        self.assertIn("Updated measurement 'sample'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select_cmd, ['sample'])
        self.assertIn("Selected experiment 'targ1-app1-sample'", stdout)
        self.assertFalse(stderr)

    def test_system_load_profile(self):
        """Test TAU_TRACK_LOAD w/ profiling"""
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, measurement_edit_cmd,
                                                       ['profile', '--system-load'])
        self.assertIn("Updated measurement 'profile'", stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, select_cmd, ['profile'])
        self.assertIn("Selected experiment 'targ1-app1-profile'", stdout)
        self.assertFalse(stderr)

    def test_tau_dir(self):
        """Test --tau_dir option"""
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        test_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as path:
            os.chdir(path)
            stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, [test_dir+'/a.out', '--tau-dir', test_dir])
            self.assertIn('BEGIN targ1-app1', stdout)
            self.assertIn('END targ1-app1', stdout)
            self.assertIn('Trial 0 produced', stdout)
            self.assertIn('profile files', stdout)
            self.assertFalse(stderr)
            os.chdir(test_dir)

    def test_description(self):
        """Test --description option"""
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, trial_create_cmd, ['--description', 'test desc', './a.out'])
        stdout, stderr = self.assertCommandReturnValue(0, trial_list_cmd, [])
        self.assertIn('test desc', stdout)

    @tests.skipUnless(util.which('python'), "Python 2 or 3 required for this test")
    def test_run_python(self):
        self.reset_project_storage(['--python', 'T', '--python-interpreter', 'python'])
        self.copy_testfile('firstprime.py')
        test_dir = os.getcwd()
        stdout, stderr = self.assertCommandReturnValue(
            0, trial_create_cmd, ['python', os.path.join(test_dir, 'firstprime.py')]
        )
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        self.assertRegex(stdout, '-tau-python-interpreter=/.*/python[23]?(\r\n?|\n| )')
        self.assertFalse(stderr)
        self.assertInLastTrialData("first_prime_after")

    @tests.skipUnless(util.which('python2'), "Python 2 required for this test")
    def test_run_python2(self):
        self.reset_project_storage(['--python', 'T', '--python-interpreter', 'python2'])
        self.copy_testfile('firstprime.py')
        test_dir = os.getcwd()
        stdout, stderr = self.assertCommandReturnValue(
            0, trial_create_cmd, ['python2', os.path.join(test_dir, 'firstprime.py')]
        )
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        # self.assertRegex(stdout, '-tau-python-interpreter=/.*/python3')
        self.assertFalse(stderr)
        self.assertInLastTrialData("first_prime_after")

    @tests.skipUnless(util.which('python3'), "Python 3 required for this test")
    def test_run_python3(self):
        self.reset_project_storage(['--python', 'T', '--python-interpreter', 'python3'])
        self.copy_testfile('firstprime.py')
        test_dir = os.getcwd()
        stdout, stderr = self.assertCommandReturnValue(
            0, trial_create_cmd, ['python3', os.path.join(test_dir, 'firstprime.py')]
        )
        self.assertIn('Trial 0 produced', stdout)
        self.assertIn('profile files', stdout)
        # self.assertRegex(stdout, '-tau-python-interpreter=/.*/python3')
        self.assertFalse(stderr)
        self.assertInLastTrialData("first_prime_after")

    @tests.skipUnless(util.which('nvc'), "NVHPC compilers required for this test")
    def test_run_openacc(self):
        self.reset_project_storage(['--openacc', 'T', '--cuda', 'T'])
        self.copy_testfile('jacobi.c')
        self.copy_testfile('timer.h')
        test_dir = os.getcwd()
        self.assertManagedBuild(0, CC, ['-acc', '-g', '-o', 'jacobi'], 'jacobi.c')
        stdout, stderr = self.assertCommandReturnValue(0, trial_create_cmd, [os.path.join(test_dir, 'jacobi')])
        self.assertIn('Trial 0 produced 2 profile files', stdout)
        self.assertFalse(stderr)
