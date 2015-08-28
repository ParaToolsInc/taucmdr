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
"""TAU Commander command line interface (CLI).

The TAU Commander CLI is composed of a single top-level command that invokes
subcommands, much like `git`_.  For example, the command line 
``tau project create my_new_project`` invokes the `create` subcommand of the
`project` subcommand with the arguments `my_new_project`. 

Every package in :py:mod:`tau.cli.commands` is a TAU Commander subcommand. Modules
in the package are that subcommand's subcommands.  This can be nested as deep as
you like.  Subcommand modules must set the following module attributes:

    * COMMAND (str): The subcommand name as returned by :any:`get_command`.
    * SHORT_DESCRIPTION (str): A one-line description of the subcommand. 
    * HELP (str): The subcommand's help page.  Should be long and detailed.
    * parser: A function that returns an argument parser for the command.
    * main: The subprogram entry point.
    
Subcommand modules may optionally set the following module attributes:

    * GROUP (str): List this subcommand in a group named `GROUP` in help messages.

.. _git: https://git-scm.com/
"""

import os
import sys
from pkgutil import walk_packages
from tau import TAU_SCRIPT, TAU_HOME
from tau import logger
from tau.error import ConfigurationError, InternalError


LOGGER = logger.get_logger(__name__)

SCRIPT_COMMAND = os.path.basename(TAU_SCRIPT)

_COMMANDS = {SCRIPT_COMMAND: {}}

_COMMANDS_PACKAGE = __name__ + '.commands'


class UnknownCommandError(ConfigurationError):
    """Indicates that a specified command is unknown."""
    message_fmt = """
%(value)r is not a valid TAU command.

%(hint)s"""
    def __init__(self, value, hint="Try 'tau --help'."):
        super(UnknownCommandError, self).__init__(value, hint)


class AmbiguousCommandError(ConfigurationError):
    """Indicates that a specified partial command is ambiguous."""
    message_fmt = """
Command '%(value)s' is ambiguous: %(matches)s

%(hint)s"""
    def __init__(self, value, matches, hint="Try 'tau --help'."):
        super(AmbiguousCommandError, self).__init__(value, hint)
        self.message_fields['matches'] = ', '.join(matches)


def get_command(module_name):
    """Converts a module name to a command name string.
    
    Maps command module names to their command line equivilants, e.g.
    'tau.cli.commands.target.create' => 'tau target create'
    
    Args:
        module_name (str): Name of a module.
        
    Returns:
        str: A string that identifies the command.
    """
    return ' '.join(_command_as_list(module_name))


def _command_as_list(module_name):
    """Converts a module name to a command name list.
    
    Maps command module names to their command line equivilants, e.g.
    'tau.cli.commands.target.create' => ['tau', 'target', 'create']

    Args:
        module_name (str): Name of a module.

    Returns:
        :py:class:`list`: Strings that identify the command.
    """
    parts = module_name.split('.')
    for part in _COMMANDS_PACKAGE.split('.'):
        if parts[0] == part:
            parts = parts[1:]
    return [SCRIPT_COMMAND] + parts


def get_commands(root=_COMMANDS_PACKAGE):
    # pylint: disable=line-too-long
    """Returns a dictionary mapping commands to Python modules.
    
    Given a root module name, return a dictionary that maps commands and their
    subcommands to Python modules.  The special key ``__module__`` maps to the
    command module.  Other strings map to subcommands of the command.
    
    Args:
        root (str): A string naming the module to search for cli.
    
    Returns:
        dict: Strings mapping to dictionaries or modules.
        
    Example:
    ::
        get_commands('tau.cli.commands.target') ==>
            {'__module__': <module 'tau.cli.commands.target' from '/home/jlinford/workspace/taucmdr/packages/tau/cli/commands/target/__init__.pyc'>,
             'create': {'__module__': <module 'tau.cli.commands.target.create' from '/home/jlinford/workspace/taucmdr/packages/tau/cli/commands/target/create.pyc'>},
             'delete': {'__module__': <module 'tau.cli.commands.target.delete' from '/home/jlinford/workspace/taucmdr/packages/tau/cli/commands/target/delete.pyc'>},
             'edit': {'__module__': <module 'tau.cli.commands.target.edit' from '/home/jlinford/workspace/taucmdr/packages/tau/cli/commands/target/edit.pyc'>},
             'list': {'__module__': <module 'tau.cli.commands.target.list' from '/home/jlinford/workspace/taucmdr/packages/tau/cli/commands/target/list.pyc'>}}
    """
    def lookup(cmd, dct):
        if not cmd:
            return dct
        elif len(cmd) == 1:
            return dct[cmd[0]]
        else:
            return lookup(cmd[1:], dct[cmd[0]])

    def walking_import(module, cmd, dct):
        car, cdr = cmd[0], cmd[1:]
        if cdr:
            walking_import(module, cdr, dct[car])
        elif not car in dct:
            dct[car] = {}
            __import__(module)
            dct[car]['__module__'] = sys.modules[module]

    command_module = sys.modules[_COMMANDS_PACKAGE]
    for _, module, _ in walk_packages(command_module.__path__, 
                                      command_module.__name__ + '.'):
        try:
            lookup(_command_as_list(module), _COMMANDS)
        except KeyError:
            walking_import(module, _command_as_list(module), _COMMANDS)

    return lookup(_command_as_list(root), _COMMANDS)


