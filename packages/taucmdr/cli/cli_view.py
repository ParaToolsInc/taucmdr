# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-17 ParaTools, Inc.
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

from __future__ import print_function

import json

import six
from texttable import Texttable
from taucmdr import EXIT_SUCCESS, ENTERPRISE_URL
from taucmdr import logger, util, cli
from taucmdr.error import UniqueAttributeError, InternalError, ModelError, ProjectSelectionError, ConfigurationError
from taucmdr.cf.storage import StorageError
from taucmdr.cf.storage.levels import SYSTEM_STORAGE, USER_STORAGE, PROJECT_STORAGE, ENTERPRISE_STORAGE
from taucmdr.model.project import Project
from taucmdr.cli import arguments
from taucmdr.cli.command import AbstractCommand


class AbstractCliView(AbstractCommand):
    """A command that works as a `view` for a `controller`.
    
    See http://en.wikipedia.org/wiki/Model-view-controller
    
    Attributes:
        controller (class): The controller class for this view's data.
        model_name (str): The lower-case name of the model.
    """

    # pylint: disable=abstract-method

    def __init__(self, model, module_name,
                 summary_fmt=None, help_page_fmt=None, group=None, include_storage_flag=True):
        self.model = model
        self.model_name = self.model.name.lower()
        format_fields = {'model_name': self.model_name}
        if not summary_fmt:
            summary_fmt = "Create and manage %(model_name)s configurations."
        self.include_storage_flag = include_storage_flag
        super(AbstractCliView, self).__init__(module_name, format_fields=format_fields, summary_fmt=summary_fmt,
                                              help_page_fmt=help_page_fmt, group=group)


class RootCommand(AbstractCliView):
    """A command with subcommands for actions."""

    def _construct_parser(self):
        usage = "%s <subcommand> [arguments]" % self.command
        epilog = ['', cli.commands_description(self.module_name), '',
                  "See `%s <subcommand> --help` for more information on a subcommand." % self.command]
        parser = arguments.get_parser(prog=self.command, usage=usage, 
                                      description=self.summary, epilog='\n'.join(epilog))
        parser.add_argument('subcommand',
                            help="See 'subcommands' below",
                            metavar='<subcommand>')
        parser.add_argument('options',
                            help="Arguments to be passed to <subcommand>",
                            metavar='[arguments]',
                            nargs=arguments.REMAINDER)
        return parser

    def main(self, argv):
        args = self._parse_args(argv)
        return cli.execute_command([args.subcommand], args.options, self.module_name)


