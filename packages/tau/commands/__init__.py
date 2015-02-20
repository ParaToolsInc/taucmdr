"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief 

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# System modules
import sys
from pkgutil import walk_packages

# TAU modules
from tau import HELP_CONTACT, EXIT_FAILURE
from logger import getLogger
from error import Error
from pprint import pprint

LOGGER = getLogger(__name__)

_commands = {__name__: {}}


class UnknownCommandError(Error):
  """
  Indicates that a specified command is unknown
  """
  def __init__(self, value, hint="Try 'tau --help'."):
    super(UnknownCommandError, self).__init__(value)
    self.hint = hint
        
  def handle(self):
    hint = 'Hint: %s' % self.hint if self.hint else ''
    message = """
%(value)r is not a valid TAU command.

%(hint)s""" % {'value': self.value, 
               'hint': hint, 
               'contact': HELP_CONTACT}
    LOGGER.error(message)
    sys.exit(EXIT_FAILURE)


class AmbiguousCommandError(Error):
  """
  Indicates that a specified partial command is ambiguous
  """
  def __init__(self, value, matches, hint="Try 'tau --help'."):
    super(AmbiguousCommandError, self).__init__(value)
    self.hint = hint
    self.matches = matches
      
  def handle(self):
    hint = 'Hint: %s' % self.hint if self.hint else ''
    message = """
Command %(value)r is ambiguous: %(matches)r

%(hint)s""" % {'value': self.value,
               'matches': self.matches, 
               'hint': hint, 
               'contact': HELP_CONTACT}
    LOGGER.error(message)
    sys.exit(EXIT_FAILURE)


def getCommands(root=__name__):
  """
  Returns commands at the specified level
  """
  def _lookup(c, d):
    if len(c) == 1: return d[c[0]]
    else: return _lookup(c[1:], d[c[0]])

  def _walking_import(module, c, d):
    car, cdr = c[0], c[1:]
    if cdr:
      _walking_import(module, cdr, d[car])
    elif not car in d:
        d[car] = {}
        __import__(module)
        d[car]['__module__'] = sys.modules[module]

  command_module = sys.modules[__name__]
  for _, module, _ in walk_packages(command_module.__path__, command_module.__name__+'.'):
    try:
      _lookup(module.split('.'), _commands)
    except KeyError:
      _walking_import(module, module.split('.'), _commands)

  return _lookup(root.split('.'), _commands)


def getCommandsHelp(root=__name__):
  """
  Builds listing of command names with short description
  """
  parts = []
  commands = getCommands(root)
  for cmd, subcmds in commands.iteritems():
    descr = subcmds['__module__'].SHORT_DESCRIPTION
    name = '{:<12}'.format(cmd)
    parts.append('  %s  %s' % (name, descr))
  return '\n'.join(parts)


def executeCommand(cmd, cmd_args=[]):
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

  while len(cmd):
    root = '.'.join([__name__] + cmd)
    try:
      main = getCommands(root)['__module__'].main
    except KeyError:
      LOGGER.debug('%r not recognized as a TAU command' % cmd)
      try:
        resolved = _resolve(cmd, _commands[__name__])
      except UnknownCommandError:
        if len(cmd) <= 1: 
          raise # We finally give up
        parent = cmd[:-1]
        LOGGER.debug('Getting help from parent command %r' % parent)
        return executeCommand(parent, ['--help'])
      else:
        LOGGER.debug('Resolved ambiguous command %r to %r' % (cmd, resolved))
        return executeCommand(resolved, cmd_args)
    except AttributeError:
      raise InternalError("'main(argv)' undefined in command %r" % cmd)
    else:
      return main(cmd_args)
