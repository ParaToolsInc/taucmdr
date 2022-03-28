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
""" This file is used for creating the data webpage display """

import os
from dash import dash_table
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output
from dash import html
from dash import dcc

from .server import app
from .parser import TauProfileParser

layout = html.Div(
    children = [
        html.Label('Choose Node'),
        html.Div(
            id='dataTable-dropdown-container',
            children=[
                dcc.Dropdown(
                    id='dataTable-selector-dropdown',
                    persistence=True,
                    persistence_type='session',
                    clearable=False
                )
            ]
        ),
        html.Div(
            className='tau-datatable',
            id='dataTable-container',
            children=[]
        )
    ]
)

def parse_profile(project, experiment, trial):
    """ This function is used for parsing the content of a profile """
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tau_data = TauProfileParser.parse(trial_path)
    profile = tau_data.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile

@app.callback(
    Output('dataTable-dropdown-container', 'children'),
    Input('url', 'pathname'),
)
def update_dropdown_component(pathname):
    """ This function is used for updating a dropdown based on the profile """
    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    graph_selector_options = []
    for node, context, thread in profile.unstack().index.values:
        graph_selector_options.append({
            'label': f'Node ({node}, {context}, {thread})',
            'value': f'{node}-{context}-{thread}'
        })

    return dcc.Dropdown(
        id='dataTable-selector-dropdown',
        persistence=True,
        persistence_type='session',
        clearable=False,
        options=graph_selector_options,
        placeholder='Select a node',
    )


@app.callback(
    Output('dataTable-container', 'children'),
    [Input('dataTable-selector-dropdown', 'value'), Input('url', 'pathname')]
)
def change_table(dropdown_value, pathname):
    """ This function is used for updating the table based on the profile """
    if dropdown_value is None:
        raise PreventUpdate

    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    index = tuple([int(i) for i in dropdown_value.split('-')])
    data_df = profile.loc[index]

    table = [
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in data_df.columns],
            data=data_df.to_dict('records'), filter_action='native',sort_action='native',
            style_cell={'overflow': 'hidden','textOverflow':'clip' ,'maxWidth': 50,},
            tooltip_data=[{column: {'value': str(value), 'type': 'markdown'}
                                        for column, value in row.items()}
                                        for row in data_df.to_dict('records')],
            tooltip_duration=None,
            page_action='none',
            style_table={'height': '720px', 'overflowY': 'auto'}
        )
    ]

    return table
