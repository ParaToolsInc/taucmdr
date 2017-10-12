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

Extensions to :any:`argparse` to support the TAU Commander command line interface.
"""

import os
import sys
import re
import argparse
import textwrap
from operator import attrgetter
from taucmdr import logger, util
from taucmdr.cli import USAGE_FORMAT
from taucmdr.error import InternalError
from taucmdr.cf.storage.levels import ORDERED_LEVELS, STORAGE_LEVELS


Action = argparse.Action
"""Action base class."""

ArgumentError = argparse.ArgumentError
"""Argument error exception base class."""

SUPPRESS = argparse.SUPPRESS
"""Suppress attribute creation in parsed argument namespace."""

REMAINDER = argparse.REMAINDER
"""All the remaining command-line arguments are gathered into a list."""

STORAGE_LEVEL_FLAG = "@"
"""Command line flag that indicates storage level."""

_DEFAULT_STORAGE_LEVEL = ORDERED_LEVELS[0].name



class MutableArgumentGroup(argparse._ArgumentGroup):
    """Argument group that allows its actions to be modified after creation."""
    # We're changing the behavior of the superclass so we need to access protected members
    # pylint: disable=protected-access
    
    def __init__(self, *args, **kwargs):
        super(MutableArgumentGroup, self).__init__(*args, **kwargs)
    
    def __getitem__(self, option_string):
        return self._option_string_actions[option_string]


class MutableArgumentGroupParser(argparse.ArgumentParser):
    """Argument parser with mutable groups and better help formatting.

    :py:class:`argparse.ArgumentParser` doesn't allow groups to change once set 
    and generates "scruffy" looking help, so we fix this problems in this subclass.
    """
    # We're changing the behavior of the superclass so we need to access protected members
    # pylint: disable=protected-access

    def __getitem__(self, option_string):
        return self._option_string_actions[option_string]

    def add_argument_group(self, *args, **kwargs):
        """Returns an argument group.
        
        If the group doesn't exist it will be created.
        
        Args:
            *args: Positional arguments to pass to :any:`ArgumentParser.add_argument_group`
            **kwargs: Keyword arguments to pass to :any:`ArgumentParser.add_argument_group`

        Returns:
            An argument group object.
        """
        title = kwargs.get('title', args[0])
        for group in self._action_groups:
            if group.title == title:
                return group
        group = MutableArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group
    
    def _format_help_markdown(self):
        """Format command line help string."""
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        for action_group in self._sorted_groups():
            title = ' '.join(x[0].upper() + x[1:] for x in action_group.title.split())
            formatter.start_section(title)
            formatter.add_arguments(sorted(action_group._group_actions, key=attrgetter('option_strings')))
            formatter.end_section()
        formatter.add_text(self.epilog)
        return formatter.format_help()
    
    def _format_help_console(self):
        """Format command line help string."""
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(self.description)
        for action_group in self._sorted_groups():
            title = ' '.join(x[0].upper() + x[1:] for x in action_group.title.split())
            formatter.start_section(title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(sorted(action_group._group_actions, key=attrgetter('option_strings')))
            formatter.end_section()
        formatter.add_text(self.epilog)
        return formatter.format_help()
    
    def format_help(self):
        try:
            func = getattr(self, '_format_help_'+USAGE_FORMAT.lower())
        except AttributeError:
            raise InternalError("Invalid USAGE_FORMAT: %s" % USAGE_FORMAT)
        return func()
    
    def _sorted_groups(self):
        """Iterate over action groups."""
        positional_title = 'positional arguments'
        optional_title = 'optional arguments'
        groups = sorted(self._action_groups, key=lambda x: x.title.lower())
        for group in groups:
            if group.title == positional_title:
                yield group
                break
        for group in groups:
            if group.title == optional_title:
                yield group
                break
        for group in groups:
            if group.title not in [positional_title, optional_title]:
                yield group
                
    def merge(self, parser, group_title=None, include_positional=False, include_optional=True, include_storage=False, 
              exclude_groups=None, exclude_arguments=None):
        """Merge arguments from a parser into this parser.
        
        Modify this parser by adding additional arguments taken from the supplied parser.
        
        Args:
            parser (ArgumentParser): Parser to pull arguments from.
            group_title (str): Optional group title for merged arguments.
            include_positional (bool): If True, include positional arguments.
            include_optional (bool): If True, include optional arguments.
            include_storage (bool): If True, include the storage level argument, see :any:`STORAGE_LEVEL_FLAG`.
            exclude_groups (list): Strings identifying argument groups that should be excluded.
            exclude_arguments (list): Strings identifying arguments that should be excluded.
        """
        for action in parser._actions:
            if exclude_groups and action.container.title in exclude_groups:
                continue
            dst_group = self.add_argument_group(group_title if group_title else action.container.title)
            optional = bool(action.option_strings)
            storage = '-'+STORAGE_LEVEL_FLAG in action.option_strings
            excluded = exclude_arguments and bool([optstr for optstr in action.option_strings  
                                                   for substr in exclude_arguments if substr in optstr])
            # pylint: disable=too-many-boolean-expressions
            if (excluded or
                    (not include_storage and storage) or
                    (not include_optional and optional) or
                    (not include_positional and not optional)):
                continue
            try:
                dst_group._add_action(action)
            except argparse.ArgumentError:
                # Argument is already in this parser.
                pass


class HelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom help string formatter for argument parser.
    
    Provide proper help message alignment, line width, and formatting.
    Uses console line width (:any:`logger.LINE_WIDTH`) to format help 
    messages appropriately so they don't wrap in strange ways.
    
    Args:
        prog (str): Name of the program.
        indent_increment (int): Number of spaces to indent wrapped lines.
        max_help_position (int): Column on which to begin subsequent lines of wrapped help strings.
        width (int): Maximum help message length before wrapping.
    """
    
    def __init__(self, prog, indent_increment=2, max_help_position=30, width=logger.LINE_WIDTH):
        super(HelpFormatter, self).__init__(prog, indent_increment, max_help_position, width)
        
    def _split_lines(self, text, width):
        parts = []
        for line in text.splitlines():
            parts.extend(textwrap.wrap(line, width))
        return parts

    def _get_help_string(self, action):
        indent = ' ' * self._indent_increment
        helpstr = action.help
        helpstr = helpstr[0].upper() + helpstr[1:] + "."
        choices = getattr(action, 'choices', None)
        if choices:
            helpstr += '\n%s- %s: %s' % (indent, action.metavar, ', '.join(choices))
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    if isinstance(action.default, list):
                        default_str = ', '.join(action.default)
                    else:
                        default_str = str(action.default)
                    helpstr += '\n%s' % indent + '- default: %s' % default_str
        return helpstr
    
    def _format_positional(self, argstr):
        return argstr
    
    def _format_optional(self, argstr):
        return argstr
    
    def _format_requred_arg(self, argstr):
        return argstr
    
    def _format_optional_arg(self, argstr):
        return argstr
    
    def _format_meta_arg(self, argstr):
        return argstr
    
    def _format_args(self, action, default_metavar):
        get_metavar = self._metavar_formatter(action, default_metavar)
        if action.nargs is None:
            result = self._format_requred_arg('%s' % get_metavar(1))
        elif action.nargs == argparse.OPTIONAL:
            result = self._format_optional_arg('[%s]' % get_metavar(1))
        elif action.nargs == argparse.ZERO_OR_MORE:
            result = self._format_optional_arg('[%s [%s ...]]' % get_metavar(2))
        elif action.nargs == argparse.ONE_OR_MORE:
            tpl = get_metavar(2)
            result = self._format_requred_arg('%s' % tpl[0]) + self._format_optional_arg(' [%s ...]' % tpl[1])  
        elif action.nargs == argparse.REMAINDER:
            result = self._format_requred_arg('...')
        elif action.nargs == argparse.PARSER:
            result = self._format_requred_arg('%s ...' % get_metavar(1))
        else:
            formats = ['%s' for _ in range(action.nargs)]
            result = ' '.join(formats) % get_metavar(action.nargs)
        return result

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return self._format_positional(metavar)
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(self._format_optional(x) for x in action.option_strings)
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s %s' % (self._format_optional(option_string), args_string))
            return ', '.join(parts)


