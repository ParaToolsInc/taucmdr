# -*- coding: utf-8 -*-
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

Functions used for unit tests of list.py.
"""
#pylint: disable=missing-docstring

import shutil
import unittest
from taucmdr import tests, TAU_HOME
from taucmdr.cf.platforms import HOST_ARCH
from taucmdr.cf.compiler.host import CC
from taucmdr.cli.commands import build
from taucmdr.cli.commands.trial.list import COMMAND as LIST_COMMAND
from taucmdr.cli.commands.trial.create import COMMAND as CREATE_COMMAND


class ListTest(tests.TestCase):
    """Tests for :any:`trial.list`."""
    
    @unittest.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_list(self):
        self.reset_project_storage(project_name='proj1')
        shutil.copyfile(TAU_HOME+'/.testfiles/hello.c', tests.get_test_workdir()+'/hello.c')
        cc_cmd = self.get_compiler(CC)
        argv = [cc_cmd, 'hello.c']
        self.exec_command(build.COMMAND, argv)
        self.exec_command(CREATE_COMMAND, ['./a.out'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, [])
        self.assertIn('./a.out', stdout)
        self.assertIn('0', stdout)
        self.assertFalse(stderr)

    def test_wrongnumber(self):
        self.reset_project_storage(project_name='proj1')
        stdout, stderr = self.assertNotCommandReturnValue(0, LIST_COMMAND, ['0'])
        self.assertIn("No trial with number='0'", stderr)
        self.assertFalse(stdout)
