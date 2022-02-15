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

Asserts that pylint score doesn't drop below minimum.
"""

import os
import sys
import subprocess
import re
from taucmdr import TAUCMDR_HOME
from taucmdr import tests

MAX_REPORT_LENGTH = 100065500
REPORT_FILE = os.path.join(TAUCMDR_HOME, "pylint.md")
PYLINT_REPORT_TEMPLATE = \
"""
## Pylint Output

### Report

{report}

<details>
  <summary> Per-file output (click to expand) </summary>

<pre>
{details}
</pre>

</details>

<details>
  <summary> Stderr </summary>

<pre>
{stderr}
</pre>

</details>
"""
REPORT_START = re.compile(r'^ *[Rr]eport *[\r\n] *====== *$', re.MULTILINE)
ROW_SEPARATOR = re.compile(r'^ *([+]-{5,}[+]?)+ *$', re.MULTILINE)
HEADER_SEPARATOR = re.compile(r'^ *[+](={5,}[+])+ *$', re.MULTILINE)
MODULE_DETAIL_HEADER = re.compile(r'^ *[*]{3,25} +Module +taucmdr([.]\w+)* *$', re.MULTILINE)
TAUCMDR_MODULE = re.compile(r' +(taucmdr([.]\w+)+)')
PYLINT_H2 = re.compile(r'^(?P<header> *(%|\w+)( +(/|\w+))* *)[\r\n]( *-{4,}) *$', re.MULTILINE)


class PylintTest(tests.TestCase):
    """Runs Pylint to make sure the code scores at least 9.0"""

    @staticmethod
    def _format_pylint_report(stdout, stderr):
        """Formats pylint output as pretty markdown"""
        _details, _report = REPORT_START.split(stdout, maxsplit=1)
        _report = PYLINT_H2.sub(r'#### \g<header>', _report)
        _report_lines = []
        for line in _report.splitlines():
            if ROW_SEPARATOR.search(line):
                continue
            elif HEADER_SEPARATOR.search(line):
                trans_table = str.maketrans("+=", "|-")
                _report_lines.append(line.translate(trans_table))
            else:
                _report_lines.append(line)
        _report_length_left =\
            MAX_REPORT_LENGTH - (len(PYLINT_REPORT_TEMPLATE) + len("\n".join(_report_lines)) + len(stderr) + 30)
        _details = _details.strip()
        if len(_details) > _report_length_left:
            _details = _details[0:_report_length_left].strip()
            _details, _ = _details.rsplit("\n", maxsplit=1)
            _details = _details + "\n ... __*TRUNCATED*__ ...\n"
        return PYLINT_REPORT_TEMPLATE.format(
            report="\n".join(_report_lines),
            details=_details.strip(),
            stderr=stderr.strip())

    def run_pylint(self, *args):
        cmd = [sys.executable, "-m", "pylint", '--rcfile=' + os.path.join(TAUCMDR_HOME, "pylintrc")]
        cmd.extend(args)
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   shell=False, env=env, universal_newlines=True)
        return process.communicate()

    def test_pylint_version(self):
        stdout, stderr = self.run_pylint('--version')
        self.assertRegex(stderr, '(^ *[Uu]sing config file .*pylintrc.*)|(^$)')
        try:
            if re.search(r'__main__.py', stdout):
                version_parts = stdout.split(',')[0].split('__main__.py ')[1].split('.')
            else:
                version_parts = stdout.split('\n')[0].split('pylint')[1].split('.')
        except IndexError:
            self.fail("Unable to parse pylint version string:\n%s" % stdout)
        version = tuple(int(x) for x in version_parts)
        self.assertGreaterEqual(version, (1, 5, 2), "Pylint version %s is too old!" % str(version))

    def test_pylint(self):
        stdout, stderr = self.run_pylint(os.path.join(TAUCMDR_HOME, "packages", "taucmdr"))
        with open(REPORT_FILE, "w") as lint_msg_file:
            try:
                lint_msg = self._format_pylint_report(stdout, stderr)
                lint_msg_file.write(str(lint_msg))
            finally:
                lint_msg_file.close()
        self.assertRegex(stderr, '(^ *[Uu]sing config file .*pylintrc.*)|(^$)')
        self.assertIn('Your code has been rated at', stdout)
        score = float(stdout.split('Your code has been rated at')[1].split('/10')[0])
        self.assertGreaterEqual(
            score,
            9.0,
            f"Pylint score {score}/10 is too low!\nPlease see report output for details:\n    {REPORT_FILE}")