class ConsoleHelpFormatter(HelpFormatter):
    """Custom help string formatter for console output."""
         
    def start_section(self, heading):
        return super(ConsoleHelpFormatter, self).start_section(util.color_text(heading, attrs=['bold']))

    def add_argument(self, action):
        if action.help is not SUPPRESS:
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            for subaction in self._iter_indented_subactions(action):
                invocations.append(get_invocation(subaction))
            invocation_length = max([len(util.uncolor_text(s)) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(self._action_max_length, action_length)
            self._add_item(self._format_action, [action])
     
    def _format_positional(self, argstr):
        return util.color_text(argstr, 'red')
    
    def _format_optional(self, argstr):
        return util.color_text(argstr, 'red')
    
    def _format_requred_arg(self, argstr):
        return util.color_text(argstr, 'blue')
    
    def _format_optional_arg(self, argstr):
        return util.color_text(argstr, 'cyan')
    
    def _format_action(self, action):
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_width = help_position - self._current_indent - 2
        action_header = self._format_action_invocation(action)
        action_header_nocolor = util.uncolor_text(action_header)
        if not action.help:
            # No help; start on same line and add a final newline
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
        elif len(action_header_nocolor) <= action_width:
            # Short action name; start on the same line and pad two spaces
            # Adjust length to account for color control chars
            length = action_width+len(action_header)-len(action_header_nocolor)
            tup = self._current_indent, '', length, action_header
            action_header = '%*s%-*s  ' % tup
            indent_first = 0
        else:
            # Long action name; start on the next line
            tup = self._current_indent, '', action_header
            action_header = '%*s%s\n' % tup
            indent_first = help_position
        parts = [action_header]
        if action.help:
            help_text = self._expand_help(action)
            help_lines = self._split_lines(help_text, help_width)
            parts.append('%*s%s\n' % (indent_first, '', help_lines[0]))
            for line in help_lines[1:]:
                parts.append('%*s%s\n' % (help_position, '', line))
        elif not action_header.endswith('\n'):
            parts.append('\n')
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))
        return self._join_parts(parts)


