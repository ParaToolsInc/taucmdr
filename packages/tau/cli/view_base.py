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
"""A command line data `view`.

See http://en.wikipedia.org/wiki/Model-view-controller
"""

import json
import pprint
from texttable import Texttable
from termcolor import termcolor
from tau import EXIT_SUCCESS
from tau import logger, util, cli
from tau.cli import arguments
from tau.cli.command import AbstractCommand
from tau.core import storage
from tau.core.mvc import UniqueAttributeError, InternalError


class CommandLineView(AbstractCommand):
    """A command that works as a `view` for a `controller`.
    
    See http://en.wikipedia.org/wiki/Model-view-controller
    
    Attributes:
        controller (class): The controller class for this view's data.
        model_name (str): The lower-case name of the model.
    """

    def __init__(self, controller, module_name, summary=None, help_page=None, group=None):
        if not summary:
            summary = "Create and manage %s configurations." % controller.model_name.lower()
        super(CommandLineView, self).__init__(module_name, summary, help_page, group)
        self.controller = controller
        self.model_name = controller.model_name.lower()


class RootCommand(CommandLineView):
    """A command with subcommands for actions."""
    
    def __init__(self, *args, **kwargs):
        super(RootCommand, self).__init__(*args, **kwargs)
    
    def construct_parser(self):
        usage = "%s <subcommand> [arguments]" % self.command
        epilog = ['', cli.get_commands_description(self.module_name), '',
                  "See '%s <subcommand> --help' for more information on <subcommand>." % self.command]
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage,
                                      description=self.summary,
                                      epilog='\n'.join(epilog))
        parser.add_argument('subcommand', 
                            help="See 'subcommands' below",
                            metavar='<subcommand>')
        parser.add_argument('options', 
                            help="Arguments to be passed to <subcommand>",
                            metavar='[arguments]',
                            nargs=arguments.REMAINDER)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        return cli.execute_command([args.subcommand], args.options, self.module_name)
    
    
class CreateCommand(CommandLineView):
    """Base class for the `create` subcommand of command line views."""
    
    def __init__(self, controller, module_name):
        model_name = controller.model_name.lower()
        summary = "Create %s configurations." % model_name
        super(CreateCommand, self).__init__(controller, module_name, summary=summary)
        
    def construct_parser(self):
        usage = "%s <%s_name> [arguments]" % (self.command, self.model_name)
        parser = arguments.get_parser_from_model(self.controller,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        arguments.add_storage_flags(parser, "create", self.model_name)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = storage.CONTAINERS[getattr(args, "@")[0]]
        ctrl = self.controller(store)
        data = {attr: getattr(args, attr) for attr in ctrl.attributes if hasattr(args, attr)}
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A %s named '%s' already exists" % (self.model_name, args.name))
        self.logger.info("Created a new %s-level %s named '%s'.", ctrl.storage.name, self.model_name, args.name)
        return EXIT_SUCCESS


class DeleteCommand(CommandLineView):
    """Base class for the `delete` subcommand of command line views."""
    
    def __init__(self, controller, module_name):
        model_name = controller.model_name.lower()
        summary = "Delete %s configurations." % model_name
        super(DeleteCommand, self).__init__(controller, module_name, summary=summary)
        
    def construct_parser(self):
        usage = "%s <%s_name> [arguments]" % (self.command, self.model_name)       
        epilog = "WARNING: This cannot be undone."
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage,
                                      description=self.summary,
                                      epilog=epilog)
        parser.add_argument('name', 
                            help="Name of %s configuration to delete" % self.model_name,
                            metavar='<%s_name>' % self.model_name)
        arguments.add_storage_flags(parser, "delete", self.model_name)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = storage.CONTAINERS[getattr(args, "@")[0]]
        ctrl = self.controller(store)
        name = args.name
        if not ctrl.exists({'name': name}):
            self.parser.error("No %(level)s-level %(model_name)s named '%(name)s'." %
                              {'level': ctrl.storage.name, 'name': name, 'model_name': self.model_name})
        ctrl.delete({'name': name})
        self.logger.info("Deleted %s '%s'", self.model_name, name)
        return EXIT_SUCCESS


