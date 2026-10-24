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
"""Unit tests for taucmdr.cf.platforms"""

import os
import platform
import tempfile
from unittest import mock

from taucmdr import tests
from taucmdr.tests import TestCase
from taucmdr.cf.platforms import (Architecture, OperatingSystem, TauMagic, ARM64, CRAY_CNL, DARWIN, HOST_OS, LINUX,
                                  SHARED_LIBRARY_SUFFIX)

_PATCH_PLATFORM = """
import platform
platform.machine = lambda: {machine!r}
platform.system = lambda: {system!r}
"""

_SHARED_LIBRARY_MODULES = ('gotcha', 'libotf2', 'scorep', 'sqlite3', 'ompt')

_JOB_VARIABLES = ('SLURM_JOB_ID', 'PBS_JOBID', 'PALS_APID', 'FLUX_JOB_ID', 'COBALT_JOBID', 'LSB_JOBID')


def _clear_job_variables():
    for var in _JOB_VARIABLES:
        os.environ.pop(var, None)


class PlatformsTest(TestCase):
    """Unit tests for taucmdr.cf.platforms"""

    def test_architecture_detect(self):
        self.assertTrue(Architecture.detect())

    def test_operating_system_detect(self):
        self.assertTrue(OperatingSystem.detect())

    def test_tau_magic_detect(self):
        self.assertTrue(TauMagic.detect())

    def test_supported_platforms(self):
        """Each supported host platform maps to the expected TAU magic word."""
        expected = {('x86_64', 'Linux'): 'x86_64',
                    ('x86_64', 'CNL'): 'craycnl',
                    ('x86_64', 'Darwin'): 'apple',
                    ('aarch64', 'Linux'): 'arm64_linux',
                    ('aarch64', 'Darwin'): 'arm64_apple',
                    ('aarch64', 'CNL'): 'craycnl',
                    ('ppc64le', 'Linux'): 'ibm64linux'}
        for (arch, opsys), magic in expected.items():
            found = TauMagic.find((Architecture.find(arch), OperatingSystem.find(opsys)))
            self.assertEqual(found.name, magic, f"({arch}, {opsys})")

    def test_removed_platforms(self):
        """Architectures and operating systems that TAU Commander doesn't support aren't defined."""
        for arch in ('KNC', 'KNL', 'BGL', 'BGP', 'BGQ', 'ibm64', 'ppc64', 'aarch32'):
            with self.assertRaises(KeyError, msg=arch):
                Architecture.find(arch)
        for opsys in ('CNK', 'Android'):
            with self.assertRaises(KeyError, msg=opsys):
                OperatingSystem.find(opsys)

    def test_cray_login_outside_job(self):
        """Outside any job, a Cray node is treated as a login node."""
        with mock.patch.dict(os.environ):
            _clear_job_variables()
            self.assertTrue(CRAY_CNL.is_cray_login())

    def test_cray_login_in_job(self):
        """Inside a Slurm, PBS, PALS, Flux, Cobalt or LSF job, a Cray node isn't treated as a login node."""
        for var in _JOB_VARIABLES:
            with mock.patch.dict(os.environ):
                _clear_job_variables()
                os.environ[var] = '1'
                self.assertFalse(CRAY_CNL.is_cray_login(), var)

    def test_cray_login_aprun(self):
        """A Cray node with aprun on PATH is still a login node outside a job."""
        with mock.patch('taucmdr.util.which', side_effect=lambda name: '/usr/bin/aprun' if name == 'aprun' else None), \
                mock.patch.dict(os.environ):
            _clear_job_variables()
            self.assertTrue(CRAY_CNL.is_cray_login())

    def test_not_cray_login(self):
        self.assertFalse(LINUX.is_cray_login())
        self.assertFalse(DARWIN.is_cray_login())

    # The below code tests platform detection without requiring that we are actually running
    # on the given platform 
    def _run_patched(self, machine, system, code, cray=False):
        """Run `code` in a new process after patching `platform.machine` and `platform.system`."""
        script = _PATCH_PLATFORM.format(machine=machine, system=system) + code
        with tempfile.TemporaryDirectory() as prefix:
            env = tests.storage_env('tinydb', prefix)
            env['PE_ENV'] = 'GNU' if cray else None
            env['CRAYOS_VERSION'] = None
            proc = tests.run_python_subprocess(['-c', script], env=env, cwd=prefix)
        self.assertSucceeded(proc)
        return proc.stdout.split()

    def test_arm64_alias(self):
        """macOS reports Apple silicon as arm64, which is the same architecture as aarch64."""
        saved = Architecture.__dict__['_detect']
        try:
            del Architecture._detect
            with mock.patch.object(platform, 'machine', return_value='arm64'):
                self.assertIs(Architecture.detect(), ARM64)
            del Architecture._detect
            with mock.patch.object(platform, 'machine', return_value='aarch64'):
                self.assertIs(Architecture.detect(), ARM64)
        finally:
            Architecture._detect = saved

    def test_arm64_apple_detected(self):
        out = self._run_patched('arm64', 'Darwin',
                                "from taucmdr.cf.platforms import HOST_ARCH, HOST_OS, HOST_TAU_MAGIC\n"
                                "print(HOST_ARCH.name, HOST_OS.name, HOST_TAU_MAGIC.name)\n")
        self.assertEqual(out, ['aarch64', 'Darwin', 'arm64_apple'])

    def test_cray_aarch64_detected(self):
        out = self._run_patched('aarch64', 'Linux',
                                "from taucmdr.cf.platforms import HOST_OS, HOST_TAU_MAGIC\n"
                                "print(HOST_OS.name, HOST_TAU_MAGIC.name)\n", cray=True)
        self.assertEqual(out, ['CNL', 'craycnl'])

    def test_cray_x86_64_detected(self):
        out = self._run_patched('x86_64', 'Linux',
                                "from taucmdr.cf.platforms import HOST_OS, HOST_TAU_MAGIC\n"
                                "print(HOST_OS.name, HOST_TAU_MAGIC.name)\n", cray=True)
        self.assertEqual(out, ['CNL', 'craycnl'])

    def test_shared_library_suffix(self):
        self.assertEqual(SHARED_LIBRARY_SUFFIX, 'dylib' if HOST_OS is DARWIN else 'so')

    def test_shared_library_names_on_darwin(self):
        code = ("import importlib\n"
                f"for name in {_SHARED_LIBRARY_MODULES!r}:\n"
                "    module = importlib.import_module('taucmdr.cf.software.%s_installation' % name)\n"
                "    for libs in module.LIBRARIES.values():\n"
                "        for lib in libs:\n"
                "            print(name + ':' + lib)\n")
        libs = [line.split(':') for line in self._run_patched('arm64', 'Darwin', code)]
        self.assertFalse([lib for _, lib in libs if lib.endswith('.so')])
        for name in _SHARED_LIBRARY_MODULES:
            self.assertTrue([lib for module, lib in libs if module == name and lib.endswith('.dylib')], name)
