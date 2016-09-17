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
from tau import logger
from tau.error import InternalError, ConfigurationError
from tau.mvc.model import Model
from tau.mvc.controller import Controller
from tau.cf.storage.levels import PROJECT_STORAGE


LOGGER = logger.get_logger(__name__)


def attributes():
    from tau.model.target import Target
    from tau.model.application import Application
    from tau.model.measurement import Measurement
    from tau.model.experiment import Experiment
    return {
        'name': {
            'primary_key': True,
            'type': 'string',
            'unique': True,
            'description': 'project name',
            'argparse': {'metavar': '<project_name>'}
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
            'description': 'the current experiment'
        },
        'force_tau_options': {
            'type': 'array',
            'description': "forcibly add options to TAU_OPTIONS environment variable (not recommended)",
            'application_rebuild': True,
            'argparse': {'flags': ('--force-tau-options',),
                         'metavar': '<option>',
                         'nargs': '+'},
            'compat': {True: Project.discourage('force_tau_options')}
        }
    }


class ProjectSelectionError(ConfigurationError):
    
    def __init__(self, value, *hints):
        from tau.cli.commands.project.create import COMMAND as project_create_cmd
        from tau.cli.commands.project.select import COMMAND as project_select_cmd
        from tau.cli.commands.project.list import COMMAND as project_list_cmd
        if not hints:
            hints = ("Use `%s` to create a new project configuration." % project_create_cmd,
                     "Use `%s <project_name>` to select a project configuration." % project_select_cmd,
                     "Use `%s` to see available project configurations." % project_list_cmd)    
        super(ProjectSelectionError, self).__init__(value, *hints)


class ExperimentSelectionError(ConfigurationError):
    
    def __init__(self, value, *hints):
        from tau.cli.commands.experiment.create import COMMAND as experiment_create_cmd
        from tau.cli.commands.project.list import COMMAND as project_list_cmd
        if not hints:
            hints = ("Use `%s` to create a new experiment." % experiment_create_cmd,
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

    def _check_rebuild(self, project, new_experiment):
        from tau.model.measurement import Measurement
        try:
            old_experiment = project.controller().selected().experiment()
        except (ProjectSelectionError, ExperimentSelectionError) as err:
            LOGGER.debug(err)
            return
        meas = new_experiment.populate('measurement')
        meas_old = old_experiment.populate('measurement')
        new_attrs = set(meas.keys())
        old_attrs = set(meas_old.keys())
        changed = {}
        for attr in new_attrs - old_attrs:
            if Measurement.attributes[attr]['application_rebuild']:
                changed[attr] = (None, meas[attr])
                break
        for attr in old_attrs - new_attrs:
            if Measurement.attributes[attr]['application_rebuild']:
                changed[attr] = (meas_old[attr], None)
                break
        for attr in new_attrs & old_attrs:
            if meas[attr] != meas_old[attr] and Measurement.attributes[attr]['application_rebuild']:
                changed[attr] = (meas_old[attr], meas[attr])
                break
        return changed
    
    def select(self, project, experiment=None):
        self.storage['selected_project'] = project.eid
        if experiment is not None:
            for attr in 'target', 'application', 'measurement':
                if experiment[attr] not in project[attr+'s']:
                    raise InternalError("Experiment contains %s not in project" % attr)
            changed = self._check_rebuild(project, experiment)
            self.update({'experiment': experiment.eid}, project.eid)
            experiment.configure()
            return changed
    
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
