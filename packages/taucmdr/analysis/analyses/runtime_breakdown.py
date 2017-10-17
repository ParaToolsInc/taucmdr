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

from bokeh.models import ColumnDataSource

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.data.tauprofile import TauProfile
from taucmdr.error import ConfigurationError
from taucmdr.gui.color import ColorMapping
from taucmdr.model.trial import Trial

import nbformat

import inspect


def show_runtime_breakdown(trials, metric):
    from taucmdr.gui.interaction import InteractivePlotHandler
    from taucmdr import logger
    from bokeh.plotting import figure
    from bokeh.io import output_notebook

    logger.set_log_level('WARN')
    output_notebook(hide_banner=True)

    def build_runtime_breakdown(trials, metric):
        patch_lists = RuntimeBreakdownVisualizer.trials_to_patch_lists(trials)
        # TODO construct figure from patch lists
        fig = figure(plot_width=80, plot_height=40, output_backend="webgl", toolbar_location="right")
        return fig

    breakdown = build_runtime_breakdown(trials, metric)
    plot = InteractivePlotHandler(breakdown)
    plot.show()


class RuntimeBreakdownVisualizer(AbstractAnalysis):
    def __init__(self, name='runtime-breakdown', description='Runtime Breakdown'):
        super(RuntimeBreakdownVisualizer, self).__init__(name=name, description=description)

    @staticmethod
    def trial_to_column_source(trials, metric):
        pass

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Runtime breakdowns can only be built for plots")
        metric = kwargs.get('metric', 'Exclusive')
        return inputs, metric

    def get_cells(self, inputs, *args, **kwargs):
        """Get Jupyter input cells containing code which will create a stacked area chart
        showing the breakdown of runtime across trials.

        Args:
            inputs (list of :obj:`Trial`): The trials to visualize

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
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(show_runtime_breakdown)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "[%s]" % (",".join(['Trial.controller(PROJECT_STORAGE).search_hash("%s")[0]' %
                                              trial.hash_digest() for trial in trials]))
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
