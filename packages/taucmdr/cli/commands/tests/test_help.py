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
"""Test functions.

Functions used for unit tests of help.py.
"""

import os
import tempfile
from unittest import mock

from taucmdr import EXIT_SUCCESS, tests
from taucmdr.cli import SCRIPT_COMMAND, UnknownCommandError
from taucmdr.cli.commands.help import COMMAND as help_command

class HelpTest(tests.TestCase):
    """Unit tests for `taucmdr help`"""

    def test_help(self):
        self.reset_project_storage()
        argv = ['build']
        self.assertCommandReturnValue(0, help_command, argv)

    def test_h_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, help_command, ['-h'])
        self.assertIn('Show this help message and exit', stdout)

    def test_help_arg(self):
        self.reset_project_storage()
        stdout, _ = self.assertCommandReturnValue(0, help_command, ['--help'])
        self.assertIn('Show this help message and exit', stdout)

    def test_unknown_name(self):
        """Help for a name that isn't a command produces an unknown command error."""
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['notacommandorfile'])
        self.assertIn('notacommandorfile', str(context.exception))

    def test_known_file_name(self):
        """Help for a makefile suggests the build command."""
        with open('Makefile', 'w', encoding='utf-8') as fout:
            fout.write('all:\n')
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['Makefile'])
        message = context.exception.message
        self.assertIn('Makefile', message)
        self.assertIn('makefile script', message)
        self.assertIn('build --help', message)

    def test_source_file(self):
        """Help for a source file suggests the build command."""
        self.copy_testfile('hello.c')
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['hello.c'])
        message = context.exception.message
        self.assertIn('source code file', message)
        self.assertIn('build --help', message)

    def test_source_file_types(self):
        """Source files are recognized by extension, whether or not the host has a mime.types file."""
        expected = {'prog.c': 'a source code file', 'prog.cpp': 'a source code file', 'prog.C': 'a source code file',
                    'prog.h': 'a source header file', 'prog.hpp': 'a source header file',
                    'prog.f90': 'a fortran source code file', 'prog.F90': 'a fortran source code file'}
        with mock.patch('mimetypes.knownfiles', []):
            for name, description in expected.items():
                with self.subTest(name=name):
                    with open(name, 'w', encoding='utf-8') as fout:
                        fout.write('int x;\n')
                    with self.assertRaises(UnknownCommandError) as context:
                        help_command.main([name])
                    self.assertIn(f"'{name}' is {description}.", context.exception.message)

    def test_unknown_binary_file(self):
        """A binary file without a recognized extension is identified as binary."""
        with open('myprog', 'wb') as fout:
            fout.write(b'\x7fELF\x02\x01\x01\x00\x00\x00')
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['myprog'])
        self.assertIn("'myprog' is an unknown binary file.", context.exception.message)

    def test_unknown_text_file(self):
        """A text file without a recognized extension is identified as text."""
        with open('notes', 'w', encoding='utf-8') as fout:
            fout.write('some notes\n')
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['notes'])
        self.assertIn("'notes' is a text file.", context.exception.message)

    def test_command_before_file(self):
        """A command name is looked up as a command even when a file has the same name."""
        with open('target', 'w', encoding='utf-8') as fout:
            fout.write('not a command\n')
        with mock.patch('taucmdr.util.page_output') as page_output:
            self.assertEqual(help_command.main(['target']), EXIT_SUCCESS)
        self.assertIn(f'Help: {SCRIPT_COMMAND} target', page_output.call_args[0][0])

    def test_directory_name(self):
        """Help for a directory that isn't a command produces an unknown command error."""
        os.mkdir('notacommanddir')
        with self.assertRaises(UnknownCommandError) as context:
            help_command.main(['notacommanddir'])
        self.assertIn('notacommanddir', str(context.exception))

    def test_file_hint_outside_project(self):
        """``tau help <file>`` prints the file hint without needing a project."""
        backend = os.environ.get('__TAUCMDR_DB_BACKEND__')
        with tempfile.TemporaryDirectory() as workdir, tempfile.TemporaryDirectory() as user_prefix:
            with open(os.path.join(workdir, 'Makefile'), 'w', encoding='utf-8') as fout:
                fout.write('all:\n')
            proc = tests.run_tau_subprocess(['help', 'Makefile'], backend, workdir, user_prefix,
                                            env={'__TAUCMDR_DISABLE_PAGER__': '1'})
        self.assertCleanExit(proc)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('makefile script', proc.stdout + proc.stderr)
        self.assertNotIn('Project directory not found', proc.stdout + proc.stderr)
