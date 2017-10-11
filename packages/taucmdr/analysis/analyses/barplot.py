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

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial

import nbformat

import inspect


def show_bar_plot(trial, metric):
    from taucmdr.data.tauprofile import TauProfile
    from taucmdr.gui.interaction import InteractivePlotHandler
    from taucmdr import logger
    from bokeh.plotting import figure
    from bokeh.models.glyphs import HBar
    from bokeh.io import output_notebook

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)

    def build_bar_plot(trial):
        data_source = BarPlotVisualizer.trial_to_column_source(trial, metric)
        indices = map(lambda x: str(x), TauProfile.indices(trial.get_data())[::-1])
        glyph = HBar(y="y", height="height", left="left", right="right", line_color="color", fill_color="color")
        fig = figure(plot_width=400, plot_height=400, y_range=indices, output_backend="webgl")
        fig.add_glyph(data_source, glyph)
        return fig

    bar = build_bar_plot(trial)
    plot = InteractivePlotHandler(bar, tooltips=[("Timer", "@label"), (metric, "@value")])
    plot.show()


class BarPlotVisualizer(AbstractAnalysis):
    def __init__(self):
        super(BarPlotVisualizer, self).__init__('barplot', 'Display a ParaProf-style bar plot')

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
        for n, c, t in indices:
            category = [str((n, c, t))]
            last_time = 0
            for name, time in \
                    data[n][c][t].interval_data().sort_values(metric, ascending=False).loc[
                        trial['number'], n, c, t][
                        [metric]].itertuples():
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
        # It turns out that calling hbar with lists of elements to add is MUCH faster than repeatedly
        # calling hbar with single elements, which is why we build the lists above instead of just
        # calling hbar inside the loop.
        data_source = ColumnDataSource(dict(y=ys, height=heights, left=lefts, right=rights,
                                            color=colors, label=labels, value=values))
        return data_source

    @staticmethod
    def _check_input(inputs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Bar plots can only be built for Trials.")
        return inputs

    def get_cells(self, inputs, *args, **kwargs):
        """Get Jupyter input cell containing code which will create a barplot when
         executed for the trials in `inputs`.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the barplot.

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        metric = kwargs.get('metric', 'Exclusive')
        trials = self._check_input(inputs)
        commands = ['from taucmdr.analysis.analyses.barplot import BarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(show_bar_plot)]
        for trial in trials:
            digest = trial.hash_digest()
            commands.append('show_bar_plot(Trial.controller(PROJECT_STORAGE).search_hash("%s")[0], "%s")'
                            % (digest, metric))
        cell_source = "\n".join(commands)
        return [nbformat.v4.new_code_cell(cell_source)]

    def run(self, inputs, *args, **kwargs):
        """Create a barplot as direct notebook output for the trials in `inputs`.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize

        Raises:
            ConfigurationError: The provided models are not Trials
        """
        metric = kwargs.get('metric', 'Exclusive')
        trials = self._check_input(inputs)
        for trial in trials:
            show_bar_plot(trial, metric)