class EditCommand(CommandLineView):
    """Base class for the `edit` subcommand of command line views."""
    
    def __init__(self, controller, module_name):
        model_name = controller.model_name.lower()
        summary = "Modify %s configurations." % model_name
        super(EditCommand, self).__init__(controller, module_name, summary=summary)
        
    def construct_parser(self):
        usage = "%s <%s_name> [arguments]" % (self.command, self.model_name)       
        parser = arguments.get_parser_from_model(self.controller,
                                                 use_defaults=False,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        parser.add_argument('--rename',
                            help="rename the %s configuration" % self.model_name,
                            metavar='<new_name>', dest='new_name',
                            default=arguments.SUPPRESS)
        arguments.add_storage_flags(parser, "modify", self.model_name)
        return parser

    def main(self, argv):
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        store = storage.CONTAINERS[getattr(args, "@")[0]]
        ctrl = self.controller(store)   
        name = args.name
        if not ctrl.exists({'name': name}):
            self.parser.error("No %(level)s-level %(model_name)s named '%(name)s'." %
                              {'level': ctrl.storage.name, 'name': name, 'model_name': self.model_name})
        data = {attr: getattr(args, attr) for attr in ctrl.attributes if hasattr(args, attr)}
        try:
            data['name'] = args.new_name
        except AttributeError:
            pass
        ctrl.update(data, {'name': name})
        self.logger.info("Updated %s '%s'", self.model_name, name)
        return EXIT_SUCCESS


class ListCommand(CommandLineView):
    """Base class for the `list` subcommand of command line views."""
    
    def __init__(self, controller, module_name, key_attr='name', default_style='dashboard', dashboard_columns=None):
        model_name = controller.model_name.lower()
        summary = "Show %s configuration data." % model_name
        super(ListCommand, self).__init__(controller, module_name, summary=summary)
        self._format_fields = {'command': self.command, 'model_name': self.model_name, 'key_attr': key_attr}
        self.key_attr = key_attr
        self.default_style = default_style
        if not dashboard_columns:
            dashboard_columns = [{'header': attr.capitalize(), 'value': attr} for attr in controller.attributes]
        self.dashboard_columns = dashboard_columns
        
    def short_format(self, records):
        """Format records in short format.
        
        Args:
            records: Controlled records to format.
        
        Returns:
            str: Record data in short format.
        """
        return '\n'.join([record[self.key_attr] for record in records])
    
    def dashboard_format(self, records):
        """Format records in dashboard format.
        
        Args:
            records: Controlled records to format.
        
        Returns:
            str: Record data in dashboard format.
        """
        title = util.hline("%s-level %ss (%s)" %
                           (records[0].storage.name.capitalize(),
                            records[0].model_name.capitalize(), 
                            records[0].storage.prefix), 
                           'cyan')
        header_row = [col['header'] for col in self.dashboard_columns]
        rows = [header_row]
        for record in records:
            populated = record.populate()
            row = []
            for col in self.dashboard_columns:
                if 'value' in col:
                    cell = populated[col['value']]
                elif 'yesno' in col:
                    cell = 'Yes' if populated.get(col['yesno'], False) else 'No'
                elif 'function' in col:
                    cell = col['function'](populated)
                else:
                    raise InternalError("Invalid column definition: %s" % col)
                color_attrs = col.get('color_attrs', None)
                if color_attrs:
                    cell = termcolor.colored(cell, **color_attrs)
                row.append(cell)
            rows.append(row)
        table = Texttable(logger.LINE_WIDTH)
        table.set_cols_align([col.get('align', 'c') for col in self.dashboard_columns])
        table.add_rows(rows)
        return '\n'.join([title, table.draw(), ''])

    def long_format(self, records):
        """Format records in long format.
        
        Args:
            records: Controlled records to format.
        
        Returns:
            str: Record data in long format.
        """
        # pylint: disable=no-self-use
        parts = []
        for record in records:
            populated = record.populate()
            parts.append(pprint.pformat(populated))
        return '\n'.join(parts)

    def json_format(self, records):
        """Format records in JSON format.
        
        Args:
            records: Controlled records to format.
        
        Returns:
            str: Record data in JSON format.
        """
        # pylint: disable=no-self-use
        return '\n'.join([json.dumps(record.data) for record in records])

    def construct_parser(self):
        key_str = self.model_name + '_' + self.key_attr
        usage_head = ("%(command)s [%(key_str)s] [%(key_str)s] ... [arguments]" % 
                      {'command': self.command, 'key_str': key_str})
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        parser.add_argument('keys', 
                            help=("Show only %(model_name)ss with the given %(key_attr)ss" % self._format_fields),
                            metavar='%(model_name)s' % self._format_fields,
                            nargs='*',
                            default=arguments.SUPPRESS)
        style_dest = 'style'
        style_group = parser.add_mutually_exclusive_group()
        style_group.add_argument('-s', '--short', 
                                 help="show minimal %(model_name)s data" % self._format_fields,
                                 const='short', action='store_const', dest=style_dest, 
                                 default=arguments.SUPPRESS)
        style_group.add_argument('-d', '--dashboard', 
                                 help="show %(model_name)s data in a fancy dasboard" % self._format_fields,
                                 const='dashboard', action='store_const', dest=style_dest, 
                                 default=arguments.SUPPRESS)
        style_group.add_argument('-l', '--long', 
                                 help="show all %(model_name)s data in a list" % self._format_fields,
                                 const='long', action='store_const', dest=style_dest, 
                                 default=arguments.SUPPRESS)
        style_group.add_argument('-j', '--json', 
                                 help="show all %(model_name)s data as JSON" % self._format_fields,
                                 const='json', action='store_const', dest=style_dest, 
                                 default=arguments.SUPPRESS)
        arguments.add_storage_flags(parser, "show", self._format_fields['model_name'], plural=True, exclusive=False)
        return parser
    
    def main(self, argv):
        """Command program entry point.
        
        Args:
            argv (list): Command line arguments.
            
        Returns:
            int: Process return code: non-zero if a problem occurred, 0 otherwise
        """
        args = self.parser.parse_args(args=argv)
        self.logger.debug('Arguments: %s', args)
        
        project_ctl = self.controller(storage.PROJECT_STORAGE)
        user_ctl = self.controller(storage.USER_STORAGE)
        system_ctl = self.controller(storage.SYSTEM_STORAGE)
        
        storage_levels = getattr(args, "@")
        system = storage.SYSTEM_STORAGE.name in storage_levels
        user = storage.USER_STORAGE.name in storage_levels
        project = storage.PROJECT_STORAGE.name in storage_levels or not (user or system)
        keys = getattr(args, 'keys', None)
        style = getattr(args, 'style', None) or self.default_style
        
        parts = []
        if system:
            parts.append(self._format_records(system_ctl, style, keys))
        if user:
            parts.append(self._format_records(user_ctl, style, keys))
        if project:
            try:
                parts.append(self._format_records(project_ctl, style, keys))
            except storage.ProjectStorageError as err:
                err.hints.insert(0, "See `tau init --help`.")
                err.hints.append("Check command line arguments.")
                self.logger.error(err)
        if style == 'dashboard':
            if not system:
                parts.append(self._count_records(system_ctl))
            if not user:
                parts.append(self._count_records(user_ctl))
            if not project:
                try:
                    parts.append(self._count_records(project_ctl))
                except storage.ProjectStorageError:
                    pass
        print '\n'.join(parts)
        return EXIT_SUCCESS
    
    def _retrieve_records(self, ctrl, keys):
        """Retrieve recorded data from the controller.
        
        Args:
            ctrl (Controller): Controller for the data model.
            keys (list): Keys to match to :any:`self.key_attr`.       
        """
        if not keys:
            records = ctrl.all()
        else:
            records = []
            for key in keys:
                record = ctrl.search({self.key_attr: key})
                if record:
                    records.extend(record)
                else:
                    self.parser.error("No %s with %s='%s'" % (self._format_fields['model_name'], self.key_attr, key))
        return records

    def _format_records(self, ctrl, style, keys=None):
        """Print formatted record data to stdout.
        
        Args:
            ctrl (Controller): Controller for the data model.
            style (str): Style in which to format records.        
            keys (list): Keys to match to :any:`self.key_attr`.       
        """
        records = self._retrieve_records(ctrl, keys)
        if not records:
            listing = "No %s-level %ss. See `%s --help`." % (ctrl.storage.name, self.model_name, self.command)
        else:
            formatter = getattr(self, style+'_format')
            listing = formatter(records)
        return listing

    def _count_records(self, ctrl):
        """Print a record count to stdout.
        
        Args:
            controller (Controller): Controller for the data model.
        """
        level = ctrl.storage.name
        count = ctrl.count()
        fields = {'count': count, 'level': level, 'command': self.command, 'level_flag': arguments.STORAGE_LEVEL_FLAG}
        if count == 1:
            return ("There is 1 %(level)s-level application."
                    " Type `%(command)s %(level_flag)s %(level)s` to list it." % fields) 
        elif count > 1:
            return ("There are %(count)d %(level)s-level applications."
                    " Type `%(command)s %(level_flag)s %(level)s` to list them." % fields) 
        else:
            return ""
