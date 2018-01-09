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
"""PerfExplorer-style correlation plot"""

import inspect

import nbformat
import numpy as np
from bokeh.models import ColumnDataSource
from scipy import stats

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial


def run_correlation(trial_ids, metric_1, timer_1, metric_2, timer_2):
    from bokeh.plotting import figure

    def build_correlation_scatterplot(_trials, _metric_1, _timer_1, _metric_2, _timer_2):
        scatter_data_source = CorrelationAnalysis.trials_to_scatter_list(_trials, _metric_1, _timer_1, _metric_2, _timer_2)
        line_data_source, r_value = CorrelationAnalysis.linear_regression(scatter_data_source.data['x'], scatter_data_source.data['y'])
        fig = figure(plot_width=80, plot_height=40, title="Correlation Results: r = %s" % r_value)
        fig.scatter("x", "y", size=10, color="red", alpha=0.8, source=scatter_data_source)
        fig.line("x", "y", line_color="black", source=line_data_source)
        fig.xaxis.axis_label = "%s (%s)" % (_timer_1, _metric_1)
        fig.yaxis.axis_label = "%s (%s)" % (_timer_2, _metric_2)
        return fig, r_value

    if isinstance(trial_ids[0], str):
        trials = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_ids)
    elif isinstance(trial_ids[0], Trial):
        trials = trial_ids
    else:
        raise ValueError("Inputs must be hashes or Trials")
    correlation_fig, r_value = build_correlation_scatterplot(trials, metric_1, timer_1, metric_2, timer_2)
    return correlation_fig, r_value


def show_correlation(trial_ids, metric_1, timer_1, metric_2, timer_2):
    from taucmdr import logger
    from taucmdr.gui.interaction import InteractivePlotHandler
    from bokeh.io import output_notebook
    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)
    correlation_fig, r_value = run_correlation(trial_ids, metric_1, timer_1, metric_2, timer_2)
    plot = InteractivePlotHandler(correlation_fig)
    plot.show()


class CorrelationAnalysis(AbstractAnalysis):
    def __init__(self, name='correlation', description='Correlation'):
        super(CorrelationAnalysis, self).__init__(name=name, description=description)

    @staticmethod
    def trials_to_scatter_list(trials, metric_1, timer_1, metric_2, timer_2):
        xs = []
        ys = []
        for trial in trials:
            trial_num = trial['number']
            trial_data = trial.get_data()
            indices = TauProfile.indices(trial_data)
            for n, c, t in indices:
                df_1 = trial_data[n][c][t].interval_data()[[metric_1]].loc[trial_num, n, c, t]
                df_2 = trial_data[n][c][t].interval_data()[[metric_2]].loc[trial_num, n, c, t]
                xs.append(float(df_1.loc[timer_1]))
                ys.append(float(df_2.loc[timer_2]))
        data_source = ColumnDataSource(dict(x=xs, y=ys))
        return data_source

    @staticmethod
    def linear_regression(x, y):
        slope, intercept, rvalue, pvalue, stderr = stats.linregress(x, y)
        min_x, max_x = stats.describe(x).minmax
        line_x = np.linspace(min_x, max_x)
        line_y = intercept + slope * line_x
        data_source = ColumnDataSource(dict(x=line_x, y=line_y))
        return data_source, rvalue

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Function histograms can only be built for trials")
        metric_1 = kwargs.get('metric_1', 'Exclusive')
        timer_1 = kwargs.get('timer_1', '.TAU application')
        metric_2 = kwargs.get('metric_2', 'Exclusive')
        timer_2 = kwargs.get('timer_2', '.TAU application')
        return inputs, metric_1, timer_1, metric_2, timer_2

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric_1, timer_1, metric_2, timer_2 = self._check_input(inputs, **kwargs)
        default_trial_ids = [trial.hash_digest() for trial in trials]
        all_trial_hashes = [trial.hash_digest() for trial in Trial.controller(ANALYSIS_STORAGE).all()]
        all_timers = self.get_timer_names(trials)
        all_metrics = self.get_metric_names(trials, numeric_only=True)
        result = [
            {'name': 'trial_ids',
             'values': all_trial_hashes,
             'default': default_trial_ids,
             'type': 'widgets.SelectMultiple'},

            {'name': 'timer_1',
             'values': all_timers,
             'default': timer_1,
             'type': 'widgets.Dropdown'},

            {'name': 'metric_1',
             'values': all_metrics,
             'default': metric_1,
             'type': 'widgets.Dropdown'},

            {'name': 'timer_2',
             'values': all_timers,
             'default': timer_1,
             'type': 'widgets.Dropdown'},

            {'name': 'metric_2',
             'values': all_metrics,
             'default': metric_1,
             'type': 'widgets.Dropdown'},

        ]
        return result

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cells containing code which will create a scatterplot
        correlating two variables, with a linear regression line on top.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Keyword Args:
            metric_1 (str): The name of the metric to visualize on the X axis
            timer_1 (str): The name of the timer to visualize on the X axis
            metric_2 (str): The name of the metric to visualize on the Y axis
            timer_2 (str): The name of the timer to visualize on the Y axis

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the correlation

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric_1, timer_1, metric_2, timer_2 = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = ['from taucmdr.analysis.analyses.correlation import CorrelationAnalysis',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                    inspect.getsource(run_correlation),
                    inspect.getsource(show_correlation)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "Trial.controller(ANALYSIS_STORAGE).search_hash([%s])" % (",".join(
            ['"%s"' % trial.hash_digest() for trial in trials]))
        if interactive:
            show_plot_str = self.get_interaction_code(inputs, 'show_correlation', *args, **kwargs)
        else:
            show_plot_str = 'show_correlation(%s, "%s", "%s", "%s", "%s")' % \
                            (trials_list_str, metric_1, timer_1, metric_2, timer_2)
        notebook_cells.append(nbformat.v4.new_code_cell(show_plot_str))
        return notebook_cells

    def run(self, inputs, *args, **kwargs):
        """Create a scatterplot correlating two variables with a linear regression line, and get
        the R value for the correlation.

        Args:
            inputs (list of :obj:`Trial`): The trials to analyze.

        Keyword Args:
            metric_1 (str): The name of the metric to visualize on the X axis
            timer_1 (str): The name of the timer to visualize on the X axis
            metric_2 (str): The name of the metric to visualize on the Y axis
            timer_2 (str): The name of the timer to visualize on the Y axis

        Returns:
            tuple: (The histogram as a Jupyter-renderable object, r-value of correlation)

        Raises:
            ConfigurationError: The provided models are not Trials
        """

        trials, metric_1, timer_1, metric_2, timer_2 = self._check_input(inputs, **kwargs)
        return run_correlation(trials, metric_1, timer_1, metric_2, timer_2)


ANALYSIS = CorrelationAnalysis()
