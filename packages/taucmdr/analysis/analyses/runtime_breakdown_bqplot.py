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
"""PerfExplorer-style runtime breakdown chart implemented in bqplot"""

import inspect

import nbformat

from taucmdr.analysis.analyses.runtime_breakdown import RuntimeBreakdownVisualizer


def show_bqplot_runtime_breakdown(trials, metric):
    from bqplot import LinearScale, Lines, Figure, Axis

    def build_runtime_breakdown(trials, metric):
        sc_x = LinearScale()
        sc_y = LinearScale()
        ax_x = Axis(label='Number of Processors', scale=sc_x)
        ax_y = Axis(label='Percentage of Total Runtime', scale=sc_y, orientation='vertical')
        patch_lists = BqplotRuntimeBreakdownVisualizer.trials_to_patch_lists(trials, metric)
        patches = Lines(x=patch_lists.data['x'], y=patch_lists.data['y'], fill='inside',
                        colors=patch_lists.data['color'], fill_colors=patch_lists.data['color'],
                        close_path=True, scales={'x': sc_x, 'y': sc_y})
        fig = Figure(marks=[patches], axes=[ax_x, ax_y], title=trials[0].populate('experiment')['name'])
        return fig

    breakdown = build_runtime_breakdown(trials, metric)
    return breakdown


class BqplotRuntimeBreakdownVisualizer(RuntimeBreakdownVisualizer):
    def __init__(self, name='bqplot-runtime-breakdown', description='Runtime Breakdown (bqplot)'):
        super(RuntimeBreakdownVisualizer, self).__init__(name=name, description=description)

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
        commands = ['from taucmdr.analysis.analyses.runtime_breakdown_bqplot import BqplotRuntimeBreakdownVisualizer',
                    'from taucmdr.model.trial import Trial',
                    'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(show_bqplot_runtime_breakdown)]
        def_cell_source = "\n".join(commands)
        notebook_cells.append(nbformat.v4.new_code_cell(def_cell_source))
        trials_list_str = "Trial.controller(PROJECT_STORAGE).search_hash([%s])" % (",".join(
            ['"%s"' % trial.hash_digest() for trial in trials]))
        show_plot_str = 'show_bqplot_runtime_breakdown(%s, "%s")' % (trials_list_str, metric)
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
        show_bqplot_runtime_breakdown(trials, metric)


ANALYSIS = BqplotRuntimeBreakdownVisualizer()