class MarkdownHelpFormatter(HelpFormatter):
    """Custom help string formatter for markdown output."""
    
    first_col_width = 30
    
    def __init__(self, prog, indent_increment=2, max_help_position=30, width=logger.LINE_WIDTH):
        super(MarkdownHelpFormatter, self).__init__(prog, indent_increment, max_help_position, width)
        trans = {'<': '*', 
                 '>': '*', 
                 '|': r'\|'}
        self._escape_rep = {re.escape(k): v for k, v in trans.iteritems()}
        self._escape_pattern = re.compile("|".join(self._escape_rep.keys()))

    
    class _Section(argparse.HelpFormatter._Section):
        """Override section help formatting."""
        # pylint: disable=protected-access
        def format_help(self):
            if self.parent is not None:
                self.formatter._indent()
            join = self.formatter._join_parts
            for func, args in self.items:
                func(*args)
            item_help = join([func(*args) for func, args in self.items])
            if self.parent is not None:
                self.formatter._dedent()
            if not self.items:
                return ''
            if self.heading is not SUPPRESS and self.heading is not None:
                title = '{:<{}}'.format(self.heading, MarkdownHelpFormatter.first_col_width)
                heading = ' \n%s | %s\n%s:| %s' % (title, 'Description',
                                                   '-'*len(title), '-'*len('Description'))
            else:
                heading = ''
            return join(['\n', heading, '\n', item_help, '\n'])
        
    def _escape_markdown(self, text):
        return self._escape_pattern.sub(lambda m: self._escape_rep[re.escape(m.group(0))], text)

    def _indent(self):
        self._current_indent = 0
        self._level = 0

    def _dedent(self):
        self._current_indent = 0
        self._level = 0

    def _split_lines(self, text, _):
        return text.splitlines()

    def _get_help_string(self, action):
        helpstr = action.help
        helpstr = helpstr[0].upper() + helpstr[1:] + "."
        choices = getattr(action, 'choices', None)
        if choices:
            helpstr += self._escape_markdown('\n  - %s: %s' % (action.metavar, ', '.join(choices)))
        return helpstr
    
    def _format_usage(self, usage, actions, groups, prefix):
        usage = super(MarkdownHelpFormatter, self)._format_usage(usage, actions, groups, "")
        return "`%s`" % usage.strip() + '\n\n'
    
    def _format_action_invocation(self, action):
        invocation = super(MarkdownHelpFormatter, self)._format_action_invocation(action)
        return '{}{:>{}}'.format(' '*self._indent_increment, self._escape_markdown(invocation),
                                 MarkdownHelpFormatter.first_col_width - self._indent_increment)
    
    def _format_action(self, action):
        # determine the required width and the entry label
        help_position = min(self._action_max_length + 2, self._max_help_position)
        help_width = max(self._width - help_position, 11)
        action_header = self._format_action_invocation(action)
        if not action.help:
            action_header = action_header + '\n'
        parts = [action_header]
        if action.help:
            help_text = self._expand_help(action)
            help_lines = self._split_lines(help_text, help_width)
            parts.append('%*s | %s\n' % (0, '', help_lines[0]))
            for line in help_lines[1:]:
                parts.append('%*s | %s\n' % (help_position, '', line))
        elif not action_header.endswith('\n'):
            # or add a newline if the description doesn't end with one
            parts.append('%*s | \n' % (help_position, ''))
        # if there are any sub-actions, add their help as well
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))
        return self._join_parts(parts)


