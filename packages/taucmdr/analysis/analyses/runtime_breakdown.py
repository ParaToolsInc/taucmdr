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
"""PerfExplorer-style runtime breakdown chart"""

import operator
from collections import defaultdict
import inspect

from bokeh.models import ColumnDataSource
import pandas as pd
import numpy as np
import nbformat

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial


def show_runtime_breakdown(trial_ids, metric):
    import six
    from bokeh.plotting import figure
    from bokeh.io import output_notebook
    from taucmdr.gui.interaction import InteractivePlotHandler
    from taucmdr import logger

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)

    def build_runtime_breakdown(trials_, metric_):
        patch_lists = RuntimeBreakdownVisualizer.trials_to_patch_lists(trials_, metric_)
        title = trials_[0].populate('experiment')['name']
        fig = figure(title=title, plot_width=80, plot_height=40, output_backend="webgl", toolbar_location="right")
        fig.xaxis.axis_label = 'Number of Processors'
        fig.yaxis.axis_label = 'Percentage of Total Runtime (%s)' % (metric_, )
        fig.patches("x", "y", fill_color="color", line_color="color", alpha=0.9, source=patch_lists)
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
    plot = InteractivePlotHandler(breakdown, tooltips=[("Timer", "@name")])
    plot.show()


class RuntimeBreakdownVisualizer(AbstractAnalysis):
    def __init__(self, name='runtime-breakdown', description='Runtime Breakdown'):
        super(RuntimeBreakdownVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def trials_to_patch_lists(trials, metric):
        sum_times = defaultdict(lambda: pd.DataFrame([], columns=[metric], dtype=np.float64))
        timer_names = set()
        # We need to get:
        #     - Names for all of the timers in all of the trials (as we need a line for each timer)
        #     - The total times for each trial across all processors
        for trial in trials:
            trial_num = trial['number']
            trial_data = trial.get_data()
            indices = TauProfile.indices(trial_data)
            num_processors = len(indices)
            trial_total_time = 0
            trial_times = pd.DataFrame([], columns=[metric], dtype=np.float64)
            for n, c, t in indices:
                df = trial_data[n][c][t].interval_data()[[metric]].loc[trial_num, n, c, t]
                trial_times = trial_times.add(df, fill_value=0.0)
            for name, value in trial_times.itertuples():
                timer_names.add(name)
            # If there are multiple trials with the same num_processors, we aggregate them
            sum_times[num_processors] = sum_times[num_processors].add(trial_times, fill_value=0.0)
        # Convert the times to percentages
        for num_processors in sum_times.keys():
            sum_times[num_processors] = (sum_times[num_processors] / (sum_times[num_processors].sum())) * 100.0
        # Now we need to convert the percentages to 'patches' for Bokeh to render.
        # We need, for each timer, a list of x- and y-coordinates for the shape to be drawn.
        # From x = 1 to num_processors, we trace out the line with y, then drop down to the
        # previous line and draw it from x = num_processors to 1.
        mapping = ColorMapping()
        raw_xs = []
        raw_ys = []
        colors = []
        names = []
        sorted_sum_times = sorted(sum_times.items())
        for timer_name in timer_names:
            timer_xs = []
            timer_ys = []
            for num_processors, df in sorted_sum_times:
                timer_xs.append(num_processors)
                timer_ys.append(float(df.loc[timer_name]))
            raw_xs.append(timer_xs)
            raw_ys.append(timer_ys)
            colors.append(mapping[timer_name])
            names.append(timer_name)
        # Postprocess the y values to stack the lines
        ys = []
        last = [0.0] * len(sorted_sum_times)
        for row in raw_ys:
            # Draw the line from left-to-right above the last line
            processed_row = map(operator.add, row, last)
            # Then complete the polygon by drawing along the top of the last line
            return_row = last[::-1]
            last = processed_row
            ys.append(processed_row + return_row)
        # Postprocess the x values for the return
        xs = []
        for row in raw_xs:
            xs.append(row + row[::-1])
        # Package everything into a data source
        data_source = ColumnDataSource(dict(x=xs, y=ys, color=colors, name=names))
        return data_source

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Runtime breakdowns can only be built for plots")
        metric = kwargs.get('metric', 'Exclusive')
        return inputs, metric

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric = self._check_input(inputs, **kwargs)
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
        trials, metric = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = ['from taucmdr.analysis.analyses.runtime_breakdown import RuntimeBreakdownVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                    inspect.getsource(show_runtime_breakdown)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "Trial.controller(ANALYSIS_STORAGE).search_hash([%s])" % (",".join(
            ['"%s"' % trial.hash_digest() for trial in trials]))
        if interactive:
            show_plot_str = self.get_interaction_code(inputs, 'show_runtime_breakdown', *args, **kwargs)
        else:
            show_plot_str = 'show_runtime_breakdown(%s, "%s")' % (trials_list_str, metric)
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
        trials, metric = self._check_input(inputs, **kwargs)
        show_runtime_breakdown(trials, metric)


ANALYSIS = RuntimeBreakdownVisualizer()