class CreateCommand(AbstractCliView):
    """Base class for the `create` command of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', "Create %(model_name)s configurations.")
        super(CreateCommand, self).__init__(*args, **kwargs)

    def _construct_parser(self):
        usage = "%s <%s_%s> [arguments]" % (self.command, self.model_name, self.model.key_attribute)
        parser = arguments.get_parser_from_model(self.model,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "create", self.model_name)
        return parser

    def _create_record(self, store, data):
        """Create the model record.
        
        Args:
            store (AbstractStorage): Storage to contain the record.
            data (dict): Record data.
            
        Returns:
            int: :any:`EXIT_SUCCESS` if successful.
        
        Raises:
            UniqueAttributeError: A record with the same unique attribute already exists.
        """
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        key = data[key_attr]
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A %s with %s='%s' already exists" % (self.model_name, key_attr, key))
        if ctrl.storage is PROJECT_STORAGE:
            from taucmdr.cli.commands.project.edit import COMMAND as project_edit_cmd
            try:
                proj = Project.selected()
            except ProjectSelectionError:
                self.logger.info("Created a new %s '%s'. Use `%s` to add the new %s to a project.",
                                 self.model_name, key, project_edit_cmd, self.model_name)
            else:
                project_edit_cmd.main([proj['name'], '--add', key])
        else:
            self.logger.info("Created a new %s-level %s: '%s'.", ctrl.storage.name, self.model_name, key)
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        return self._create_record(store, data)


class DeleteCommand(AbstractCliView):
    """Base class for the `delete` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', "Delete %(model_name)s configurations.")
        super(DeleteCommand, self).__init__(*args, **kwargs)

    def _construct_parser(self):
        key_attr = self.model.key_attribute
        usage = "%s <%s_%s> [arguments]" % (self.command, self.model_name, key_attr)
        epilog = util.color_text("WARNING: THIS OPERATION IS NOT REVERSABLE!", 'yellow', attrs=['bold'])
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage,
                                      description=self.summary,
                                      epilog=epilog)
        parser.add_argument(key_attr,
                            help="%s of %s configuration to delete" % (key_attr.capitalize(), self.model_name),
                            metavar='<%s_%s>' % (self.model_name, key_attr))
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "delete", self.model_name)
        return parser

    def _delete_record(self, store, key):
        key_attr = self.model.key_attribute
        ctrl = self.model.controller(store)
        records = ctrl.search({key_attr: key})
        if not records:
            records = ctrl.search_hash(key)
            if not records:
                self.parser.error("No %s-level %s with %s='%s'." % (store.name, self.model_name, key_attr, key))
            if len(records) > 1:
                matches = [record.hash_digest() for record in records]
                self.parser.error("Ambiguous hash %s for %s at %s-level: matches %s" %
                                  (key, self.model_name, store.name, matches))
        eids_to_delete = [record.eid for record in records]
        ctrl.delete(eids_to_delete)
        self.logger.info("Deleted %s '%s'", self.model_name, key)
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        key = getattr(args, self.model.key_attribute)
        return self._delete_record(store, key)


