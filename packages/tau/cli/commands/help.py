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
"""``tau help`` subcommand."""

import os
import sys
from tau import EXIT_SUCCESS, HELP_CONTACT
from tau import logger, cli
from tau.cli import UnknownCommandError, arguments


LOGGER = logger.get_logger(__name__)

COMMAND = cli.get_command(__name__)

SHORT_DESCRIPTION = "Show help for a command or suggest actions for a file."

HELP = """
Show help for a command line or file.
"""

_GENERIC_HELP = "See 'tau --help' or contact %s for assistance" % HELP_CONTACT

_KNOWN_FILES = {'makefile': ("makefile script",
                             "See 'tau make --help' for help building with make"),
                'a.out': ("binary executable",
                          "See 'tau run --help' for help with profiling this program"),
                '.exe': ("binary executable",
                         "See 'tau run --help' for help with profiling this program")}

_MIME_HINTS = {None: 
               {None: ("unknown file", _GENERIC_HELP), 
                'gzip': ("compressed file", "Please specify an executable file")},
                'application': {None: ("unknown binary file", _GENERIC_HELP),
                                'sharedlib': ("shared library", "Please specify an executable file"),
                                'archive': ("archive file", "Please specify an executable file"),
                                'tar': ("archive file", "Please specify an executable file"),
                                'unknown': ("unknown binary file", _GENERIC_HELP)},
               'text': {None: ("unknown text file", _GENERIC_HELP),
                        'src': ("source code file", "See 'tau build --help' for help compiling this file"),
                        'hdr': ("source header file", "See 'tau build --help' for help instrumenting this file"),
                        'fortran': ("fortran source code file", "See 'tau build --help' for help compiling this file"),
                        'plain': ("text file", _GENERIC_HELP)}}


def _fuzzy_index(dct, full_key):
    """Return d[key] where ((key in k) == true) or return d[None]."""
    for key in dct.iterkeys():
        if key and (key in full_key):
            return dct[key]
    return dct[None]


def _guess_filetype(filename):
    """Return a (filetype, encoding) tuple for a file."""
    import mimetypes
    mimetypes.init()
    filetype = mimetypes.guess_type(filename)
    if not filetype[0]:
        textchars = bytearray(
            [7, 8, 9, 10, 12, 13, 27]) + bytearray(range(0x20, 0x100))
        with open(filename) as fd:
            if fd.read(1024).translate(None, textchars):
                filetype = ('application/unknown', None)
            else:
                filetype = ('text/plain', None)
    return filetype


def exit_with_help(module_name):
    """Show a subcommands help page and exit."""
    __import__(module_name)
    module = sys.modules[module_name]
    print """
%(bar)s

%(usage)s

%(bar)s

%(help)s

%(bar)s""" % {'bar': '-' * 80,
              'usage': module.parser().format_help(),
              'help': module.HELP}
    return EXIT_SUCCESS


def parser():
    """Construct a command line argument parser.
    
    Constructing the parser may cause a lot of imports as :py:mod:`tau.cli` is explored.
    To avoid possible circular imports we defer parser creation until afer all
    modules are imported, hence this function.  The parser instance is maintained as
    an attribute of the function, making it something like a C++ function static variable.
    """
    if not hasattr(parser, 'inst'):
        usage_head = "%s (<command>|<file>) [arguments]" % COMMAND
        parser.inst = arguments.get_parser(prog=COMMAND,
                                           usage=usage_head,
                                           description=SHORT_DESCRIPTION)
        parser.inst.add_argument('command', 
                                 help="A TAU command, system command, or file",
                                 metavar='(<command>|<file>)',
                                 nargs=arguments.REMAINDER)
    return parser.inst
        

def main(argv):
    """
    Program entry point
    """
    args = parser().parse_args(args=argv)
    LOGGER.debug('Arguments: %s', args)

    if not args.command:
        return exit_with_help('__main__')

    # Try to look up a Tau command's built-in help page
    cmd = '.'.join(args.command)
    try:
        return exit_with_help('commands.' + cmd)
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
            hint = "'%s' is %s %s.\n%s." % (cmd, article, desc, hint)
            raise UnknownCommandError(cmd, hint)

        # Get the filetype and try to be helpful.
        filetype, encoding = _guess_filetype(cmd)
        LOGGER.debug("'%s' has filetype (%s, %s)", cmd, filetype, encoding)
        if filetype:
            filetype, subtype = filetype.split('/')
            try:
                type_hints = _MIME_HINTS[filetype]
            except KeyError:
                hint = "TAU doesn't recognize '%s'.\nSee 'tau --help' and use the appropriate subcommand." % cmd
            else:
                desc, hint = _fuzzy_index(type_hints, subtype)
                article = 'an' if desc[0] in 'aeiou' else 'a'
                hint = "'%s' is %s %s.\n%s." % (cmd, article, desc, hint)
            raise UnknownCommandError(cmd, hint)
        else:
            raise UnknownCommandError(cmd)

    # Not a file, not a command, let's just show TAU usage and exit
    return exit_with_help('__main__')