def get_commands_description(root=_COMMANDS_PACKAGE):
    """Builds listing of command names with short description.
    
    Args:
        root (str): A dot-seperated string naming the module to search for cli.
    
    Returns:
        str: Help string describing all commands found at or below `root`.
    """
    groups = {}
    commands = sorted([i for i in get_commands(root).iteritems() if i[0] != '__module__'])
    for cmd, topcmd in commands:
        module = topcmd['__module__']
        descr = getattr(module, 'SHORT_DESCRIPTION', "FIXME: No description")
        group = getattr(module, 'GROUP', None)
        name = '{:<12}'.format(cmd)
        groups.setdefault(group, []).append('  %s  %s' % (name, descr))

    parts = []
    for group, members in groups.iteritems():
        if group:
            parts.append(group + ' subcommands:')
        else:
            parts.append('subcommands:')
        parts.extend(members)
        parts.append('')
    return '\n'.join(parts)


def execute_command(cmd, cmd_args=None, parent_module=None):
    """Import the command module and run its main routine.
    
    Args:
        cmd (:py:class:`list`): List of strings identifying the command, i.e. from :any:`_command_as_list`.
        cmd_args (:py:class:`list`): Command line arguments to be parsed by command.
        parent_module (str): Dot-seperated name of the command's parent.
        
    Raises:
        UnknownCommandError: `cmd` is invalid.
        AmbiguousCommandError: `cmd` is ambiguous.
        
    Returns:
        int: Command return code.
    """
    # pylint: disable=invalid-name
    def _resolve(c, d):
        if not c:
            return []
        car, cdr = c[0], c[1:]
        try:
            matches = [(car, d[car])]
        except KeyError:
            matches = [i for i in d.iteritems() if i[0].startswith(car)]
        if len(matches) == 1:
            return [matches[0][0]] + _resolve(cdr, matches[0][1])
        elif len(matches) == 0:
            raise UnknownCommandError(' '.join(cmd))
        elif len(matches) > 1:
            raise AmbiguousCommandError(' '.join(cmd), [m[0] for m in matches])

    if parent_module:
        parent = _command_as_list(parent_module)[1:]
        cmd = parent + cmd

    while len(cmd):
        root = '.'.join([_COMMANDS_PACKAGE] + cmd)
        try:
            main = get_commands(root)['__module__'].main
        except KeyError:
            LOGGER.debug('%r not recognized as a TAU command', cmd)
            try:
                resolved = _resolve(cmd, _COMMANDS[SCRIPT_COMMAND])
            except UnknownCommandError:
                if len(cmd) <= 1:
                    raise  # We finally give up
                if not parent_module:
                    parent = cmd[:-1]
                LOGGER.debug('Getting help from parent command %r', parent)
                return execute_command(parent, ['--help'])
            else:
                LOGGER.debug('Resolved ambiguous command %r to %r', cmd, resolved)
                return execute_command(resolved, cmd_args)
        except AttributeError:
            raise InternalError("'main(argv)' undefined in command %r", cmd)
        else:
            if not cmd_args:
                cmd_args = []
            return main(cmd_args)
