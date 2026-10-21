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

Checks that ``requirements.txt`` lists the third-party packages that are imported
by TAU Commander.
"""

import ast
import os
import re
import sys
from taucmdr import tests

_PACKAGE_DIR = os.path.join(tests.REPO_DIR, 'packages', 'taucmdr')
_REQUIREMENTS = os.path.join(tests.REPO_DIR, 'requirements.txt')


def _imported_packages():
    """Return the lower-case top-level names of the third-party modules TAU Commander's code imports."""
    names = set()
    # Walk the packages directory, locating every non-vendored .py file.
    # For each, parse it, extract the import statements, and return the
    # imported modules that are not part of the standard library.
    for dirpath, dirnames, filenames in os.walk(_PACKAGE_DIR):
        dirnames[:] = [name for name in dirnames if name != '_vendor']
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            path = os.path.join(dirpath, filename)
            with open(path, encoding='utf-8') as fin:
                tree = ast.parse(fin.read(), path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names.add(node.module.split('.')[0])
    return {name.lower() for name in names if name not in sys.stdlib_module_names and name != 'taucmdr'}


def _required_packages():
    """Return the lower-case names of the packages listed in ``requirements.txt``."""
    names = set()
    with open(_REQUIREMENTS, encoding='utf-8') as fin:
        for line in fin:
            requirement = line.split('#')[0].strip()
            if requirement:
                names.add(re.match(r'[A-Za-z0-9_.-]+', requirement).group().lower())
    return names


class RequirementsTest(tests.TestCase):
    """Tests for ``requirements.txt``."""

    @tests.skipUnless(hasattr(sys, 'stdlib_module_names'), "Python 3.10 or newer required")
    def test_requirements_match_imports(self):
        """requirements.txt lists exactly the third-party packages TAU Commander imports."""
        self.assertEqual(_required_packages(), _imported_packages())
