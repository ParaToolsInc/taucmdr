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


LOGGER = getLogger('commands')


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
%(value)r is not a TAU subcommand.

%(hint)s""" % {'value': self.value, 
               'hint': hint, 
               'contact': HELP_CONTACT}
        LOGGER.error(message)
        sys.exit(EXIT_FAILURE)


def getCommands():
  """
  Builds list of command names
  """
  names = []
  for _, module, _ in walk_packages(__path__, __name__+'.'):
    if module.count('.') == 1:
      __import__(module)
      name = module.split('.')[-1]
      names.append(name)
  return names

def getCommandsHelp():
  """
  Builds listing of command names with short description
  """
  parts = []
  for _, module, _ in walk_packages(__path__, __name__+'.'):
    if module.count('.') == 1:
      __import__(module)
      descr = sys.modules[module].SHORT_DESCRIPTION
      name = '{0:<12}'.format(module.split('.')[-1])
      parts.append('  %s  %s' % (name, descr))
  return '\n'.join(parts)


def getSubcommands(command, depth=1):
  """
  Builds list of subcommand names
  """
  LOGGER.debug('Getting subcommands of %r' % command)
  names = []
  command_module = sys.modules[command] 
  depth = len(command_module.__name__.split('.')) + depth
  for _, module, _ in walk_packages(command_module.__path__, command_module.__name__+'.'):
    if len(module.split('.')) <= depth:
      LOGGER.debug('importing %r' % module)
      __import__(module)
      names.append(module.split('.')[-1])
  return names

def getSubcommandsHelp(command, depth=1):
  """
  Builds listing of subcommand names with short description
  """
  LOGGER.debug('Getting subcommands of %r' % command)
  parts = []
  command_module = sys.modules[command] 
  depth = len(command_module.__name__.split('.')) + depth
  for _, module, _ in walk_packages(command_module.__path__, command_module.__name__+'.'):
    if len(module.split('.')) <= depth:
      LOGGER.debug('importing %r' % module)
      __import__(module)
      descr = sys.modules[module].SHORT_DESCRIPTION
      name = '{:<12}'.format(module.split('.')[-1])
      parts.append('  %s  %s' % (name, descr))
  return '\n'.join(parts)


def getCommandAttribute(cmd, attr_name):
  if len(cmd):
    cmd_module = 'tau.commands.%s' % '.'.join(cmd)
    __import__(cmd_module)
    try:
      attr = getattr(sys.modules[cmd_module], attr_name)
    except AttributeError:
      LOGGER.debug("%s.%s doesn't exist" % (cmd_module, attr_name))
      attr = None
    else:
      LOGGER.debug("Found %s.%s" % (cmd_module, attr_name))
    return attr
  else:
    return None


def executeCommand(cmd, cmd_args=[]):
    """
    Import the command module and run its main routine
    """
    try:
      main = getCommandAttribute(cmd, 'main')
      LOGGER.debug('Recognized %r as TAU command' % cmd)
    except ImportError:
      LOGGER.debug('%r not recognized as a TAU command' % cmd)
      parent = cmd[:-1]
      while len(parent):
        main = getCommandAttribute(parent, 'main')
        if main:
          LOGGER.debug('Getting help from %r' % parent)
          return main(['--help'])
        else:
          parent = parent[:-1]
      raise UnknownCommandError(' '.join(cmd))
    else:
      return main(cmd_args)
