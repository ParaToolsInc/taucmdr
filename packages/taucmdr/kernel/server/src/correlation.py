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
""" This file is used for creating content for the correlation webpage """

import os
from dash.dependencies import Input, Output
from dash import html
from dash import dcc

import plotly.express as px

from .server import app
from .parser import TauProfileParser

layout = html.Div(
    children=[
        html.Div(
            id='function-dropdowns',
            children=[
                html.Label('Choose First Function'),
                dcc.Dropdown(
                    id='function-selector-dropdown-first',
                    clearable=False,
                    persistence=True,
                    persistence_type='session',
                    options=[

                    ],
                    value=0
                ),
                html.Br(),
                html.Label('Choose Second Function'),
                dcc.Dropdown(
                    id='function-selector-dropdown-second',
                    clearable=False,
                    persistence=True,
                    persistence_type='session',
                    options=[

                    ],
                    value=0
                )
            ]
        ),
        dcc.Graph(
            id='correlation-graph',
            config={
                'displayModeBar': False
            }
        ),
        html.Label('Data Metric:'),
        dcc.Dropdown(
            id='scatter-metric-dropdown',
            clearable=False,
            persistence=True,
            persistence_type='session',
            options=[
                {'label':'Exclusive', 'value':'Exclusive'},
                {'label':'Inclusive', 'value':'Inclusive'},
                {'label':'Exclusive per Call', 'value':'Exclusive per Call'},
                {'label':'Inclusive per Call', 'value':'Inclusive per Call'},
                {'label':'Number of Calls', 'value':'Calls'},
                {'label':'Number of Child Calls', 'value':'Subcalls'}
            ],
            value='Exclusive'
        )
    ]
)

def parse_profile(project, experiment, trial):
    """ This function is used for parsing a profile by path"""
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tau_data = TauProfileParser.parse(trial_path)
    profile = tau_data.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile

@app.callback(
    Output('function-dropdowns', 'children'),
    Input('url', 'pathname')
)
def update_dropdowns(pathname):
    """ This function returns a dropdown based on the profile """
    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    functions = []
    for j in range(0,len(profile.loc[0,0,0].values)-1):
        functions.append({
            'label':'{}'.format(profile.loc[0,0,0]["Timer Name"].iloc[[j]]),
            'value':j
        })

    return [
            html.Label('Choose First Function'),
            dcc.Dropdown(
                id='function-selector-dropdown-first',
                clearable=False,
                persistence=True,
                persistence_type='session',
                options=functions,
                value=0
            ),
            html.Br(),
            html.Label('Choose Second Function'),
            dcc.Dropdown(
                id='function-selector-dropdown-second',
                clearable=False,
                persistence=True,
                persistence_type='session',
                options=functions,
                value=0
            )
    ]


@app.callback(
    Output('correlation-graph', 'figure'),
    [
        Input('function-selector-dropdown-first', 'value'),
        Input('function-selector-dropdown-second', 'value'),
        Input('scatter-metric-dropdown', 'value'),
        Input('url', 'pathname')
    ]
)
def display_scatter_plot(first_func, second_func, scatter_metric, pathname):
    """ This function returns a scatter plot based on the dropdown selection and profile """
    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    scatter_data = profile[[scatter_metric]]
    scatter_df = scatter_data.unstack().sort_values((0, 0, 0), axis=1).transpose().fillna(0)

    fig = px.scatter(
        x=scatter_df.iloc[first_func].values,
        y=scatter_df.iloc[second_func].values,
        trendline='ols',
        trendline_color_override='red',
        labels={
            'x':'{}'.format(profile.loc[0,0,0]['Timer Name'].iloc[[first_func]]),
            'y':'{}'.format(profile.loc[0,0,0]['Timer Name'].iloc[[second_func]])
        }
    )
    return fig
