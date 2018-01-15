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
"""ParaProf style horizontal bar chart implemented using Plotly"""

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial

import nbformat

import inspect


def run_plotly_trial_bar_plot(trial_id, metric, top_n = 100):
    import six
    import pandas as pd
    import plotly.graph_objs as go
    def build_bar_plot(_trial, _metric):
        metric_data = trial.get_profile_data().interval_data()[[_metric]]
        idata = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
        plotframe = pd.concat([idata[:top_n], idata[top_n:].sum(level=0).rename({_metric: 'MISC'})], copy=False)
        indices = [str(i) for i in plotframe.columns.values]
        num_indices = len(indices)
        data = [go.Bar(
            y=indices[::-1],
            x=row.values[::-1],
            name=index[1],
            orientation='h',
            hoverinfo='text',
            text=["<br>".join([index[1][i:i + 75] for i in range(0, len(index[1]), 75)])] * num_indices
        ) for index, row in plotframe.iterrows()]
        data[-1]['marker'] = {'color': '#000000'}
        layout = go.Layout(
            barmode='stack',
            showlegend=False,
            hovermode='closest'
        )
        fig = go.Figure(data=data, layout=layout)
        return fig

    if isinstance(trial_id, six.string_types):
        trial = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")
    return build_bar_plot(trial, metric)


def show_plotly_trial_bar_plot(trial_id, metric, top_n = 100):
    import plotly.offline as py
    fig = run_plotly_trial_bar_plot(trial_id, metric, top_n=top_n)
    py.iplot(fig)


class PlotlyTrialBarPlotVisualizer(AbstractAnalysis):
    def __init__(self, name='trial-barplot-plotly', description='Trial Bar Plot (Plotly)'):
        super(PlotlyTrialBarPlotVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        if not inputs:
            raise ConfigurationError("Trial bar plot requires that at least one Trial be selected.");
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Bar plots can only be built for Trials.")
        metric = kwargs.get('metric', 'Exclusive')
        return inputs, metric

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric = self._check_input(inputs, **kwargs)
        trial = trials[0]
        all_trial_hashes = [t.hash_digest() for t in Trial.controller(ANALYSIS_STORAGE).all()]
        prof_data = trial.get_profile_data()
        all_metrics = prof_data.get_value_types()
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
        """Get Jupyter input cells containing code which will create a barplot when
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
        commands = [ 'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                    inspect.getsource(run_plotly_trial_bar_plot),
                    inspect.getsource(show_plotly_trial_bar_plot)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        for trial in trials:
            if interactive:
                notebook_cells.append(nbformat.v4.new_code_cell(
                    self.get_interaction_code(inputs, 'show_plotly_trial_bar_plot', **kwargs)))
            else:
                digest = trial.hash_digest()
                notebook_cells.append(nbformat.v4.new_code_cell(
                    'show_plotly_trial_bar_plot(Trial.controller(ANALYSIS_STORAGE).search_hash("%s")[0], "%s")'

                    % (digest, metric)))
        return notebook_cells

    def run(self, inputs, *args, **kwargs):
        """Create a barplot as direct notebook output for the trials in `inputs`.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric = self._check_input(inputs, **kwargs)
        return [run_plotly_trial_bar_plot(trial, metric) for trial in trials]


ANALYSIS = PlotlyTrialBarPlotVisualizer()
