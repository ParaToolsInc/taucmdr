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
"""PerfExplorer-style runtime breakdown chart using Plotly"""

import inspect
import nbformat

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial


def run_runtime_breakdown_plotly(trial_ids, metric, top_n):
    import six
    from taucmdr import logger

    logger.set_log_level('WARN')

    def build_runtime_breakdown(trials_, metric_):
        import pandas as pd
        import plotly.graph_objs as go
        from itertools import izip, cycle
        from taucmdr.gui.color import ColorMapping
        profile_sums = []
        for trial in trials_:
            metric_by_profile = trial.get_profile_data().interval_data()[[metric_]].unstack()
            num_cores = metric_by_profile.shape[0]
            profile_sum = metric_by_profile.sum(level=1).transpose().rename(columns={0: num_cores})
            profile_sums.append(profile_sum)
        timer_by_cores = pd.concat(profile_sums, axis=1).sort_values(1, axis=0, ascending=False).loc[metric_]
        top_profile_sum = timer_by_cores[:top_n].append(timer_by_cores[top_n:].sum().rename("MISC"))
        percent_time = top_profile_sum.divide(top_profile_sum.sum()).cumsum()
        x_vals = timer_by_cores.columns.values
        data = [go.Scatter(
            name=abs_row[0],
            x=x_vals,
            y=percent_row[1].values,
            text=["%d<br>%s" % (v, "<br>".join([abs_row[0][i:i + 75] for i in range(0, len(abs_row[0]), 75)])) for v in
                  abs_row[1].values],
            mode='lines',
            line=dict(
                color=color,
            ),
            fill='tonexty',
            hoverinfo='text',
        ) for abs_row, percent_row, color in
            izip(timer_by_cores.iterrows(), percent_time.iterrows(), cycle(ColorMapping.get_default_palette()))]
        data[-1]['line']['color'] = '#000000'
        layout = go.Layout(
            showlegend=False,
            hovermode='closest',
        )
        fig = go.Figure(data=data, layout=layout)
        return fig

    if not isinstance(trial_ids, list):
        trial_ids = list(trial_ids)
    if isinstance(trial_ids[0], six.string_types):
        trials = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_ids)
    elif isinstance(trial_ids[0], Trial):
        trials = trial_ids
    else:
        raise ValueError("Inputs must be hashes or Trials")
    breakdown = build_runtime_breakdown(trials, metric)
    return breakdown


def show_runtime_breakdown_plotly(trial_ids, metric, top_n):
    import plotly.offline as py
    fig = run_runtime_breakdown_plotly(trial_ids=trial_ids, metric=metric, top_n=top_n)
    py.iplot(fig)


class PlotlyRuntimeBreakdownVisualizer(AbstractAnalysis):
    def __init__(self, name='runtime-breakdown-plotly', description='Runtime Breakdown (Plotly)'):
        super(PlotlyRuntimeBreakdownVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Runtime breakdowns can only be built for plots")
        metric = kwargs.get('metric', 'Exclusive')
        top_n = kwargs.get('top_n', 50)
        return inputs, metric, top_n

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric, top_n = self._check_input(inputs, **kwargs)
        default_trial_ids = [t.hash_digest() for t in trials]
        all_trial_hashes = [t.hash_digest() for t in Trial.controller(ANALYSIS_STORAGE).all()]
        all_metrics = self.get_metric_names(trials, numeric_only=True)
        result = [
            {'name': 'trial_ids',
             'values': all_trial_hashes,
             'default': default_trial_ids,
             'type': 'widgets.SelectMultiple'},

            {'name': 'metric',
             'values': all_metrics,
             'default': metric,
             'type': 'widgets.Dropdown'},

            {'name': 'top_n',
             'values': range(1, 200),
             'default': top_n,
             'type': 'widgets.BoundedIntText'}

        ]
        return result

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cells containing code which will create a stacked area chart
        showing the breakdown of runtime across trials.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Keyword Args:
            metric (str): The name of the metric to visualize

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the runtime breakdown.

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric, top_n = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = [ 'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                     inspect.getsource(run_runtime_breakdown_plotly),
                    inspect.getsource(show_runtime_breakdown_plotly)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "Trial.controller(ANALYSIS_STORAGE).search_hash([%s])" % (",".join(
            ['"%s"' % trial.hash_digest() for trial in trials]))
        if interactive:
            show_plot_str = self.get_interaction_code(inputs, 'show_runtime_breakdown_plotly', *args, **kwargs)
        else:
            show_plot_str = 'show_runtime_breakdown_plotly(%s, "%s", %s)' % (trials_list_str, metric, top_n)
        notebook_cells.append(nbformat.v4.new_code_cell(show_plot_str))
        return notebook_cells

    def run(self, inputs, *args, **kwargs):
        """Create a stacked area chart showing the breakdown of runtime across trials.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric, top_n = self._check_input(inputs, **kwargs)
        run_runtime_breakdown_plotly(trials, metric, top_n)


ANALYSIS = PlotlyRuntimeBreakdownVisualizer()
