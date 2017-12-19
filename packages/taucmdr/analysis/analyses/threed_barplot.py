# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, ParaTools, Inc.
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
"""ParaProf style 3D bar chart"""

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial

import nbformat

import inspect


def get_3d_bar_plot_data(trial_id, metric):
    from taucmdr.data.tauprofile import TauProfile
    from bokeh import palettes
    import pandas as pd

    def build_bar_plot(_trial, _metric):
        trial_num = _trial['number']
        trial_data = _trial.get_data()
        indices = TauProfile.indices(_trial.get_data())[::-1]
        dfs = []
        for (node, context, thread) in indices:
            df = trial_data[node][context][thread].interval_data().loc[trial_num, node, context, thread][[_metric]]
            df.columns = ["(%d, %d, %d)" % (node, context, thread)]
            dfs.append(df)
        overall = pd.concat(dfs[::-1], axis=1, join='inner')
        overall.sort_index(inplace=True)
        max_height = overall.max().max()
        overall = (overall / max_height) * 100
        palette = palettes.viridis(101)
        heights = overall.values.flatten().tolist()
        colors = [palette[int(x)] for x in heights]
        result = {'xLabels': overall.columns.tolist(), 'yLabels': overall.index.tolist(), 'heights': heights, 'colors': colors}
        return result

    if isinstance(trial_id, str):
        trial = Trial.controller(PROJECT_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")
    return build_bar_plot(trial, metric)


def show_3d_bar_plot(trial_id, metric, height=700, width=900):
    from IPython.display import display
    import json
    data = get_3d_bar_plot_data(trial_id, metric)
    data['height'] = height
    data['width'] = width
    return display({'application/tau': json.dumps(data)}, raw=True)


class ThreeDBarPlotVisualizer(AbstractAnalysis):
    def __init__(self, name='trial-3d-barplot', description='Trial 3D Bar Plot'):
        super(ThreeDBarPlotVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        if not inputs:
            raise ConfigurationError("3D bar plot requires that at least one Trial be selected.");
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("3D bar plots can only be built for Trials.")
        metric = kwargs.get('metric', 'Exclusive')
        return inputs, metric

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric = self._check_input(inputs, **kwargs)
        trial = trials[0]
        all_trial_hashes = [trial.hash_digest() for trial in Trial.controller(PROJECT_STORAGE).all()]
        all_metrics = self.get_metric_names(trials, numeric_only=True)
        result = [
            {'name': 'trial_id',
             'values': all_trial_hashes,
             'default': trial.hash_digest(),
             'type': 'widgets.Dropdown'},

            {'name': 'metric',
             'values': all_metrics,
             'default': metric,
             'type': 'widgets.Dropdown'}
        ]
        return result

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cells containing code which will create a 3D barplot when
         executed for the trials in `inputs`.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Keyword Args:
            metric (str): The name of the metric to visualize

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the barplot.

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = ['from taucmdr.analysis.analyses.trial_barplot import TrialBarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(get_3d_bar_plot_data),
                    inspect.getsource(show_3d_bar_plot)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        for trial in trials:
            if interactive:
                notebook_cells.append(nbformat.v4.new_code_cell(
                    self.get_interaction_code(inputs, 'show_3d_bar_plot', **kwargs)))
            else:
                digest = trial.hash_digest()
                notebook_cells.append(nbformat.v4.new_code_cell(
                    'show_3d_bar_plot(Trial.controller(PROJECT_STORAGE).search_hash("%s")[0], "%s")'
                    % (digest, metric)))
        return notebook_cells

    def run(self, inputs, *args, **kwargs):
        """Create a 3D barplot as direct notebook output for the trials in `inputs`.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric = self._check_input(inputs, **kwargs)
        return [show_3d_bar_plot(trial, metric) for trial in trials]


ANALYSIS = ThreeDBarPlotVisualizer()
