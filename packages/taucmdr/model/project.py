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
"""Project data model.

A project collects multiple :any:`Target`, :any:`Application`, and :any:`Measurement`
configurations in a single container.  Selecting one of each forms a new :any:`Experiment`.
Each application of the :any:`Experiment` generates a new :any:`Trial` record along with
some performance data (profiles, traces, etc.).
"""

import os
from taucmdr import logger
from taucmdr.error import InternalError, ProjectSelectionError, ExperimentSelectionError
from taucmdr.mvc.model import Model
from taucmdr.mvc.controller import Controller
from taucmdr.cf.storage.levels import PROJECT_STORAGE


LOGGER = logger.get_logger(__name__)


def attributes():
    from taucmdr.model.target import Target
    from taucmdr.model.application import Application
    from taucmdr.model.measurement import Measurement
    from taucmdr.model.experiment import Experiment
    return {
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': 'project name',
        },
        'targets': {
            'collection': Target,
            'via': 'projects',
            'description': 'targets used by this project'
        },
        'applications': {
            'collection': Application,
            'via': 'projects',
            'description': 'applications used by this project'
        },
        'measurements': {
            'collection': Measurement,
            'via': 'projects',
            'description': 'measurements used by this project'
        },
        'experiments': {
            'collection': Experiment,
            'via': 'project',
            'description': 'experiments formed from this project'
        },
        'experiment': {
            'model': Experiment,
            'description': 'the current experiment',
        },
        'init_options': {
            'type': 'string',
            'description': 'options passed to initialize command',
        },
    }


class ProjectController(Controller):
    """Project data controller."""

    def create(self, data):
        if self.storage is not PROJECT_STORAGE:
            raise InternalError("Projects may only be created in project-level storage")
        return super(ProjectController, self).create(data)

    def delete(self, keys):
        to_delete = self.one(keys)

        try:
            selected = self.selected()
        except ProjectSelectionError:
            pass
        else:
            if selected == to_delete:
                self.unselect()

        super(ProjectController, self).delete(keys)

    def select(self, project, experiment=None):
        self.storage['selected_project'] = project.eid
        if experiment is not None:
            for attr in 'target', 'application', 'measurement':
                if experiment[attr] not in project[attr+'s']:
                    raise InternalError("Experiment contains %s not in project" % attr)
            self.update({'experiment': experiment.eid}, project.eid)
            experiment.configure()

    def unselect(self):
        if self.storage.contains({'key': 'selected_profile'}):
            del self.storage['selected_project']

    def selected(self):
        try:
            selected = self.one(self.storage['selected_project'])
            if not selected:
                raise KeyError
        except KeyError:
            raise ProjectSelectionError("No project selected")
        else:
            return selected


class Project(Model):
    """Project data controller."""

    __attributes__ = attributes

    __controller__ = ProjectController

    def on_update(self, changes):
        from taucmdr.model.experiment import Experiment
        from taucmdr.model.compiler import Compiler
        try:
            old_value, new_value = changes['experiment']
        except KeyError:
            # We only care about changes to experiment
            return
        if old_value and new_value:
            new_expr = Experiment.controller().one(new_value)
            old_expr = Experiment.controller().one(old_value)
            for model_attr in 'target', 'application', 'measurement':
                if old_expr[model_attr] != new_expr[model_attr]:
                    new_model = new_expr.populate(model_attr)
                    old_model = old_expr.populate(model_attr)
                    for attr, props in new_model.attributes.iteritems():
                        if props.get('rebuild_required'):
                            new_value = new_model.get(attr, None)
                            old_value = old_model.get(attr, None)
                            if old_value != new_value:
                                if props.get('model') == Compiler:
                                    new_comp = Compiler.controller(self.storage).one(new_value)
                                    old_comp = Compiler.controller(self.storage).one(old_value)
                                    new_path = new_comp['path'] if new_comp else None
                                    old_path = old_comp['path'] if old_comp else None
                                    message = {attr: (old_path, new_path)}
                                    self.controller(self.storage).push_to_topic('rebuild_required', message)
                                elif props.get('argparse').get('metavar') == '<metric>':
                                    old_papi = [metric for metric in old_value if 'PAPI' in metric]
                                    new_papi = [metric for metric in new_value if 'PAPI' in metric]
                                    if bool(old_papi) != bool(new_papi):
                                        message = {attr: (old_value, new_value)}
                                        self.controller(self.storage).push_to_topic('rebuild_required', message)
                                else:
                                    message = {attr: (old_value, new_value)}
                                    self.controller(self.storage).push_to_topic('rebuild_required', message)

    @classmethod
    def controller(cls, storage=PROJECT_STORAGE):
        return cls.__controller__(cls, storage)

    @classmethod
    def selected(cls, storage=PROJECT_STORAGE):
        try:
            return cls.__controller__(cls, storage).selected()
        except ProjectSelectionError:
            return None

    @property
    def prefix(self):
        return os.path.join(self.storage.prefix, self['name'])

    def experiment(self):
        """Gets the currently selected experiment configuration.

        Returns:
            Experiment: The current experiment

        Raises:
            ExperimentSelectionError: No experiment currently selected.
        """
        try:
            return self.populate('experiment')
        except KeyError:
            raise ExperimentSelectionError("No experiment configured")
