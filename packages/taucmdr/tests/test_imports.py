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

Checks that every TAU Commander module is capable of being imported on its own
and that no module produces deprecation warnings.
"""

import os
import pkgutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import taucmdr
from taucmdr import tests


def _module_names():
    """Return the names of TAU Commander's modules and non-vendored packages."""
    failures = []
    names = [info.name for info in pkgutil.walk_packages(taucmdr.__path__, 'taucmdr.', onerror=failures.append)
             if not info.name.startswith('taucmdr._vendor')]
    return sorted(names), failures


def _import_alone(name):
    """Import one module in a new interpreter, treating deprecation warnings as errors."""
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
    # By name, because a module can be named after a keyword, e.g. the `tau system import` command.
    code = f'import importlib; importlib.import_module({name!r})'
    proc = subprocess.run([sys.executable, '-W', 'error::DeprecationWarning', '-c', code], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return name, proc.returncode, proc.stdout


class ImportTest(tests.TestCase):
    """Import every module within :py:mod:`taucmdr` in a new interpreter. """

    def test_import_each_module(self):
        names, failures = _module_names()
        self.assertFalse(failures, f"Couldn't import packages: {failures}")
        self.assertGreater(len(names), 150)
        with ThreadPoolExecutor(max_workers=8) as pool:
            failed = [f"{name}:\n{output}" for name, retval, output in pool.map(_import_alone, names) if retval]
        self.assertFalse(failed, '\n'.join(failed))