class ParsePackagePathAction(argparse.Action):
    """Argument parser action for software package paths.
    
    This action checks that an argument's value is one of these cases:
    1) The path to an existing software package installation.
    2) The path to an archive file containing the software package.
    3) A URL to an archive file containing the software package.
    4) The magic word "download" or value that parses to True via :any:`taucmdr.util.parse_bool`.
    5) A value that parses to False via :any:`parse_bool`.
    """
    # pylint: disable=too-few-public-methods

    def __call__(self, parser, namespace, value, unused_option_string=None):
        """Sets the `self.dest` attribute in `namespace` to the parsed value of `value`.
        
        If `value` parses to a boolean True value then the attribute value is 'download'.
        If `value` parses to a boolean False value then the attribute value is ``None``.
        Otherwise the attribute value is the value of `value`.
            
        Args:
            parser (str): Argument parser object this group belongs to.
            namespace (object): Namespace to receive parsed value via setattr.
            value (str): Value parsed from the command line.
        """
        try:
            value_as_bool = util.parse_bool(value, additional_true=['download', 'nightly'])
        except TypeError:
            if not util.is_url(value):
                value = os.path.abspath(os.path.expanduser(value))
                if not (os.path.isdir(value) or util.path_accessible(value)):
                    raise argparse.ArgumentError(self, "Keyword, valid path, or URL required: %s" % value)
        else:
            value = value.lower() if value_as_bool else None
        setattr(namespace, self.dest, value)


class ParseBooleanAction(argparse.Action):
    """Argument parser action for boolean values.
    
    Essentially a wrapper around :any:`taucmdr.util.parse_bool`.
    """
    # pylint: disable=too-few-public-methods

    def __call__(self, parser, namespace, value, unused_option_string=None):
        """Sets the `self.dest` attribute in `namespace` to the parsed value of `value`.
        
        If `value` parses to a boolean via :any:`taucmdr.util.parse_bool` then the 
        attribute value is that boolean value.
            
        Args:
            parser (str): Argument parser object this group belongs to.
            namespace (object): Namespace to receive parsed value via setattr.
            value (str): Value parsed from the command line/
        """
        try:
            setattr(namespace, self.dest, util.parse_bool(value))
        except TypeError:
            raise argparse.ArgumentError(self, 'Boolean value required')


def get_parser(prog=None, usage=None, description=None, epilog=None):
    """Builds an argument parser.
    
    The returned argument parser accepts no arguments.
    Use :any:`argparse.ArgumentParser.add_argument` to add arguments.
    
    Args:
        prog (str): Name of the program.
        usage (str): Description of the program's usage.
        description (str): Text to display before the argument help.
        epilog (str): Text to display after the argument help.

    Returns:
        MutableArgumentGroupParser: The customized argument parser object.
    """
    try:
        formatter = getattr(sys.modules[__name__], USAGE_FORMAT.capitalize() + 'HelpFormatter')
    except AttributeError:
        raise InternalError("Invalid USAGE_FORMAT: %s" % USAGE_FORMAT)
    return MutableArgumentGroupParser(prog=prog,
                                      usage=usage,
                                      description=description,
                                      epilog=epilog,
                                      formatter_class=formatter)


