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
"""ParaProf style horizontal bar chart for an individual profile,
rendered using Plotly"""

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial

import nbformat

import inspect


def show_plotly_profile_bar_plot(trial_id, indices, metric):
    from itertools import islice, cycle
    import six
    import plotly.offline as py
    import plotly.graph_objs as go
    from taucmdr import logger
    from taucmdr.gui.color import ColorMapping

    logger.set_log_level('WARN')

    def build_profile_bar_plot(trial, indices_, metric_):
        profdata = trial.get_profile_data()
        idata = profdata.interval_data()
        s = idata.loc[indices_][[metric_]].sort_values(metric_)
        smax = s[metric_].max()
        data = [
            go.Bar(
                x=s[metric_],
                y=s.index.values,
                orientation='h',
                marker=dict(
                    color=list(islice(cycle(ColorMapping.get_default_palette()), s.shape[0])),
                ),
                text=s.index.values,
                textposition='outside',
            )
        ]
        layout = go.Layout(
            autosize=True,
            height=25 * s.shape[0],
            margin=go.Margin(
                l=0,
                r=0,
                b=0,
                t=10,
            ),
            xaxis=dict(
                range=[-0.1 * smax, smax * 1.25]
            ),
        )
        fig = go.Figure(data=data, layout=layout)
        return fig

    if isinstance(trial_id, six.string_types):
        trial = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")
    bar = build_profile_bar_plot(trial, indices, metric)
    py.iplot(bar)


class PlotlyProfileBarPlotVisualizer(AbstractAnalysis):
    def __init__(self, name='profile-barplot-plotly', description='Profile Bar Plot (Plotly)'):
        super(PlotlyProfileBarPlotVisualizer, self).__init__(name=name, description=description)

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
        return inputs, metric, indices

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric, indices = self._check_input(inputs, **kwargs)
        trial = trials[0]
        all_trial_hashes = [t.hash_digest() for t in Trial.controller(ANALYSIS_STORAGE).all()]
        prof_data = trial.get_profile_data()
        all_indices = prof_data.indices
        all_metrics = prof_data.get_value_types()
        result = [
            {'name': 'trial_id',
             'values': all_trial_hashes,
             'default': trial.hash_digest(),
             'type': 'widgets.Dropdown'},

            {'name': 'indices',
             'values': all_indices,
             'default': indices,
             'type': 'widgets.Dropdown'},

            {'name': 'metric',
             'values': all_metrics,
             'default': metric,
             'type': 'widgets.Dropdown'}
        ]
        return result

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cell containing code which will create a barplot when
         executed for the specific profile in trial in `inputs`.

        Args:
            inputs (:obj:`Trial`): The trial to visualize
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Keyword Args:
            metric (str): The name of the metric to visualize
            indices (tuple of int): The (node, context, thread) combination to visualize

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which show the barplot.

        Raises:
            ConfigurationError: The provided model is not a Trial, or more than one provided
        """
        trials, metric, indices = self._check_input(inputs, **kwargs)
        commands = ['from taucmdr.analysis.analyses.profile_barplot import ProfileBarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import ANALYSIS_STORAGE',
                    inspect.getsource(show_plotly_profile_bar_plot)]
        for trial in trials:
            digest = trial.hash_digest()
            if interactive:
                commands.append(self.get_interaction_code(inputs, 'show_plotly_profile_bar_plot', *args, **kwargs))
            else:
                commands.append('show_plotly_profile_bar_plot(Trial.controller(ANALYSIS_STORAGE).'
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
        trials, metric, indices = self._check_input(inputs)
        for trial in trials:
            show_plotly_profile_bar_plot(trial, indices, metric)


ANALYSIS = PlotlyProfileBarPlotVisualizer()
