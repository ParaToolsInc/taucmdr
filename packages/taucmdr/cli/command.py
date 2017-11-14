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
"""Base class for TAU Commander commands"""

from abc import ABCMeta, abstractmethod

import six
from taucmdr import logger, cli
from taucmdr.cli.arguments import ArgumentsNamespace


class AbstractCommand(six.with_metaclass(ABCMeta, object)):
    """Abstract base class for TAU Commander commands.
    
    Attributes:
        module_name (str): Name of the command module this command object belongs to.
        command (str): Command line string that executes this command.
        summary (str): One-line summary of the command.
        help_page (str): Long and informative description of the command.
        group (str): If not None, commands will be grouped together by group name in help messages.
    """
    
    def __init__(self, module_name, format_fields=None, summary_fmt=None, help_page_fmt=None, group=None):
        if not summary_fmt:
            summary_fmt = "No summary for '%(command)s'"
        if not help_page_fmt:
            help_page_fmt = "No help page for '%(command)s'" 
        self.module_name = module_name
        self.logger = logger.get_logger(module_name)
        self.command = cli.command_from_module_name(module_name)
        self.format_fields = format_fields if format_fields else {}
        self.format_fields['command'] = self.command
        self.summary_fmt = summary_fmt
        self.help_page_fmt = help_page_fmt
        self.group = group
        self._parser = None
        
    def __str__(self):
        return self.command

    @property
    def summary(self):
        return self.summary_fmt % self.format_fields
    
    @property
    def help_page(self):
        return self.help_page_fmt % self.format_fields

    @property
    def parser(self):
        if self._parser is None:
            self._parser = self._construct_parser()
        return self._parser
        
    @property
    def usage(self):
        return self.parser.format_help()

    def _parse_args(self, argv):
        if isinstance(argv, ArgumentsNamespace):
            args = argv
        else:
            args = self.parser.parse_args(args=argv)
        self.logger.debug('%s args: %s', self.command, args)
        return args

    @abstractmethod
    def _construct_parser(self):
        """Construct a command line argument parser."""

    @abstractmethod
    def main(self, argv):
        """Command program entry point.
        
        Args:
            argv (list): Command line arguments.
            
        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """

