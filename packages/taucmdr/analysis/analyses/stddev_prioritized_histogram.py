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
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial

import nbformat
import faststat

from collections import defaultdict
import inspect
from math import sqrt
from operator import itemgetter


def run_stddev_prioritized_analysis(trial_id, metric, top_n):
    from taucmdr.analysis.analyses.trial_barplot import ANALYSIS as trial_barplot_analysis
    from taucmdr.analysis.analyses.function_histogram import ANALYSIS as histogram_analysis
    from itertools import islice
    from operator import itemgetter
    import six

    if isinstance(trial_id, str):
        trial = Trial.controller(PROJECT_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")
    figures = []
    trial_summaries = [result[1] for result in trial_barplot_analysis.run(trial, metric=metric)]
    for trial_summary in trial_summaries:
        stddevs = trial_summary['Std. Dev.']
        sorted_stddevs = sorted(six.iteritems(stddevs), key=itemgetter(1), reverse=True)
        for timer, stddev in islice(sorted_stddevs, top_n):
            hist_result = histogram_analysis.run(trial, metric=metric, timer=timer)
            figures.append(hist_result['fig'])
    return figures


def show_stddev_prioritized_analysis(trial_id, metric, top_n):
    from taucmdr import logger
    from taucmdr.gui.interaction import InteractivePlotHandler
    from bokeh.io import output_notebook

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)
    figs = run_stddev_prioritized_analysis(trial_id, metric, top_n)
    plot = InteractivePlotHandler(figs, tooltips=[("Timer", "@label"), (metric, "@value")])
    plot.show()


class StdDevPrioritizedAnalysis(AbstractAnalysis):
    def __init__(self, name='stddev-priority', description='Standard Deviation Prioritized Analysis'):
        super(StdDevPrioritizedAnalysis, self).__init__(name=name, description=description)

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        if not inputs:
            raise ConfigurationError("Prioritized analysis requires that at least one Trial be selected.");
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Prioritized analysis can only be built for Trials.")
        metric = kwargs.get('metric', 'Exclusive')
        top_n = kwargs.get('top_n', 2)
        return inputs, metric, top_n

    def get_input_spec(self, inputs, *args, **kwargs):
        """Get the input specification for the analysis.

        Returns:
            list of dict: {name, default, values, type}
        """
        trials, metric, top_n = self._check_input(inputs, **kwargs)
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
             'type': 'widgets.Dropdown'},

            {'name': 'top_n',
             'values': range(1,11),
             'default': top_n,
             'type': 'widgets.BoundedIntText'}
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
        trials, metric, top_n = self._check_input(inputs, **kwargs)
        notebook_cells = []
        commands = ['from taucmdr.analysis.analyses.trial_barplot import TrialBarPlotVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(run_stddev_prioritized_analysis),
                    inspect.getsource(show_stddev_prioritized_analysis)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        for trial in trials:
            if interactive:
                notebook_cells.append(nbformat.v4.new_code_cell(
                    self.get_interaction_code(inputs, 'show_stddev_prioritized_analysis', **kwargs)))
            else:
                digest = trial.hash_digest()
                notebook_cells.append(nbformat.v4.new_code_cell(
                    'show_stddev_prioritized_analysis(Trial.controller(PROJECT_STORAGE).search_hash("%s")[0], "%s", %s)'
                    % (digest, metric, top_n)))
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
        trials, metric, top_n = self._check_input(inputs, **kwargs)
        return [run_stddev_prioritized_analysis(trial, metric, ) for trial in trials]


ANALYSIS = StdDevPrioritizedAnalysis()
