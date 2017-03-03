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
from taucmdr.error import InternalError, ConfigurationError
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
            'on_change': Project.on_experiment_change
        },
        'force_tau_options': {
            'type': 'array',
            'description': "forcibly add options to TAU_OPTIONS environment variable (not recommended)",
            'rebuild_on_change': True,
            'argparse': {'flags': ('--force-tau-options',),
                         'metavar': '<option>'},
            'compat': {True: Project.discourage('force_tau_options')}
        }
    }


class ProjectSelectionError(ConfigurationError):
    
    def __init__(self, value, *hints):
        from taucmdr.cli.commands.project.create import COMMAND as project_create_cmd
        from taucmdr.cli.commands.project.select import COMMAND as project_select_cmd
        from taucmdr.cli.commands.project.list import COMMAND as project_list_cmd
        if not hints:
            hints = ("Use `%s` to create a new project configuration." % project_create_cmd,
                     "Use `%s <project_name>` to select a project configuration." % project_select_cmd,
                     "Use `%s` to see available project configurations." % project_list_cmd)    
        super(ProjectSelectionError, self).__init__(value, *hints)


class ExperimentSelectionError(ConfigurationError):
    
    def __init__(self, value, *hints):
        from taucmdr.cli.commands.select import COMMAND as select_cmd
        from taucmdr.cli.commands.experiment.create import COMMAND as experiment_create_cmd
        from taucmdr.cli.commands.dashboard import COMMAND as dashboard_cmd
        from taucmdr.cli.commands.project.list import COMMAND as project_list_cmd
        if not hints:
            hints = ("Use `%s` or `%s` to create a new experiment." % (select_cmd, experiment_create_cmd),
                     "Use `%s` to see current project configuration." % dashboard_cmd,
                     "Use `%s` to see available project configurations." % project_list_cmd)    
        super(ExperimentSelectionError, self).__init__(value, *hints)


class ProjectController(Controller):
    """Project data controller."""
    
    def create(self, data):
        if self.storage is not PROJECT_STORAGE:
            raise InternalError("Projects may only be created in project-level storage")
        return super(ProjectController, self).create(data)
    
    def delete(self, keys):
        super(ProjectController, self).delete(keys)
        try:
            selected = self.selected()
        except ProjectSelectionError:
            pass
        else:
            if selected is None:
                self.unselect()

    def select(self, project, experiment=None):
        self.storage['selected_project'] = project.eid
        if experiment is not None:
            for attr in 'target', 'application', 'measurement':
                if experiment[attr] not in project[attr+'s']:
                    raise InternalError("Experiment contains %s not in project" % attr)
            self.update({'experiment': experiment.eid}, project.eid)
            tau = experiment.configure()
            tau.check_metrics()
    
    def unselect(self):
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
    
    @classmethod
    def _check_rebuild_required(cls, model_attr, old, new):
        from taucmdr.model.experiment import Experiment
        model_cls = Experiment.attributes[model_attr]['model']
        model_new = new.populate(model_attr)
        model_old = old.populate(model_attr)
        changed = {}
        for attr, props in model_cls.attributes.iteritems():
            if 'on_change' in props:
                old_value = model_old.get(attr, None)
                new_value = model_new.get(attr, None)
                if old_value != new_value:
                    changed[attr] = (old_value, new_value)
        return changed
    
    @classmethod
    def on_experiment_change(cls, model, attr, new_value):
        from taucmdr.model.experiment import Experiment
        old_value = model.get(attr, None)
        if old_value and new_value:
            new = Experiment.controller().one(new_value)
            old = Experiment.controller().one(old_value)
            rebuild_required = {}
            for model_attr in 'target', 'application', 'measurement':
                if old[model_attr] != new[model_attr]:
                    rebuild_required.update(cls._check_rebuild_required(model_attr, old, new))
            if rebuild_required:
                cls.controller(model.storage).push_to_topic('rebuild_required', rebuild_required)

    @classmethod
    def controller(cls, storage=PROJECT_STORAGE):
        return cls.__controller__(cls, storage)
    
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
