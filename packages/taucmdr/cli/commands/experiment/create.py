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
"""``experiment create`` subcommand."""

from __future__ import absolute_import
from taucmdr import EXIT_SUCCESS
from taucmdr.error import UniqueAttributeError
from taucmdr.model.experiment import Experiment
from taucmdr.model.project import Project
from taucmdr.model.target import Target
from taucmdr.model.application import Application
from taucmdr.model.measurement import Measurement
from taucmdr.cli.cli_view import CreateCommand
from taucmdr.cf.storage.levels import PROJECT_STORAGE


class ExperimentCreateCommand(CreateCommand):
    """``experiment create`` subcommand."""

    def _construct_parser(self):
        parser = super(ExperimentCreateCommand, self)._construct_parser()
        # All three options must be given to create the experiments
        parser['--target'].required = True
        parser['--application'].required = True
        parser['--measurement'].required = True
        return parser

    def _create_record(self, store, data):
        ctrl = self.model.controller(store)
        key_attr = self.model.key_attribute
        key = data[key_attr]
        try:
            ctrl.create(data)
        except UniqueAttributeError:
            self.parser.error("A {} with {}='{}' already exists".format(self.model_name, key_attr, key))
        self.logger.info("Created a new experiment '%s'", key)
        return EXIT_SUCCESS

    def main(self, argv):
        args = self._parse_args(argv)
        proj_ctrl = Project.controller()
        proj = proj_ctrl.selected()
        targ = Target.controller(proj_ctrl.storage).one({'name': args.target})
        if targ is None:
            self.parser.error("A target with name %s does not exist." %args.target)
        app = Application.controller(proj_ctrl.storage).one({'name': args.application})
        if app is None:
            self.parser.error("An application with name %s does not exist." %args.application)
        meas = Measurement.controller(proj_ctrl.storage).one({'name': args.measurement})
        if meas is None:
            self.parser.error("A measurement with name %s does not exist." %args.measurement)
        data = {'name': args.name,
                'project': proj.eid,
                'target': targ.eid,
                'application': app.eid,
                'measurement': meas.eid}
        return self._create_record(PROJECT_STORAGE, data)


COMMAND = ExperimentCreateCommand(Experiment, __name__, summary_fmt="Create a new experiment from project components.",
                                  include_storage_flag=False)
