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

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial

import nbformat

import inspect


def bar_plot(trial):
    # TODO Fix this to use Pandas frames directly instead of building a bunch of separate lists
    data = trial.get_data()
    from taucmdr.gui.color import ColorMapping
    from bokeh.plotting import figure, show
    from bokeh.io import output_notebook
    output_notebook()
    indices = []
    trial = 7
    mapping = ColorMapping()
    for node_num, node_data in data.iteritems():
        for context_num, context_data in node_data.iteritems():
            for thread_num, thread_data in context_data.iteritems():
                indices.append((node_num, context_num, thread_num))
    myfig = figure(plot_width=400, plot_height=400, y_range=map(lambda x: str(x), indices[::-1]),
                   output_backend="webgl")
    ys = []
    heights = []
    lefts = []
    rights = []
    colors = []
    for n, c, t in indices:
        category = [str((n, c, t))]
        last_time = 0
        for name, time in \
                data[n][c][t].interval_data().sort_values('Exclusive', ascending=False).loc[trial, n, c, t][
                    ['Exclusive']].itertuples():
            next_time = last_time + time
            color = mapping[name]
            ys.append(category)
            heights.append(0.5)
            lefts.append(last_time)
            rights.append(next_time)
            colors.append(color)
            last_time = next_time
    # It turns out that calling hbar with lists of elements to add is MUCH faster than repeatedly
    # calling hbar with single elements, which is why we build the lists above instead of just
    # calling hbar inside the loop.
    myfig.hbar(y=ys, height=heights, left=lefts, right=rights, color=colors)
    show(myfig)


class BarPlotVisualizer(AbstractAnalysis):

    def __init__(self):
        super(BarPlotVisualizer, self).__init__('barplot', 'Display a ParaProf-style bar plot')

    @staticmethod
    def check_input(inputs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("Bar plots can only be built for Trials.")
        return inputs

    def get_cells(self, inputs, *args, **kwargs):
        trials = self.check_input(inputs)
        commands = ['from taucmdr.model.trial import Trial', 'from taucmdr.cf.storage.levels import PROJECT_STORAGE',
                    inspect.getsource(bar_plot)]
        for trial in trials:
            digest = trial.hash_digest()
            commands.append('bar_plot(Trial.controller(PROJECT_STORAGE).search_hash("%s")[0])' % digest)
        cell_source = "\n".join(commands)
        return [nbformat.v4.new_code_cell(cell_source)]

    def run(self, inputs, *args, **kwargs):
        trials = self.check_input(inputs)
        for trial in trials:
            bar_plot(trial)