class EditCommand(AbstractCliView):
    """Base class for the `edit` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', "Modify %(model_name)s configurations.")
        self.include_new_key_flag = kwargs.pop('include_new_key_flag', True)
        super(EditCommand, self).__init__(*args, **kwargs)

    def _construct_parser(self):
        key_attr = self.model.key_attribute
        usage = "%s <%s_%s> [arguments]" % (self.command, self.model_name, key_attr)
        parser = arguments.get_parser_from_model(self.model,
                                                 use_defaults=False,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        if self.include_new_key_flag:
            group = parser.add_argument_group('%s arguments' % self.model_name)
            group.add_argument('--new-%s' % key_attr,
                               help="change the configuration's %s" % key_attr,
                               metavar='<new_%s>' % key_attr,
                               dest='new_key',
                               default=arguments.SUPPRESS)
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "modify", self.model_name)
        return parser

    def _update_record(self, store, data, key):
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        used_hash = False
        records = ctrl.search({key_attr: key})
        if not records:
            records = ctrl.search_hash(key)
            used_hash = True
            if not records:
                self.parser.error("No %s-level %s with %s='%s'." % (ctrl.storage.name, self.model_name, key_attr, key))
            if len(records) > 1:
                matches = [record.hash_digest() for record in records]
                self.parser.error("Ambiguous hash %s for %s at %s-level: matches %s" %
                                  (key, self.model_name, store.name, matches))
        eids_to_update = [record.eid for record in records]
        if used_hash and data[key_attr] == key:
            del data[key_attr]
        print(data)
        ctrl.update(data, eids_to_update)
        self.logger.info("Updated %s '%s'", self.model_name, key)
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        key_attr = self.model.key_attribute
        try:
            data[key_attr] = args.new_key
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        return self._update_record(store, data, key)


class ListCommand(AbstractCliView):
    """Base class for the `list` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', "Show %(model_name)s configuration data.")
        default_style = kwargs.pop('default_style', 'dashboard')
        dashboard_columns = kwargs.pop('dashboard_columns', None)
        title_fmt = kwargs.pop('title_fmt', "%(model_name)s Configurations (%(storage_path)s)")
        self.storage_enterprise_only = kwargs.pop('enterprise_only', False)
        super(ListCommand, self).__init__(*args, **kwargs)
        key_attr = self.model.key_attribute
        self._format_fields = {'command': self.command, 'model_name': self.model_name, 'key_attr': key_attr}
        self.default_style = default_style
        self.dashboard_columns = dashboard_columns or [{'header': key_attr.title(), 'value': key_attr}]
        self.title_fmt = title_fmt

    def short_format(self, models):
        """Format modeled records in short format.

        Args:
            models: Modeled records to format.

        Returns:
            str: Record data in short format.
        """
        return [str(model[self.model.key_attribute]) for model in models]

    def dashboard_format(self, records):
        """Format modeled records in dashboard format.

        Args:
            records: Modeled records to format.
 
        Returns:
            str: Record data in dashboard format.
        """
        title = util.hline(self.title_fmt % {'model_name': records[0].name.capitalize(),
                                             'storage_path': records[0].storage}, 'cyan')
        header_row = [col['header'] for col in self.dashboard_columns]
        rows = [header_row]
        for record in records:
            populated = record.populate()
            row = []
            for col in self.dashboard_columns:
                if 'value' in col:
                    try:
                        cell = populated[col['value']]
                    except KeyError:
                        cell = 'N/A'
                elif 'yesno' in col:
                    cell = 'Yes' if populated.get(col['yesno'], False) else 'No'
                elif 'function' in col:
                    cell = col['function'](populated)
                elif 'hash' in col:
                    cell = record.hash_digest()[-col['hash']:]
                else:
                    raise InternalError("Invalid column definition: %s" % col)
                row.append(cell)
            rows.append(row)
        table = Texttable(logger.LINE_WIDTH)
        table.set_cols_align([col.get('align', 'c') for col in self.dashboard_columns])
        table.set_cols_dtype([col.get('dtype', 'a') for col in self.dashboard_columns])
        table.add_rows(rows)
        return [title, table.draw(), '']

    def json_format(self, records):
        rows = []
        for record in records:
            populated = record.populate()
            row = {}
            for col in self.dashboard_columns:
                if 'value' in col:
                    try:
                        cell = populated[col['value']]
                    except KeyError:
                        cell = None
                elif 'yesno' in col:
                    cell = 'Yes' if populated.get(col['yesno'], False) else 'No'
                elif 'function' in col:
                    cell = col['function'](populated)
                elif 'hash' in col:
                    cell = record.hash_digest()[-col['hash']:]
                else:
                    raise InternalError("Invalid column definition: %s" % col)
                row[col['header']] = cell
            rows.append(row)
        headers = [col['header'] for col in self.dashboard_columns]
        result = {'model': self.model_name, 'headers': headers, 'rows': rows}
        return [json.dumps(result)]

    def _format_long_item(self, key, val):
        attrs = self.model.attributes[key]
        if 'collection' in attrs:
            foreign_model = attrs['collection']
            foreign_keys = []
            for foreign_record in val:
                try:
                    foreign_keys.append(str(foreign_record[foreign_model.key_attribute]))
                except (AttributeError, ModelError):
                    foreign_keys.append(str(foreign_record))
            val = ', '.join(foreign_keys)
        elif 'model' in attrs:
            foreign_model = attrs['model']
            try:
                if val is None:
                    val = str(val)
                else:
                    val = str(val[foreign_model.key_attribute])
            except (AttributeError, ModelError):
                val = str(val)
        elif 'type' in attrs:
            if attrs['type'] == 'boolean':
                val = str(bool(val))
            elif attrs['type'] == 'array':
                val = ', '.join(str(x) for x in val)
            elif attrs['type'] != 'string':
                val = str(val)
        else:
            raise InternalError("Attribute has no type: %s, %s" % (attrs, val))
        description = attrs.get('description', 'No description')
        description = description[0].upper() + description[1:] + "."
        flags = ', '.join(flag for flag in attrs.get('argparse', {'flags': ('N/A',)})['flags'])
        return [key, val, flags, description]

    def long_format(self, records):
        """Format records in long format.
        
        Args:
            records: Controlled records to format.
        
        Returns:
            str: Record data in long format.
        """
        title = util.hline(self.title_fmt % {'model_name': records[0].name.capitalize(),
                                             'storage_path': records[0].storage}, 'cyan')
        retval = [title]
        for record in records:
            rows = [['Attribute', 'Value', 'Command Flag', 'Description']]
            populated = record.populate()
            for key, val in sorted(six.iteritems(populated)):
                if key != self.model.key_attribute:
                    rows.append(self._format_long_item(key, val))
            table = Texttable(logger.LINE_WIDTH)
            table.set_cols_align(['r', 'c', 'l', 'l'])
            table.set_deco(Texttable.HEADER | Texttable.VLINES)
            table.add_rows(rows)
            retval.append(util.hline("%s %s" % (populated[self.model.key_attribute], record.hash_digest()), 'cyan'))
            retval.extend([table.draw(), ''])
        return retval

    def _construct_parser(self):
        key_str = self.model_name + '_' + self.model.key_attribute
        usage_head = ("%(command)s [%(key_str)s] [%(key_str)s] ... [arguments]" %
                      {'command': self.command, 'key_str': key_str})
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        parser.add_argument('keys',
                            help=("Show only %(model_name)ss with the given %(key_attr)ss" % self._format_fields),
                            metavar=key_str,
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
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "show", self.model_name, plural=True, exclusive=False,
                                       enterprise_only=self.storage_enterprise_only)
        return parser

    def _list_records(self, storage_levels, keys, style):
        """Shows record data via `print`.
        
        Args:
            storage_levels (list): Storage levels to query, e.g. ['user', 'project']
            keys (list): Keys to match to :any:`self.key_attr`.
            style (str): Style in which to format records.
            
        Returns:
            int: :any:`EXIT_SUCCESS` if successful.
        """

        project_ctl = self.model.controller(PROJECT_STORAGE)
        user_ctl = self.model.controller(USER_STORAGE)
        system_ctl = self.model.controller(SYSTEM_STORAGE)

        system = SYSTEM_STORAGE.name in storage_levels
        user = USER_STORAGE.name in storage_levels
        enterprise = ENTERPRISE_STORAGE.name in storage_levels
        project = PROJECT_STORAGE.name in storage_levels or not (user or system or enterprise)

        parts = []
        if system:
            parts.extend(self._format_records(system_ctl, style, keys))
        if user:
            parts.extend(self._format_records(user_ctl, style, keys))
        if project:
            parts.extend(self._format_records(project_ctl, style, keys))
        if enterprise:
            token, db_name = Project.connected()
            ENTERPRISE_STORAGE.connect_database(url=ENTERPRISE_URL, db_name=db_name, token=token)
            enterprise_ctl = self.model.controller(ENTERPRISE_STORAGE)
            parts.extend(self._format_records(enterprise_ctl, style, keys))
        if style == 'dashboard':
            # Show record counts (not the records themselves) for other storage levels
            if not system:
                parts.extend(self._count_records(system_ctl))
            if not user:
                parts.extend(self._count_records(user_ctl))
            if not project:
                parts.extend(self._count_records(project_ctl))
        print('\n'.join(parts))
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        keys = getattr(args, 'keys', None)
        style = getattr(args, 'style', None) or self.default_style
        storage_levels = [level.name for level in arguments.parse_storage_flag(args)]
        return self._list_records(storage_levels, keys, style)

    def _retrieve_records(self, ctrl, keys):
        """Retrieve modeled data from the controller.
        
        Args:
            ctrl (Controller): Controller for the data model.
            keys (list): Keys to match to :any:`self.key_attr`.
            
        Returns:
            list: Model records.
        """
        if not keys:
            records = ctrl.all()
        else:
            key_attr = self.model.key_attribute
            if len(keys) == 1:
                records = ctrl.search({key_attr: keys[0]})
                if not records:
                    records = ctrl.search_hash(keys[0])
                    if not records:
                        self.parser.error("No %s with %s='%s'" % (self.model_name, key_attr, keys[0]))
            else:
                records = ctrl.search([{key_attr: key} for key in keys])
                if not records:
                    records = ctrl.search_hash(keys)
                for i, record in enumerate(records):
                    if not record:
                        self.parser.error("No %s with %s='%s'" % (self.model_name, key_attr, keys[i]))
        return records

    def _format_records(self, ctrl, style, keys=None):
        """Format records in a given style.
        
        Retrieves records for controller `ctrl` and formats them.
        
        Args:
            ctrl (Controller): Controller for the data model.
            style (str): Style in which to format records.        
            keys (list): Keys to match to :any:`self.key_attr`.
            
        Returns:
            list: Record data as formatted strings.
        """
        try:
            records = self._retrieve_records(ctrl, keys)
        except StorageError:
            records = []
        if not records:
            if style == 'json':
                parts = ['[]']
            else:
                parts = ["No %ss." % self.model_name]
        else:
            formatter = getattr(self, style + '_format')
            parts = formatter(records)
        return parts

    def _count_records(self, ctrl):
        """Print a record count to stdout.
        
        Args:
            controller (Controller): Controller for the data model.
        """
        level = ctrl.storage.name
        try:
            count = ctrl.count()
        except StorageError:
            count = 0
        fields = dict(self._format_fields, count=count, level=level, level_flag=arguments.STORAGE_LEVEL_FLAG)
        if count == 1:
            return ["There is 1 %(level)s %(model_name)s."
                    " Type `%(command)s -%(level_flag)s %(level)s` to list it." % fields]
        elif count > 1:
            return ["There are %(count)d %(level)s %(model_name)ss."
                    " Type `%(command)s -%(level_flag)s %(level)s` to list them." % fields]
        else:
            # return ["There are no %(level)s %(model_name)ss." % fields]
            return []


