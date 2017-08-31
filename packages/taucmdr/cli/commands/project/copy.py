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
"""``project copy`` subcommand."""

from taucmdr import EXIT_SUCCESS
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import CopyCommand
from taucmdr.model.project import Project
from taucmdr.model.target import Target
from taucmdr.model.application import Application
from taucmdr.model.measurement import Measurement
from taucmdr.cf.storage.levels import PROJECT_STORAGE


class ProjectCopyCommand(CopyCommand):
    """``project copy`` subcommand."""
    
    def _parse_explicit(self, args, model):
        acc = set()
        ctrl = model.controller(PROJECT_STORAGE)
        model_name = model.name.lower()
        try:
            names = getattr(args, model_name)
        except AttributeError:
            pass
        else:
            for name in names: 
                found = ctrl.one({"name": name})
                if not found:
                    self.parser.error('There is no %s named %s.' % (model_name, name))
                else:
                    acc.add(found)
        return acc
    
    def _construct_parser(self):
        parser = super(ProjectCopyCommand, self)._construct_parser()
        parser.add_argument('--target',
                            help="Target configurations in the project copy",
                            metavar='t',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--application',
                            help="Application configurations in the project copy",
                            metavar='a',
                            nargs='+',
                            default=arguments.SUPPRESS)
        parser.add_argument('--measurement',
                            help="Measurement configurations in the project copy",
                            metavar='m',
                            nargs='+',
                            default=arguments.SUPPRESS)
        return parser
    
    def _copy_record(self, store, updates, key):
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        matching = ctrl.search({key_attr: key})
        if not matching:
            self.parser.error("No %s-level %s with %s='%s'." % (ctrl.storage.name, self.model_name, key_attr, key))
        elif len(matching) > 1:
            raise InternalError("More than one %s-level %s with %s='%s' exists!" % 
                                (ctrl.storage.name, self.model_name, key_attr, key))
        else:
            found = matching[0]
        data = dict(found)
        data.pop('experiment', None)
        data.pop('experiments', None)
        data.update(updates)
        key_attr = self.model.key_attribute
        key = data[key_attr]
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A %s with %s='%s' already exists" % (self.model_name, key_attr, key))
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        targets = self._parse_explicit(args, Target)
        applications = self._parse_explicit(args, Application)
        measurements = self._parse_explicit(args, Measurement)

        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        
        key_attr = self.model.key_attribute
        try:
            data[key_attr] = getattr(args, 'copy_%s' % key_attr)
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        
        if targets:
            data['targets'] = [model.eid for model in targets]
        if applications:
            data['applications'] = [model.eid for model in applications]
        if measurements: 
            data['measurements'] = [model.eid for model in measurements]
        
        return self._copy_record(PROJECT_STORAGE, data, key)


COMMAND = ProjectCopyCommand(Project, __name__)    
