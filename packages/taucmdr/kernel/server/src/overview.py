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
""" This file is used for creating a webpage that gives an overview of the profiles. """

import os
import re
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from dash import html
from dash import dcc

import pandas as pd
import plotly.graph_objects as go

from .server import app
from .parser import TauProfileParser

layout = html.Div(
    className='tau-overview',
    children=[
        html.Label('Data Metric:'),
        dcc.Dropdown(options=[
            {'label': 'Exclusive', 'value': 'Exclusive'},
            {'label': 'Inclusive', 'value': 'Inclusive'},
            {'label': 'Exclusive per Call', 'value': 'Exclusive per Call'},
            {'label': 'Inclusive per Call', 'value': 'Inclusive per Call'},
            {'label': 'Number of Calls', 'value': 'Calls'},
            {'label': 'Number of Child Calls', 'value': 'Subcalls'}
        ], value='Exclusive', id='overview-dm-dropdown', clearable=False),
        dcc.Graph(
            id='overview',
            config={
                'displayModeBar': False,
                'responsive': True
            },
            style={
                'height': '100%'
            }
        )]
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

# Callback: Update overview figure when URL changes
@app.callback(
    Output('overview', 'figure'),
    Input('overview-dm-dropdown', 'value'),
    State('url', 'pathname')
)
def make_overview(dropdown_value, pathname):
    """ This function is used for generating a graph based on the profile chosen """
    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    metric_data = profile[[dropdown_value]].sort_values(dropdown_value, ascending=False)
    metric_df = metric_data.unstack().sort_values(
            (0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

    top_n = 15
    if len(metric_df.index) > top_n:
        metric_df = pd.concat([metric_df[ :top_n], metric_df[top_n: ]
            .groupby(level=0)
            .sum()
            .rename({dropdown_value: 'Other'})], copy=False)

    indices = ['Std. Dev.', 'Mean', 'Max', 'Min']
    for node, context, thread in metric_df.columns.values:
        indices.append(f'node {node}, thread {thread}')

    total_thread_count = len(metric_df.columns)
    metric_df['Std. Dev.'] = metric_df.iloc[:, 0:total_thread_count].std(axis=1)
    metric_df['Mean'] = metric_df.iloc[:, 0:total_thread_count].mean(axis=1)
    metric_df['Max'] = metric_df.iloc[:, 0:total_thread_count].max(axis=1)
    metric_df['Min'] = metric_df.iloc[:, 0:total_thread_count].min(axis=1)

    columns = list(metric_df.columns.values)
    metric_df = metric_df[
            columns[total_thread_count:total_thread_count+4] + columns[0:total_thread_count]]

    index_count = len(indices)
    data = []
    for idx, row in metric_df.iterrows():
        text=['<br>'.join([idx[1][i:i + 75] for i in range(0, len(idx[1]), 75)])] * index_count
        dash_bar = go.Bar(
            x=row.values[::-1],
            y=indices[::-1],
            orientation='h',
            hoverinfo='text',
            text=text
        )
        data.append(dash_bar)

    data[-1]['marker'] = {'color': '#000000'}
    data[-1]['text'] = 'Other'

    layout = go.Layout(
        barmode='stack',
        showlegend=False,
        hovermode='closest',
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),
    )

    fig = go.Figure(data=data, layout=layout)
#    fig.update_layout(width=800, height=700)

    return fig

# Callback: Update URL when a node is clicked
@app.callback(
    [Output('url', 'pathname'), Output('url', 'search')],
    Input('overview', 'click_data'),
    State('url', 'pathname')
)
def display_click_data(click_data, pathname):
    """ This function is used for interacting with the overview graph """
    if click_data is None:
        raise PreventUpdate

    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    if click_data['points'][0]['y'] == 'Std. Dev.':
        index = 'stddev'
    elif click_data['points'][0]['y'] == 'Mean':
        index = 'mean'
    elif click_data['points'][0]['y'] == 'Max':
        index = 'max'
    elif click_data['points'][0]['y'] == 'Min':
        index = 'min'
    else:
        index = '-'.join(re.findall(r'\b\d+\b', click_data['points'][0]['y']))
    return f'/{project}/{experiment}/{trial}/bar-plot', f'?index={index}'
