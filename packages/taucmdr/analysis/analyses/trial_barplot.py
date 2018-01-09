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
"""ParaProf style horizontal bar chart"""

from bokeh.models import ColumnDataSource

import six
from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial

import nbformat
import faststat

from collections import defaultdict
import inspect
from math import sqrt


def run_trial_bar_plot(trial_id, metric):
    from taucmdr.data.tauprofile import TauProfile
    from bokeh.models.callbacks import CustomJS
    from bokeh.models.glyphs import HBar
    from bokeh.models.ranges import DataRange1d
    from bokeh.plotting import figure

    def build_bar_plot(_trial, _metric):
        data_source, summary = TrialBarPlotVisualizer.trial_to_column_source(_trial, _metric)
        indices = []
        indices.extend(map(lambda x: str(x), TauProfile.indices(_trial.get_data())[::-1]))
        indices.extend(['Min', 'Max', 'Mean', 'Std. Dev.'])
        glyph = HBar(y="y", height="height", left="left", right="right", line_color="color", fill_color="color")
        fig = figure(plot_width=80, plot_height=40, x_range = DataRange1d(), y_range=indices, output_backend="webgl")
        fig.add_glyph(data_source, glyph)
        callback = CustomJS(args=dict(y_range=fig.y_range),
                            code=TrialBarPlotVisualizer.get_callback_code(_trial.hash_digest()))

        fig.js_on_event('tap', callback)
        return fig, summary

    if isinstance(trial_id, str):
        trial = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")
    return build_bar_plot(trial, metric)


def show_trial_bar_plot(trial_id, metric):
    from taucmdr import logger
    from taucmdr.gui.interaction import InteractivePlotHandler
    from bokeh.io import output_notebook

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)
    fig, _ = run_trial_bar_plot(trial_id, metric)
    plot = InteractivePlotHandler(fig, tooltips=[("Timer", "@label"), (metric, "@value")])
    plot.show()


class TrialBarPlotVisualizer(AbstractAnalysis):
    def __init__(self, name='trial-barplot', description='Trial Bar Plot'):
        super(TrialBarPlotVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def get_callback_code(digest):
        return """
        let mapping = y_range._mapping;
        let selected = null;
        if(cb_obj.sx < 60) {
            for(var key in mapping) {
                if(mapping.hasOwnProperty(key)) {
                    let mapsTo = mapping[key];
                    if(mapsTo.hasOwnProperty("value")) {
                        let value = mapsTo["value"];
                        if(Math.abs(value - cb_obj.y) < 0.2) {
                            selected = key;
                            break;
                        }
                    }
                }
            }
        }
        if(selected != null) {
            let trial_hash = "%s";
            window.defaultExperimentPane.run_analysis_on_trials_with_args("profile-barplot", [trial_hash], "indices=" + key);
        }
        """ % digest

    @staticmethod
    def trial_to_column_source(trial, metric):
        """Convert trial data as returned by Trial.get_data to a Bokeh ColumnDataSource
        formatted for producing a bar chart through bokeh.plotting.hbar.

        Args:
            trial (Trial): Trial from which to produce a chart
            metric (str): The name of the metric to display

        Returns:
            bokeh.models.ColumnDataSource: Transformed data suitable for horizontal bar charts
        """
        data = trial.get_data()
        mapping = ColorMapping()
        indices = TauProfile.indices(data)
        ys = []
        heights = []
        lefts = []
        rights = []
        colors = []
        labels = []
        values = []
        stats = defaultdict(faststat.Stats)
        for n, c, t in indices:
            category = [str((n, c, t))]
            last_time = 0
            for name, time in \
                    data[n][c][t].interval_data().sort_values(metric, ascending=False).loc[
                        trial['number'], n, c, t][
                        [metric]].itertuples():
                time = time / 1e6
                values.append(time)
                next_time = last_time + time
                color = mapping[name]
                labels.append(name)
                ys.append(category)
                heights.append(0.5)
                lefts.append(last_time)
                rights.append(next_time)
                colors.append(color)
                last_time = next_time
                stats[name].add(time)
        summary = defaultdict(dict)
        extras = [('Max', lambda s: s.max), ('Min', lambda s: s.min), ('Mean', lambda s: s.mean),
                  ('Std. Dev.', lambda s: sqrt(s.variance))]
        for extra, func in extras:
            last_time = 0
            category = [extra]
            for name, stat in sorted(six.iteritems(stats), key=lambda (k, v): (func(v), k), reverse=True):
                time = func(stat)
                values.append(time)
                next_time = last_time + time
                color = mapping[name]
                labels.append(name)
                ys.append(category)
                heights.append(0.5)
                lefts.append(last_time)
                rights.append(next_time)
                colors.append(color)
                last_time = next_time
                summary[extra][name] = time

        # It turns out that calling hbar with lists of elements to add is MUCH faster than repeatedly
        # calling hbar with single elements, which is why we build the lists above instead of just
        # calling hbar inside the loop.
        data_source = ColumnDataSource(dict(y=ys, height=heights, left=lefts, right=rights,
                                            color=colors, label=labels, value=values))
        return data_source, summary

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
        all_trial_hashes = [trial.hash_digest() for trial in Trial.controller(ANALYSIS_STORAGE).all()]
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
        commands = ['from taucmdr.analysis.analyses.trial_barplot import TrialBarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                    inspect.getsource(run_trial_bar_plot),
                    inspect.getsource(show_trial_bar_plot)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        for trial in trials:
            if interactive:
                notebook_cells.append(nbformat.v4.new_code_cell(
                    self.get_interaction_code(inputs, 'show_trial_bar_plot', **kwargs)))
            else:
                digest = trial.hash_digest()
                notebook_cells.append(nbformat.v4.new_code_cell(
                    'show_trial_bar_plot(Trial.controller(ANALYSIS_STORAGE).search_hash("%s")[0], "%s")'
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
        return [run_trial_bar_plot(trial, metric) for trial in trials]


ANALYSIS = TrialBarPlotVisualizer()
