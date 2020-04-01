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
"""``measurement edit`` subcommand."""

from taucmdr.error import ImmutableRecordError, IncompatibleRecordError
from taucmdr.cli import arguments
from taucmdr.cli.cli_view import EditCommand
from taucmdr.cli.commands.measurement.copy import COMMAND as measurement_copy_cmd
from taucmdr.cli.commands.experiment.delete import COMMAND as experiment_delete_cmd
from taucmdr.model.measurement import Measurement
from taucmdr.model.experiment import Experiment


class MeasurementEditCommand(EditCommand):
    """``measurement edit`` subcommand."""

    def _parse_args(self, argv):
        args = super(MeasurementEditCommand, self)._parse_args(argv)
        if hasattr(args, 'select_file'):
            if args.select_file.lower() == 'none':
                args.select_file = None
        return args

    def _update_record(self, store, data, key):
        try:
            retval = super(MeasurementEditCommand, self)._update_record(store, data, key)
        except (ImmutableRecordError, IncompatibleRecordError) as err:
            err.hints = ["Use `%s` to create a modified copy of the measurement" % measurement_copy_cmd,
                         "Use `%s` to delete the experiments." % experiment_delete_cmd]
            raise err
        if not retval:
            rebuild_required = Experiment.rebuild_required()
            if rebuild_required:
                self.logger.info(rebuild_required)
        return retval

    def main(self, argv):
        args = self._parse_args(argv)
        store = arguments.parse_storage_flag(args)[0]
        data = {attr: getattr(args, attr) for attr in self.model.attributes if hasattr(args, attr)}
        meas_name = args.name
        try:
            force_tau_options = args.force_tau_options
        except AttributeError:
            pass
        else:
            # Unset force_tau_options if it was already set and --force-tau-options=none
            if data.pop('force_tau_options', False) and [i.lower().strip() for i in force_tau_options] == ['none']:
                meas_ctrl = Measurement.controller(store)
                if 'force_tau_options' in meas_ctrl.one({"name": meas_name}):
                    meas_ctrl.unset(['force_tau_options'], {'name': meas_name})
                    self.logger.info("Removed 'force-tau-options' from measurement '%s'.", meas_name)
                else:
                    self.logger.info("'force-tau-options' was not present in measurement '%s'.", meas_name)
            else:
                data['force_tau_options'] = force_tau_options
                self.logger.info("Added 'force-tau-options' to measurement '%s'.", meas_name)
        try:
            extra_tau_options = args.extra_tau_options
        except AttributeError:
            pass
        else:
            # Unset extra_tau_options if it was already set and --extra-tau-options=none
            if data.pop('extra_tau_options', False) and [i.lower().strip() for i in extra_tau_options] == ['none']:
                meas_ctrl = Measurement.controller(store)
                if 'extra_tau_options' in meas_ctrl.one({"name": meas_name}):
                    meas_ctrl.unset(['extra_tau_options'], {'name': meas_name})
                    self.logger.info("Removed 'extra-tau-options' from measurement '%s'.", meas_name)
                else:
                    self.logger.info("'extra-tau-options' was not present in measurement '%s'.", meas_name)

            else:
                data['extra_tau_options'] = extra_tau_options
                self.logger.info("Added 'extra-tau-options' to measurement '%s'.", meas_name)

        key_attr = self.model.key_attribute
        try:
            data[key_attr] = args.new_key
        except AttributeError:
            pass
        key = getattr(args, key_attr)
        return self._update_record(store, data, key)


COMMAND = MeasurementEditCommand(Measurement, __name__)
