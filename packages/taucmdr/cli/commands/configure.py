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
from __future__ import print_function

import six

"""``configure`` subcommand."""

from taucmdr import EXIT_SUCCESS
from taucmdr import configuration
from taucmdr.error import InternalError
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand
from taucmdr.cf.storage.levels import PROJECT_STORAGE



class ConfigureCommand(AbstractCommand):
    """``configure`` subcommand."""

    def _construct_parser(self):
        """Constructs the command line argument parser.
          
        Returns:
            A command line argument parser instance.
        """
        usage = "%s [arguments] <key> <value>" % self.command
        parser = arguments.get_parser(prog=self.command, usage=usage, description=self.summary)
        arguments.add_storage_flag(parser, "Get or set", "configuration item")
        parser.add_argument('key',
                            help="option key",
                            metavar='<key>',
                            nargs='?',
                            default=arguments.SUPPRESS)
        parser.add_argument('value',
                            help="option value",
                            metavar='<value>',
                            nargs='?',
                            default=arguments.SUPPRESS)
        parser.add_argument('-u', '--unset',
                            help="unset configuration option",
                            action='store_const',
                            const=True,
                            default=arguments.SUPPRESS)
        parser.add_argument('--import',
                            help="import configuration file",
                            metavar='<path>',
                            dest='import_file',
                            default=arguments.SUPPRESS)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        storage = arguments.parse_storage_flag(args)[0]
        if storage is not PROJECT_STORAGE:
            storage.connect_filesystem()

        if hasattr(args, 'import_file'):
            try:
                configuration.import_from_file(args.import_file, storage=storage)
            except IOError:
                self.parser.error("Can't read configuration file '%s'" % args.import_file)
            return EXIT_SUCCESS
        
        if not hasattr(args, 'key'):
            for key, val in sorted(six.iteritems(configuration.get(storage=storage))):
                print('%s : %r' % (key, val))
        elif not (hasattr(args, 'value') or hasattr(args, 'unset')):
            try:
                print(configuration.get(args.key, storage))
            except KeyError:
                self.parser.error('Invalid key: %s' % args.key)
        elif hasattr(args, 'unset'):
            try:
                configuration.delete(args.key, storage)
            except KeyError:
                self.parser.error('Invalid key: %s' % args.key)
        elif hasattr(args, 'value'):
            configuration.put(args.key, args.value, storage)
        else:
            raise InternalError("Unhandled arguments in %s" % COMMAND)
        return EXIT_SUCCESS


COMMAND = ConfigureCommand(__name__, summary_fmt="Configure TAU Commander.")

