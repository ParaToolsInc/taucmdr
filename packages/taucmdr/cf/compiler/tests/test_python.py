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
"""Tests for recognizing Python interpreters by name."""

import os
import sys
import tempfile

from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompiler, _CompilerFamily, _without_minor_version
from taucmdr.cf.compiler.python import PY, PYTHON3


def versioned_python_link():
    """Return the path of a new link named ``python3.<minor>`` to this Python, in the test's work directory."""
    link = os.path.join(tempfile.mkdtemp(dir=os.getcwd()), f'python3.{sys.version_info[1]}')
    os.symlink(sys.executable, link)
    return link


class VersionedNameTest(tests.TestCase):
    """Tests for interpreter commands whose names include a minor version."""

    def test_versioned_name(self):
        """``python3.<minor>`` is recognized as a Python 3 interpreter."""
        link = versioned_python_link()
        self.assertIs(_CompilerFamily.probe(link), PYTHON3)
        info = InstalledCompiler.probe(link, role=PY).info
        self.assertIs(info.family, PYTHON3)
        self.assertEqual(info.command, 'python3')

    def test_without_minor_version(self):
        self.assertEqual(_without_minor_version('python3.12'), 'python3')
        self.assertEqual(_without_minor_version('python3'), 'python3')
        self.assertEqual(_without_minor_version('gcc-13'), 'gcc-13')

    def test_python2_versioned_refused(self):
        """``python2.7`` isn't taken for a Python 3 interpreter."""
        script = os.path.join(tempfile.mkdtemp(dir=os.getcwd()), 'python2.7')
        with open(script, 'w', encoding='utf-8') as fout:
            fout.write('#!/bin/sh\necho "Python 2.7.18"\n')
        os.chmod(script, 0o755)
        with self.assertRaisesRegex(ConfigurationError, 'Cannot determine compiler family'):
            InstalledCompiler.probe(script, role=PY)
