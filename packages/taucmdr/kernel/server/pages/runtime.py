#
# Copyright (c) 2022, ParaTools, Inc.
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
""" This file is used for displaying the runtime webpage """

import os
from dash import html
from dash import dcc
from dash.dependencies import Input, Output

import pandas as pd
import plotly.graph_objects as go

from .server import app
from .parser import TauProfileParser

colors = [
    '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c', '#98df8a',
    '#ff9896', '#9467bd', '#c5b0d5', '#8c564b', '#c49c94',
    '#f7b6d2', '#7f7f7f', '#c7c7c7', '#bcbd22', '#dbdb8d',
    '#9edae5', '#7fc97f', '#beaed4', '#fdc086', '#ffff99',
    '#f0027f', '#bf5b17', '#666666', '#1b9e77', '#d95f02',
    '#e7298a', '#66a61e', '#e6ab02', '#a6761d', '#666666',
    '#b3cde3', '#ccebc5', '#decbe4', '#fed9a6', '#ffffcc',
    '#fddaec', '#f2f2f2', '#393b79', '#5254a3', '#6b6ecf',
    '#637939', '#8ca252', '#b5cf6b', '#cedb9c', '#8c6d31',
    '#e7ba52', '#e7cb94', '#843c39', '#ad494a', '#d6616b',
    '#7b4173', '#a55194', '#ce6dbd', '#de9ed6', '#8dd3c7',
    '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69',
    '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f', '#3182bd',
    '#9ecae1', '#c6dbef', '#e6550d', '#fd8d3c', '#fdae6b',
    '#31a354', '#74c476', '#a1d99b', '#c7e9c0', '#756bb1',
    '#bcbddc', '#dadaeb', '#636363', '#969696', '#bdbdbd'
]


layout = html.Div(
    children=[
        html.Label('Metric:'),
        dcc.Dropdown(
            id='breakdown-metric-dropdown',
            clearable=False,
            options=[
                {'label':'Exclusive', 'value':'Exclusive'},
                {'label':'Inclusive', 'value':'Inclusive'},
                {'label':'Exclusive per Call', 'value':'Exclusive per Call'},
                {'label':'Inclusive per Call', 'value':'Inclusive per Call'},
                {'label':'Number of Calls', 'value':'Calls'},
                {'label':'Number of Child Calls', 'value':'Subcalls'}
            ],
            value='Exclusive'
        ),
        dcc.Graph(
            id='breakdown-graph',
            config={
                'displayModeBar': False
            }
        )
    ]
)

def parse_profile(project, experiment, trial):
    """ This function is used for parsing profile data """
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tau_data = TauProfileParser.parse(trial_path)
    profile = tau_data.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile


#runtime breakdown page callback
@app.callback(
    Output('breakdown-graph', 'figure'),
    [Input('breakdown-metric-dropdown', 'value'), Input('url', 'pathname')]
)
def display_runtime_breakdown(metric, pathname):
    """
    Creates the runtime breakdown graph (using Plotly's filled area plot) with
    the current metric, selected from the dropdown

    param:
        metric: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        the runtime breakdown figure
    """
    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    metric_data = profile[[metric]].sort_values(metric, ascending=False)
    metric_df = metric_data.unstack().sort_values(
            (0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

    breakdown_top_n = 10
    if len(metric_df.index) > breakdown_top_n:
        metric_df = pd.concat([metric_df[ :breakdown_top_n], metric_df[breakdown_top_n: ]
            .groupby(level=0)
            .sum()
            .rename({metric: 'Other'})], copy=False)

    thread_calc = profile[['Exclusive']].sort_values('Exclusive',ascending=False)
    thread_calc = thread_calc.unstack().sort_values(
            (0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

    total_thread_count = len(thread_calc.columns)

    for i in range(len(metric_df.index)-1):
        for j in range(1, total_thread_count):
            #the values add up on each other as the number of threads/nodes increases
            metric_df.iat[i,j] = metric_df.iat[i, j-1] + metric_df.iat[i,j]

    x_values = [str(i) for i in range(total_thread_count)]

    fig = go.Figure(layout=go.Layout(height=600, width=900))
    for i in range(len(metric_df)):
        ### shortening the strings in legend, not working yet###
        new_string = metric_df.index[i]
        if new_string != 'Other':
            new_string = new_string[1: ]

        # if len(new_string) > 20:
            # subtract = len(metric_df.index[i]) - 20
            # new_string[ :-subtract]

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=metric_df.iloc[i],     #sum(sorted_data.iloc[i][0:i])
                mode='lines',
                line=dict(width=0.5, color=colors[i]),
                stackgroup='one',
                groupnorm='percent', # sets the normalization for the sum of the stackgroup
                name='{}'.format(new_string)
            )
        )

    fig.update_layout(legend=dict(
       # yanchor="top",
        y=-0.35,
       # xanchor="left",
        x=0.1,
        bordercolor="Black",
        borderwidth=1
    ))

    fig.update_layout(
        margin=dict(
            l=20,
            r=10,
            t=10,
            b=10
        )
    )

    return fig
