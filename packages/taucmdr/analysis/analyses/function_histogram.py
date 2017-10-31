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
"""ParaProf-style function histogram"""

import inspect

import numpy as np
import nbformat

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial


def show_function_histogram(trial_ids, metric, timer, bins):
    from taucmdr import logger
    from taucmdr.gui.interaction import InteractivePlotHandler
    from bokeh.io import output_notebook
    from bokeh.plotting import figure

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)

    def build_histogram(_trials, _metric, _timer, _bins):
        hist, edges = FunctionHistogramVisualizer.trials_to_histogram(_trials, _metric, _timer, _bins)
        fig = figure(plot_width=80, plot_height=40, title=timer, output_backend="webgl")
        fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color="red", line_color="black")
        fig.xaxis.axis_label = metric
        fig.yaxis.axis_label = 'Threads'
        return fig

    if isinstance(trial_ids[0], str):
        trials = Trial.controller(PROJECT_STORAGE).search_hash(trial_ids)
    elif isinstance(trial_ids[0], Trial):
        trials = trial_ids
    else:
        raise ValueError("Inputs must be hashes or Trials")
    hist_fig = build_histogram(trials, metric, timer, bins)
    plot = InteractivePlotHandler(hist_fig)
    plot.show()


class FunctionHistogramVisualizer(AbstractAnalysis):
    def __init__(self, name='function-histogram', description='Function Histogram'):
        super(FunctionHistogramVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def trials_to_histogram(trials, metric, timer, bins):
        data_for_timer = np.array([])
        for trial in trials:
            trial_num = trial['number']
            trial_data = trial.get_data()
            indices = TauProfile.indices(trial_data)
            for n, c, t in indices:
                df = trial_data[n][c][t].interval_data()[[metric]].loc[trial_num, n, c, t]
                data_for_timer = np.append(data_for_timer, df.loc[timer])
        hist, edges = np.histogram(data_for_timer, bins=bins)
        return hist, edges

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Function histograms can only be built for trials")
        metric = kwargs.get('metric', 'Exclusive')
        timer = kwargs.get('timer', '.TAU application')
        bins = kwargs.get('bins', 10)
        return inputs, metric, timer, bins

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric, timer, bins = self._check_input(inputs, **kwargs)
        default_trial_ids = [trial.hash_digest() for trial in trials]
        all_trial_hashes = [trial.hash_digest() for trial in Trial.controller(PROJECT_STORAGE).all()]
        all_timers = self.get_timer_names(trials)
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

            {'name': 'timer',
             'values': all_timers,
             'default': timer,
             'type': 'widgets.Dropdown'},

            {'name': 'bins',
             'values': range(1,101),
             'default': bins,
             'type': 'widgets.BoundedIntText'},
        ]
        return result

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cells containing code which will create a histogram showing
        the distribution of timer values for a function over multiple profiles.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Keyword Args:
            metric (str): The name of the metric to visualize
            timer (str): The name of the timer for which to construct the histogram
            bins (int): The number of bins to use for the histogram

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the histogram

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        trials, metric, timer, bins = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = ['from taucmdr.analysis.analyses.function_histogram import FunctionHistogramVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(show_function_histogram)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "Trial.controller(PROJECT_STORAGE).search_hash([%s])" % (",".join(
            ['"%s"' % trial.hash_digest() for trial in trials]))
        if interactive:
            show_plot_str = self.get_interaction_code(inputs, 'show_function_histogram', *args, **kwargs)
        else:
            show_plot_str = 'show_function_histogram(%s, "%s", "%s", %s)' % (trials_list_str, metric, timer, bins)
        notebook_cells.append(nbformat.v4.new_code_cell(show_plot_str))
        return notebook_cells

    def run(self, inputs, *args, **kwargs):
        """Create a histogram showing the distribution of timer values for a function over multiple profiles.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize
            timer (str): The name of the timer for which to construct the histogram
            bins (int): The number of bins to use for the histogram

        Returns:
            The histogram as a Jupyter-renderable object.

        Raises:
            ConfigurationError: The provided models are not Trials
        """

        trials, metric, timer, bins = self._check_input(inputs, **kwargs)
        show_function_histogram(trials, metric, timer, bins)


ANALYSIS = FunctionHistogramVisualizer()
