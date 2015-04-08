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
import os
import argparse

# TAU modules
import logger
import util


SUPPRESS = argparse.SUPPRESS
REMAINDER = argparse.REMAINDER


class MutableGroupArgumentParser(argparse.ArgumentParser):
  """
  Argument parser that permits groups to be updated
  """
  def getGroup(self, title):
    for group in self._action_groups:
      if group.title == title:
        return group
    return None

class ArgparseHelpFormatter(argparse.RawDescriptionHelpFormatter):
  """
  Custom formatter for argparse
  """
  def __init__(self, prog, indent_increment=2, max_help_position=30, width=logger.LINE_WIDTH):
    super(ArgparseHelpFormatter,self).__init__(prog, indent_increment, max_help_position, width)

  def _split_lines(self, text, width):
    parts = []
    for line in text.splitlines():
      parts.extend(argparse.HelpFormatter._split_lines(self, line, width))
    return parts

  def _get_help_string(self, action):
    indent = ' '*self._indent_increment
    help = action.help
    choices = getattr(action, 'choices', None)
    if choices:
      help += '\n%s- %s: (%s)' % (indent, action.metavar, ', '.join(choices))
    if '%(default)' not in action.help:
      if action.default is not argparse.SUPPRESS:
        defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
        if action.option_strings or action.nargs in defaulting_nargs:
          help += '\n%s' % indent + '- default: %(default)s'
    return help
  

class ParsePackagePathAction(argparse.Action):
  """
  TODO: Docs
  """
  def __call__(self, parser, namespace, flag, option_string=None):
    flag_as_bool = util.parseBoolean(flag)
    if flag_as_bool == True:
      value = 'download'
    elif flag_as_bool == False:
      value = False
    elif (flag.lower() == 'download') or (os.path.exists(flag)) or util.isURL(flag):
      value = flag
    else:
      raise argparse.ArgumentError(self, "Boolean, 'download', path, or URL required, received: %s" % flag)
    setattr(namespace, self.dest, value)


class ParseBooleanAction(argparse.Action):
  """
  Parses an option value into a boolean
  """
  def __call__(self, parser, namespace, value, option_string=None):
    bool_value = util.parseBoolean(value)
    if bool_value == None:
      raise argparse.ArgumentError(self, 'Boolean value required')
    setattr(namespace, self.dest, bool_value)
    

def getParser(arguments, prog=None, usage=None, description=None, epilog=None):
  """
  Builds and argparse.ArgumentParser from the given arguments
  """
  parser = argparse.ArgumentParser(prog=prog, 
                                   usage=usage, 
                                   description=description,
                                   epilog=epilog,
                                   formatter_class=ArgparseHelpFormatter)
  for arg in arguments:
    flags, options = arg
    parser.add_argument(*flags, **options)
  return parser


def getParserFromModel(model, use_defaults=True,
                       prog=None, usage=None, description=None, epilog=None):
  """
  Builds an argparse.ArgumentParser from a model's attributes
  """
  parser = MutableGroupArgumentParser(prog=prog, 
                                      usage=usage, 
                                      description=description,
                                      epilog=epilog,
                                      formatter_class=ArgparseHelpFormatter)
  groups = {}
  for attr, props in model.attributes.iteritems():
    try:
      options = dict(props['argparse'])
    except KeyError:
      continue
    try:
      default = props['defaultsTo']
    except KeyError:
      options['default'] = argparse.SUPPRESS
    else:
      if use_defaults and default:
        options['default'] = default
      else:
        options['default'] = argparse.SUPPRESS 
    try:
      group_name = options['group'] + ' arguments'
    except KeyError:
      group = parser
    else:
      del options['group']
      groups.setdefault(group_name, parser.add_argument_group(group_name))
      group = groups[group_name]
    try:
      flags = options['flags']
    except KeyError:
      flags = (attr,)
    else:
      del options['flags']
      options['dest'] = attr
    group.add_argument(*flags, **options)
  return parser
