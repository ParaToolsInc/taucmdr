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
"""Unit tests for for the test runner itself."""

import os
import subprocess
import sys
import taucmdr
from taucmdr import tests

_RUN_TESTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(taucmdr.__file__)))),
                          'scripts', 'run_tests.py')


class RunTestsTest(tests.TestCase):
    """Tests for ``scripts/run_tests.py``."""

    def _run(self, *args):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
        proc = subprocess.run([sys.executable, _RUN_TESTS] + list(args), env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, universal_newlines=True, check=False)
        test_ids = [line for line in proc.stdout.splitlines() if line.startswith('taucmdr.')]
        return proc.returncode, test_ids, proc.stdout

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_package_name(self):
        """Listing tests by package name lists the tests in every test module under it."""
        retval, test_ids, output = self._run('--list', 'taucmdr.model.tests')
        self.assertEqual(retval, 0, output)
        self.assertIn('taucmdr.model.tests.test_target.TargetTest.test_unknown_host_arch', test_ids)
        self.assertIn('taucmdr.model.tests.test_compiler.CompilerTest.test_unknown_family', test_ids)

    @tests.skipUnless(os.path.exists(_RUN_TESTS), "Needs a source checkout")
    def test_name_without_tests(self):
        """Listing a package that holds no tests is an error."""
        for args in (['--list', 'taucmdr.error'], ['taucmdr.error']):
            retval, test_ids, output = self._run(*args)
            self.assertEqual(retval, 1, output)
            self.assertEqual(test_ids, [])
            self.assertIn('taucmdr.error', output)