def get_parser_from_model(model, use_defaults=True, prog=None, usage=None, description=None, epilog=None,
                          positional_primary_key=True):
    """Builds an argument parser from a model's attributes.
    
    The returned argument parser will accept arguments as defined by the model's `argparse` 
    attribute properties, where the arguments to :any:`argparse.ArgumentParser.add_argument` 
    are specified as keyword arguments.
    
    Examples:
        Given this model attribute:
        ::
        
            'openmp': {
                'type': 'boolean', 
                'description': 'application uses OpenMP',
                'default': False, 
                'argparse': {'flags': ('--openmp',),
                             'metavar': 'T/F',
                             'nargs': '?',
                             'const': True,
                             'action': ParseBooleanAction},
            }

        The returned parser will accept the ``--openmp`` flag accepting zero or one arguments 
        with 'T/F' as the metavar.  If ``--openmp`` is omitted the default value of False will
        be used.  If ``--openmp`` is provided with zero arguments, the const value of True will
        be used.  If ``--openmp`` is provided with one argument then the provided argument will
        be passed to a ParseBooleanAction instance to generate a boolean value.  The argument's
        help description will appear as "application uses OpenMP" if the ``--help`` argument is given.
    
    Args:
        model (Model): Model to construct arguments from.
        use_defaults (bool): If True, use the model attribute's default value 
                             as the argument's value if argument is not specified. 
        prog (str): Name of the program.
        usage (str): Description of the program's usage.
        description (str): Text to display before the argument help.
        epilog (str): Text to display after the argument help.
        positional_primary_key (bool): If True, automatically add a positional argument for the primary key.

    Returns:
        MutableArgumentGroupParser: The customized argument parser object.        
    """
    parser = get_parser(prog, usage, description, epilog)
    groups = {}
    for attr, props in model.attributes.iteritems():
        try:
            options = dict(props['argparse'])
        except KeyError:
            if 'primary_key' in props and positional_primary_key:
                options = {'metavar': '<%s_%s>' % (model.name.lower(), attr)}
            else:
                continue
        if use_defaults:
            options['default'] = props.get('default', argparse.SUPPRESS) 
        else:
            options['default'] = argparse.SUPPRESS
        try:
            options['help'] = props['description']
        except KeyError:
            pass
        try:
            group_name = options['group'] + ' arguments'
        except KeyError:
            group_name = model.name.lower() + ' arguments'
        else:
            del options['group']
        group = groups.setdefault(group_name, parser.add_argument_group(group_name))
        try:
            flags = options['flags']
        except KeyError:
            flags = (attr,)
        else:
            del options['flags']
            options['dest'] = attr
        prop_type = props.get('type', 'string')
        if prop_type == 'array':
            if 'nargs' not in options:
                options['nargs'] = '+'
        elif prop_type == 'boolean':
            if 'action' not in options:
                options['action'] = ParseBooleanAction
            if 'nargs' not in options:
                options['nargs'] = '?'
            if 'const' not in options:
                options['const'] = True
            if 'metavar' not in options:
                options['metavar'] = 'T/F'
        else:
            if 'type' not in options:
                options['type'] = {'integer': int,
                                   'float': float,
                                   'boolean': str,
                                   'string': str}[prop_type]
        group.add_argument(*flags, **options)
    return parser

def add_storage_flag(parser, action, object_name, plural=False, exclusive=True):
    """Add flag to indicate target storage container.
    
    Args:
        parser (MutableArgumentGroupParser): The parser to modify.
        action (str): The action that will be taken by the command, e.g. "delete" or "list"
        object_name (str): The type of object that will be manipulated, e.g. "application" or "measurement"
        plural (bool): Pluralize help message if True.
        exclusive (bool): Only one storage level may be specified if True.
    """
    help_parts = ["%s %ss" if plural else "%s the %s",
                  " at the specified storage ",
                  "level" if exclusive else "levels"]
    help_str = "".join(help_parts) % (action, object_name)
    nargs = 1 if exclusive else '+'
    choices = [container.name for container in ORDERED_LEVELS]
    parser.add_argument('-'+STORAGE_LEVEL_FLAG,
                        help=help_str,
                        metavar="<level>", 
                        nargs=nargs, 
                        choices=choices,
                        default=[_DEFAULT_STORAGE_LEVEL])

def parse_storage_flag(args):
    try:
        names = getattr(args, STORAGE_LEVEL_FLAG)
    except AttributeError:
        names = [_DEFAULT_STORAGE_LEVEL]
    return [STORAGE_LEVELS[name] for name in names]