class CopyCommand(CreateCommand):
    """Base class for the `copy` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', "Copy and modify %(model_name)s configurations.")
        super(CopyCommand, self).__init__(*args, **kwargs)

    def _construct_parser(self):
        key_attr = self.model.key_attribute
        usage = ("%s <%s_%s> <copy_%s> [arguments]" % (self.command, self.model_name, key_attr, key_attr))
        parser = arguments.get_parser_from_model(self.model,
                                                 use_defaults=False,
                                                 prog=self.command,
                                                 usage=usage,
                                                 description=self.summary)
        group = parser.add_argument_group('%s arguments' % self.model_name)
        group.add_argument('copy_%s' % key_attr,
                           help="new %s configuration's %s" % (self.model_name, key_attr),
                           metavar='<copy_%s>' % key_attr,
                           default=arguments.SUPPRESS)
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "copy", self.model_name)
        return parser

    def _copy_record(self, store, updates, key):
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        matching = ctrl.search({key_attr: key})
        if not matching:
            matching = ctrl.search_hash(key)
            if not matching:
                self.parser.error("No %s-level %s with %s='%s'." % (ctrl.storage.name, self.model_name, key_attr, key))
        if len(matching) > 1:
            raise InternalError("More than one %s-level %s with %s='%s' exists!" %
                                (ctrl.storage.name, self.model_name, key_attr, key))
        else:
            found = matching[0]
        data = dict(found)
        data.update(updates)
        return self._create_record(store, data)

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        key_attr = self.model.key_attribute
        try:
            data[key_attr] = getattr(args, 'copy_%s' % key_attr)
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        return self._copy_record(store, data, key)


class PushCommand(AbstractCliView):
    """Base class for the `push` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', 'Push %(model_name)s configurations to TAU Enterprise.')
        super(PushCommand, self).__init__(*args, **kwargs)
        key_attr = self.model.key_attribute
        self._format_fields = {'command': self.command, 'model_name': self.model_name, 'key_attr': key_attr}

    def _construct_parser(self):
        key_str = self.model_name + '_' + self.model.key_attribute
        usage_head = ("%(command)s [%(key_str)s] [%(key_str)s] ... [arguments]" %
                      {'command': self.command, 'key_str': key_str})
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        parser.add_argument('keys',
                            help=("Push %(model_name)ss with the given %(key_attr)ss" % self._format_fields),
                            metavar=key_str,
                            nargs='+',
                            default=arguments.SUPPRESS)
        mode_dest = 'mode'
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument('-n', '--dry-run',
                                help="show the data that would be pushed, but don't actually push",
                                const='dryrun', action='store_const', dest=mode_dest,
                                default=arguments.SUPPRESS)
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "push", self.model_name, plural=True, exclusive=False)
        return parser

    def _find_records(self, ctrl, keys):
        key_attr = self.model.key_attribute
        if len(keys) == 1:
            records = ctrl.search({key_attr: keys[0]})
            if not records:
                try:
                    int_keys = [int(key) for key in keys]
                    records = ctrl.search({key_attr: int_keys[0]})
                    if not records:
                        records = ctrl.search_hash(keys[0])
                except ValueError:
                    records = ctrl.search_hash(keys[0])
        else:
            records = ctrl.search([{key_attr: key} for key in keys])
            if not records:
                try:
                    int_keys = [int(key) for key in keys]
                    records = ctrl.search([{key_attr: int_key} for int_key in int_keys])
                    if not records:
                        records = ctrl.search_hash(keys)
                except ValueError:
                    records = ctrl.search_hash(keys)
        return records

    def _push_records(self, storage_levels, keys, mode):
        project_ctl = self.model.controller(PROJECT_STORAGE)
        user_ctl = self.model.controller(USER_STORAGE)
        system_ctl = self.model.controller(SYSTEM_STORAGE)

        system = SYSTEM_STORAGE.name in storage_levels
        user = USER_STORAGE.name in storage_levels
        project = PROJECT_STORAGE.name in storage_levels or not (user or system)

        base_records = []
        if system:
            base_records.extend(self._find_records(system_ctl, keys))
        if user:
            base_records.extend(self._find_records(user_ctl, keys))
        if project:
            base_records.extend(self._find_records(project_ctl, keys))

        if not base_records:
            self.parser.error("No %s matching %s found." % (self.model.name, keys))

        records_to_push = project_ctl.traverse_records(base_records)

        if mode == 'dryrun':
            for record in records_to_push:
                self.logger.info("Would push %s %s", record.name, record.hash_digest())
            return EXIT_SUCCESS

        token, db_name = Project.connected()
        ENTERPRISE_STORAGE.connect_database(url=ENTERPRISE_URL, db_name=db_name, token=token)

        eid_map = {}
        with ENTERPRISE_STORAGE as database:
            for record in records_to_push:
                remote_eid, already_present = record.controller(record.storage).transport_record(record, database,
                                                                                                 eid_map, 'push')
                eid_map[record.hash_digest()] = remote_eid
                if already_present:
                    self.logger.info("Skipped %s %s, already uploaded.", record.name, record.hash_digest())
                else:
                    self.logger.info("Pushed %s %s to server.", record.name, record.hash_digest())

        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        keys = getattr(args, 'keys', None)
        mode = getattr(args, 'mode', None) or 'none'
        storage_levels = arguments.parse_storage_flag(args)
        return self._push_records(storage_levels, keys, mode)


