# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, ParaTools, Inc.
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

Functions used for unit tests of edit.py.
"""
#pylint: disable=missing-docstring

from taucmdr import tests
from taucmdr.cf.platforms import HOST_ARCH
from taucmdr.cf.compiler.host import CC
from taucmdr.cli.commands.trial.renumber import COMMAND as RENUMBER_COMMAND
from taucmdr.cli.commands.trial.create import COMMAND as CREATE_COMMAND
from taucmdr.cli.commands.trial.list import COMMAND as LIST_COMMAND
from taucmdr.cli.commands.trial.edit import COMMAND as EDIT_COMMAND
from taucmdr.cli.commands.trial.delete import COMMAND as DELETE_COMMAND

class RenumberTest(tests.TestCase):
    """Tests for :any:`trial.renumber`."""

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_newtrial(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
        self.assertCommandReturnValue(0, EDIT_COMMAND, ['0', '--description', 'desc0'])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['0', '--to', '1'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, [])
        self.assertIn('./a.out', stdout)
        self.assertIn('  1  ', stdout)
        self.assertIn('desc0', stdout)
        self.assertNotIn('  0  ', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_swaptrials(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        for i in xrange(3):
            self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
            self.assertCommandReturnValue(0, EDIT_COMMAND, [str(i), '--description', 'desc%s' %i])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['0', '1', '2', '--to', '1', '2', '0'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '0')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc2', stdout)
        self.assertNotIn('desc0', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '1')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc0', stdout)
        self.assertNotIn('desc1', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '2')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc1', stdout)
        self.assertNotIn('desc2', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)

    @tests.skipIf(HOST_ARCH.is_bluegene(), "Test skipped on BlueGene")
    def test_compresstrials(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        for i in xrange(13):
            self.assertCommandReturnValue(0, CREATE_COMMAND, ['./a.out'])
            self.assertCommandReturnValue(0, EDIT_COMMAND, [str(i), '--description', 'desc%s' %i])
        self.assertCommandReturnValue(0, DELETE_COMMAND, ['9', '11'])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['12', '--to', '9'])
        self.assertCommandReturnValue(0, RENUMBER_COMMAND, ['13', '--to', '11'])
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '8')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc8', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '9')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc12', stdout)
        self.assertNotIn('desc9', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
        stdout, stderr = self.assertCommandReturnValue(0, LIST_COMMAND, '11')
        self.assertIn('./a.out', stdout)
        self.assertIn('desc13', stdout)
        self.assertNotIn('desc11', stdout)
        self.assertIn('Selected experiment:', stdout)
        self.assertFalse(stderr)
