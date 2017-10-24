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
"""ParaProf style horizontal bar chart for an individual profile"""

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial

from bokeh.models import ColumnDataSource
import nbformat
from ipywidgets import interact
import ipywidgets as widgets

import inspect


def show_profile_bar_plot(trial, indices, metric):
    from taucmdr.gui.interaction import InteractivePlotHandler
    from taucmdr import logger
    from bokeh.plotting import figure
    from bokeh.models.glyphs import HBar
    from bokeh.io import output_notebook
    from bokeh.models import LabelSet

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)

    def build_profile_bar_plot(trial, indices, metric):
        data_source = ProfileBarPlotVisualizer.profile_to_column_source(trial, indices, metric)
        glyph = HBar(y="y", height="height", left="left", right="right", line_color="color", fill_color="color")
        max_time = data_source.data['left'][-1]
        fig = figure(plot_width=80, plot_height=40, x_range=(1.5 * max_time, -4 * max_time), output_backend="webgl",
                     toolbar_location="left", title=str(indices))
        fig.add_glyph(data_source, glyph)
        fig.left.remove(fig.yaxis[0])
        fig.below.remove(fig.xaxis[0])
        name_labels = LabelSet(x='right', y='y', text='name', level='glyph', y_offset=-10, x_offset=5,
                               text_align='left', source=data_source, render_mode='canvas')
        time_labels = LabelSet(x='left', y='y', text='value', level='glyph', y_offset=-10, x_offset=-5,
                               text_align='right', source=data_source, render_mode='canvas')
        fig.add_layout(name_labels)
        fig.add_layout(time_labels)
        return fig

    bar = build_profile_bar_plot(trial, indices, metric)
    plot = InteractivePlotHandler(bar)
    plot.show()


def interaction_handler(trial, index, metric):
    show_profile_bar_plot(trial, index, metric)


class ProfileBarPlotVisualizer(AbstractAnalysis):
    def __init__(self, name='profile-barplot', description='Profile Bar Plot'):
        super(ProfileBarPlotVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def profile_to_column_source(trial, indices, metric):
        data = trial.get_data()
        node, context, thread = indices
        profile_data = data[node][context][thread].interval_data().loc[trial['number'], node, context, thread][
            [metric]].sort_values(metric)
        mapping = ColorMapping()
        ys = []
        heights = []
        lefts = []
        rights = []
        colors = []
        names = []
        values = []
        for index, (name, time) in enumerate(profile_data.itertuples()):
            ys.append(index)
            heights.append(0.9)
            lefts.append((-time) / 1e6)
            rights.append(0)
            colors.append(mapping[name])
            names.append(name)
            values.append("{0:.3G}".format(time / 1e6))
        data_source = ColumnDataSource(
            dict(y=ys, height=heights, left=lefts, right=rights, color=colors, name=names, value=values))
        return data_source

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        if not inputs:
            raise ConfigurationError("Profile bar plot requires that one trial be selected")
        if len(inputs) > 1:
            raise ConfigurationError("Profile bar plot can only be produced for one trial")
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Bar plots can only be built for Trials.")
        metric = kwargs.get('metric', 'Exclusive')
        indices = kwargs.get('indices', (0, 0, 0))
        interactive = kwargs.get('interactive', True)
        return inputs, metric, indices, interactive

    def get_cells(self, inputs, *args, **kwargs):
        """Get Jupyter input cell containing code which will create a barplot when
         executed for the specific profile in trial in `inputs`.

        Args:
            inputs (:obj:`Trial`): The trial to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize
            indices (tuple of int): The (node, context, thread) combination to visualize

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the barplot.

        Raises:
            ConfigurationError: The provided model is not a Trial, or more than one provided
        """
        trials, metric, indices, interactive = self._check_input(inputs, **kwargs)
        commands = ['from taucmdr.analysis.analyses.profile_barplot import ProfileBarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(show_profile_bar_plot)]
        if interactive:
            commands.extend(['from ipywidgets import interact',
                             'import ipywidgets as widgets',
                             'from taucmdr.data.tauprofile import TauProfile',
                             inspect.getsource(interaction_handler)])
        for trial in trials:
            digest = trial.hash_digest()
            if interactive:
                commands.append('trial = Trial.controller(PROJECT_STORAGE).search_hash("%s")[0]' % digest)
                commands.append('indices = TauProfile.indices(trial.get_data())')
                commands.append('default_index = %s' % str(indices))
                commands.append('metric = "%s"' % metric)
                commands.append('interact(interaction_handler, '
                                'trial=widgets.Dropdown(options=[trial], value=trial, disabled=True), '
                                'index=widgets.Dropdown(options=indices, value=default_index), '
                                'metric=widgets.Dropdown(options=[metric], value=metric, disabled=True))')
            else:
                commands.append('show_profile_bar_plot(Trial.controller(PROJECT_STORAGE).'
                                'search_hash("%s")[0], %s, "%s")'
                                % (digest, indices, metric))
        cell_source = "\n".join(commands)
        return [nbformat.v4.new_code_cell(cell_source)]

    def run(self, inputs, *args, **kwargs):
        """Create a barplot as direct notebook output for the specific profile in trial in `inputs`.

        Args:
            inputs (:obj:`Trial`): The trial to visualize

        Keyword Args:
            metric (str): The name of the metric to visualize
            indices (tuple of int): The (node, context, thread) combination to visualize

        Raises:
            ConfigurationError: The provided model is not a Trial, or more than one provided
        """
        trials, metric, indices, interactive = self._check_input(inputs)
        for trial in trials:
            if interactive:
                interact(interaction_handler,
                         trial=widgets.Dropdown(options=[trial], value=trial, disabled=True),
                         index=widgets.Dropbown(options=[TauProfile.indices(trial)], value=indices),
                         metric=widgets.Dropdown(options=[metric], value=metric))
            else:
                show_profile_bar_plot(trial, metric)


ANALYSIS = ProfileBarPlotVisualizer()