class PullCommand(AbstractCliView):
    """Base class for the `pull` subcommand of command line views."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('summary_fmt', 'Pull %(model_name)s configurations from TAU Enterprise.')
        super(PullCommand, self).__init__(*args, **kwargs)
        key_attr = self.model.key_attribute
        self._format_fields = {'command': self.command, 'model_name': self.model_name, 'key_attr': key_attr}

    def _construct_parser(self):
        key_str = self.model_name + '_' + self.model.key_attribute
        usage_head = ("%(command)s [%(key_str)s] [%(key_str)s] ... [arguments]" %
                      {'command': self.command, 'key_str': key_str})
        parser = arguments.get_parser(prog=self.command,
                                      usage=usage_head,
                                      description=self.summary)
        parser.add_argument('keys',
                            help=("Pull %(model_name)ss with the given %(key_attr)ss" % self._format_fields),
                            metavar=key_str,
                            nargs='+',
                            default=arguments.SUPPRESS)
        mode_dest = 'mode'
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument('-n', '--dry-run',
                                help="Show the data that would be pushed, but don't actually push",
                                const='dryrun', action='store_const', dest=mode_dest,
                                default=arguments.SUPPRESS)
        mode_group.add_argument('-p', '--project',
                                help="Pull objects into the current project",
                                const='project', action='store_const', dest=mode_dest,
                                default=arguments.SUPPRESS)
        if self.include_storage_flag:
            arguments.add_storage_flag(parser, "pull", self.model_name, plural=True, exclusive=True)
        return parser

    def _find_records(self, ctrl, keys):
        key_attr = self.model.key_attribute
        if len(keys) == 1:
            records = ctrl.search({key_attr: keys[0]})
            if not records:
                try:
                    int_keys = [int(key) for key in keys]
                    records = ctrl.search({key_attr: int_keys[0]})
                    if not records:
                        records = ctrl.search_hash(keys[0])
                except ValueError:
                    records = ctrl.search_hash(keys[0])
        else:
            records = ctrl.search([{key_attr: key} for key in keys])
            if not records:
                try:
                    int_keys = [int(key) for key in keys]
                    records = ctrl.search([{key_attr: int_key} for int_key in int_keys])
                    if not records:
                        records = ctrl.search_hash(keys)
                except ValueError:
                    records = ctrl.search_hash(keys)
        return records

    def _pull_records(self, storage_level, keys, mode):
        print("Should pull %s" % keys)

        token, db_name = Project.connected()
        ENTERPRISE_STORAGE.connect_database(url=ENTERPRISE_URL, db_name=db_name, token=token)
        enterprise_ctl = self.model.controller(ENTERPRISE_STORAGE)
        base_records = self._find_records(enterprise_ctl, keys)
        if not base_records:
            self.parser.error("No %s matching %s found." % (self.model.name, keys))
        print(base_records)
        records_to_pull = enterprise_ctl.traverse_records(base_records)

        if mode == 'dryrun':
            for record in records_to_pull:
                self.logger.info("Would pull %s %s", record.name, record.hash_digest())
            return EXIT_SUCCESS

        if SYSTEM_STORAGE.name in storage_level:
            local_storage = SYSTEM_STORAGE
        elif USER_STORAGE.name in storage_level:
            local_storage = USER_STORAGE
        else:
            local_storage = PROJECT_STORAGE

        proj = None
        if mode == 'project':
            proj = Project.selected()

        with local_storage as storage:
            eid_map = {}
            for record in records_to_pull:
                local_ctl = record.controller(storage)
                try:
                    remote_eid, already_present = record.controller(ENTERPRISE_STORAGE). \
                        transport_record(record, local_ctl, eid_map, 'pull', proj)
                    eid_map[record.hash_digest()] = remote_eid
                    if already_present:
                        self.logger.info("Skipped %s %s, already present in %s.", record.name,
                                         record.hash_digest(), local_storage.name)
                    else:
                        self.logger.info("Pulled %s %s to %s.", record.name, record.hash_digest(), local_storage.name)
                except UniqueAttributeError as e:
                    raise ConfigurationError("Unable to pull %s %s because an existing record "
                                             "with the same primary key %s already exists." %
                                             (record.name, record.hash_digest(), e.unique))

        if proj is not None:
            Project.controller().select(proj)

        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        keys = getattr(args, 'keys', None)
        mode = getattr(args, 'mode', None) or 'none'
        storage_level = arguments.parse_storage_flag(args)
        if ENTERPRISE_STORAGE.name in storage_level:
            self.parser.error("Can't pull from Enterprise to Enterprise.")
        return self._pull_records(storage_level, keys, mode)
