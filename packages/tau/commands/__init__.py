#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

import os
import sys
from pkgutil import walk_packages
from tau import logger, environment
from tau.error import ConfigurationError, InternalError


LOGGER = logger.getLogger(__name__)


_COMMAND_ROOT = os.path.basename(environment.TAU_SCRIPT)
_COMMANDS = {_COMMAND_ROOT: {}}


class UnknownCommandError(ConfigurationError):

    """
    Indicates that a specified command is unknown
    """

    message_fmt = """
%(value)r is not a valid TAU command.

%(hint)s"""

    def __init__(self, value, hint="Try 'tau --help'."):
        super(UnknownCommandError, self).__init__(value, hint)


class AmbiguousCommandError(ConfigurationError):

    """
    Indicates that a specified partial command is ambiguous
    """
    message_fmt = """
Command '%(value)s' is ambiguous: %(matches)s

%(hint)s"""

    def __init__(self, value, matches, hint="Try 'tau --help'."):
        super(AmbiguousCommandError, self).__init__(value, hint)
        self.message_fields['matches'] = ', '.join(matches)


def get_command_list(module_name):
    """Converts a module name to a command name list.
    
    Maps command module names to their command line equivilants, e.g.
    'tau.commands.target.create' => ['tau', 'target', 'create']
    
    Args:
        module_name: Name of a module.
        
    Returns:
        A list of strings that identifies the command.
    """
    parts = module_name.split('.')
    for part in __name__.split('.'):
        if parts[0] == part:
            parts = parts[1:]
    return [_COMMAND_ROOT] + parts


def get_command(module_name):
    """Converts a module name to a command name string.
    
    Maps command module names to their command line equivilants, e.g.
    'tau.commands.target.create' => 'tau target create'
    
    Args:
        module_name: Name of a module.
        
    Returns:
        A string that identifies the command.
    """
    return ' '.join(get_command_list(module_name))


def get_commands(root_module=__name__):
    """Returns a dictionary mapping commands to Python modules.
    
    Given a root module name, return a dictionary that maps commands and their
    subcommands to Python modules.  The special key '__module__' maps to the
    command module.  Other strings map to subcommands of the command.
    
    Args:
        root_module: A string naming the module to search for commands.
    
    Returns:
        A dictionary of strings mapping to dictionaries or modules.
        
    Example:
        get_commands('tau.commands.target') ==>
            {'__module__': <module 'tau.commands.target' from '/home/jlinford/workspace/taucmdr/packages/tau/commands/target/__init__.pyc'>,
             'create': {'__module__': <module 'tau.commands.target.create' from '/home/jlinford/workspace/taucmdr/packages/tau/commands/target/create.pyc'>},
             'delete': {'__module__': <module 'tau.commands.target.delete' from '/home/jlinford/workspace/taucmdr/packages/tau/commands/target/delete.pyc'>},
             'edit': {'__module__': <module 'tau.commands.target.edit' from '/home/jlinford/workspace/taucmdr/packages/tau/commands/target/edit.pyc'>},
             'list': {'__module__': <module 'tau.commands.target.list' from '/home/jlinford/workspace/taucmdr/packages/tau/commands/target/list.pyc'>}}
    """
    if environment.TAU_HOME == None:
        # Not executed from command line, don't worry about commands
        # e.g. this happens when building documentation with Sphinx
        return {}

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

    command_module = sys.modules[__name__]
    for _, module, _ in walk_packages(command_module.__path__, 
                                      command_module.__name__ + '.'):
        try:
            lookup(get_command_list(module), _COMMANDS)
        except KeyError:
            walking_import(module, get_command_list(module), _COMMANDS)

    return lookup(get_command_list(root_module), _COMMANDS)


def getCommandsHelp(root=__name__):
    """
    Builds listing of command names with short description
    """
    groups = {}
    commands = sorted(
        [i for i in get_commands(root).iteritems() if i[0] != '__module__'])
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


def executeCommand(cmd, cmd_args=[], parent_module=None):
    """
    Import the command module and run its main routine
    """
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
        parent = parent_module.split('.')[2:]
        cmd = parent + cmd

    while len(cmd):
        root = '.'.join([__name__] + cmd)
        try:
            main = get_commands(root)['__module__'].main
        except KeyError:
            LOGGER.debug('%r not recognized as a TAU command' % cmd)
            try:
                resolved = _resolve(cmd, _COMMANDS[_COMMAND_ROOT])
            except UnknownCommandError:
                if len(cmd) <= 1:
                    raise  # We finally give up
                if not parent_module:
                    parent = cmd[:-1]
                LOGGER.debug('Getting help from parent command %r' % parent)
                return executeCommand(parent, ['--help'])
            else:
                LOGGER.debug(
                    'Resolved ambiguous command %r to %r' % (cmd, resolved))
                return executeCommand(resolved, cmd_args)
        except AttributeError:
            raise InternalError("'main(argv)' undefined in command %r" % cmd)
        else:
            return main(cmd_args)
