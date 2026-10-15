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
"""Unit tests for :py:mod:`taucmdr.cf.storage.local_file`."""

import os
import subprocess
import sys
from taucmdr import tests


class LocalFileTest(tests.TestCase):
    """Tests for :py:mod:`taucmdr.cf.storage.local_file`."""

    def test_vendored_tinydb(self):
        """TAU Commander uses its vendored TinyDB and never imports a top-level ``tinydb``."""
        # Import TAU Commander the way the `tau` command does.
        code = ("import sys\n"
                "import taucmdr.cli.commands.__main__\n"
                "from taucmdr.cf.storage import local_file\n"
                "print(local_file.tinydb.__name__)\n"
                "print('tinydb' in sys.modules)\n")
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
        out = subprocess.check_output([sys.executable, '-c', code], env=env, universal_newlines=True)
        self.assertEqual(out.split()[-2:], ['taucmdr._vendor.tinydb', 'False'])
