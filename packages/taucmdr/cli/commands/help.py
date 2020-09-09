# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
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
"""``help`` subcommand."""

from __future__ import absolute_import
import os
import mimetypes
import re
from taucmdr import EXIT_SUCCESS, HELP_CONTACT, TAUCMDR_SCRIPT
from taucmdr import logger, util, cli
from taucmdr.cli import arguments, UnknownCommandError
from taucmdr.cli.command import AbstractCommand
from six.moves import range


LOGGER = logger.get_logger(__name__)

_SCRIPT_CMD = os.path.basename(TAUCMDR_SCRIPT)

_GENERIC_HELP = "See '{} --help' or contact {} for assistance".format(_SCRIPT_CMD, HELP_CONTACT)

_KNOWN_FILES = {'makefile': ("makefile script",
                             "See 'taucmdr make --help' for help building with make"),
                'a.out': ("binary executable",
                          "See 'taucmdr run --help' for help with profiling this program"),
                '.exe': ("binary executable",
                         "See 'taucmdr run --help' for help with profiling this program")}

_MIME_HINTS = {None:
               {None: ("unknown file", _GENERIC_HELP),
                'gzip': ("compressed file", "Please specify an executable file")},
               'application': {None: ("unknown binary file", _GENERIC_HELP),
                               'sharedlib': ("shared library",
                                             "Please specify an executable file"),
                               'archive': ("archive file",
                                           "Please specify an executable file"),
                               'tar': ("archive file",
                                       "Please specify an executable file"),
                               'unknown': ("unknown binary file", _GENERIC_HELP)},
               'text': {None: ("unknown text file", _GENERIC_HELP),
                        'src': ("source code file",
                                "See 'taucmdr build --help' for help compiling this file"),
                        'hdr': ("source header file",
                                "See 'taucmdr build --help' for help instrumenting this file"),
                        'fortran': ("fortran source code file",
                                    "See 'taucmdr build --help' for help compiling this file"),
                        'plain': ("text file", _GENERIC_HELP)}}


def _fuzzy_index(dct, full_key):
    """Return d[key] where ((key in k) == true) or return d[None]."""
    for key in dct:
        if key and (key in full_key):
            return dct[key]
    return dct[None]


def _guess_filetype(filename):
    """Return a (filetype, encoding) tuple for a file."""
    mimetypes.init()
    filetype = mimetypes.guess_type(filename)
    if not filetype[0]:
        textchars = bytearray([7, 8, 9, 10, 12, 13, 27]) + bytearray(list(range(0x20, 0x100)))
        with open(filename,mode='rb') as fd:
            if re.sub(textchars, b'', fd.read(1024)):
                filetype = ('application/unknown', None)
            else:
                filetype = ('text/plain', None)
    return filetype


class HelpCommand(AbstractCommand):
    """``help`` subcommand."""

    @staticmethod
    def exit_with_help(name):
        """Show a subcommands help page and exit."""
        cmd_obj = cli.find_command(name)
        command = cmd_obj.command
        parts = [
            "", util.hline("Help: " + command),
            cmd_obj.help_page,
            "", util.hline("Usage: " + command),
            cmd_obj.usage]
        util.page_output('\n'.join(parts))
        return EXIT_SUCCESS

    @staticmethod
    def exit_with_fullhelp():
        """Show a recursive help page for all commands and exit."""
        help_output = ''
        for cmd_name in cli.get_all_commands():
            name = cli.command_from_module_name(cmd_name)
            cmd_obj = cli.find_command(name.split()[1:])
            command = cmd_obj.command
            parts = ["", util.hline("Help: " + command),
                     cmd_obj.help_page,
                     "", util.hline("Usage: " + command),
                     cmd_obj.usage]
            help_output += '\n'.join(parts)
        util.page_output(help_output)
        return EXIT_SUCCESS

    def _construct_parser(self):
        usage_head = "%s <command>|<file>|all [arguments]" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage_head, description=self.summary)
        parser.add_argument('command',
                            help="A TAU command, system command, or file.",
                            metavar='(<command>|<file>|all)',
                            nargs='+')
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        if not args.command:
            return self.exit_with_help([])
        if args.command[0] == 'all':
            return self.exit_with_fullhelp()

        # Try to look up a Tau command's built-in help page
        cmd = args.command
        try:
            return self.exit_with_help(cmd)
        except ImportError:
            pass

        # Is this a file?
        if os.path.exists(cmd):
            # Do we recognize the file name?
            try:
                desc, hint = _fuzzy_index(_KNOWN_FILES, cmd.lower())
            except KeyError:
                pass
            else:
                article = 'an' if desc[0] in 'aeiou' else 'a'
                hint = "'{}' is {} {}.\n{}.".format(cmd, article, desc, hint)
                raise UnknownCommandError(cmd, hint)

            # Get the filetype and try to be helpful.
            filetype, encoding = _guess_filetype(cmd)
            self.logger.debug("'%s' has filetype (%s, %s)", cmd, filetype, encoding)
            if filetype:
                filetype, subtype = filetype.split('/')
                try:
                    type_hints = _MIME_HINTS[filetype]
                except KeyError:
                    hint = "TAU doesn't recognize '%s'.\nSee 'taucmdr --help' and use the appropriate subcommand." % cmd
                else:
                    desc, hint = _fuzzy_index(type_hints, subtype)
                    article = 'an' if desc[0] in 'aeiou' else 'a'
                    hint = "'{}' is {} {}.\n{}.".format(cmd, article, desc, hint)
                raise UnknownCommandError(cmd, hint)
            else:
                raise UnknownCommandError(cmd)

        LOGGER.error("Cannot identify '%s' as a command or filename.")
        return self.exit_with_help('__main__')

COMMAND = HelpCommand(__name__, summary_fmt="Show help for a command or suggest actions for a file.")
