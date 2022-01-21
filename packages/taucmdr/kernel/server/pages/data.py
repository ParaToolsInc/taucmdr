import os
from .server import app
from .parser import TauProfileParser

import dash
from dash import dash_table
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

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
            id='dataTable-container',
            children=[]
        )
    ]
)

def parse_profile(project, experiment, trial):
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tauData = TauProfileParser.parse(trial_path)
    profile = tauData.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile


@app.callback(
    Output('dataTable-dropdown-container', 'children'),
    Input('url', 'pathname'),
)
def update_dropdown_component(pathname):
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    graph_selector_options = []
    for node, context, thread in profile.unstack().index.values:
        graph_selector_options.append({'label': f'Node ({node}, {context}, {thread})', 'value': f'{node}-{context}-{thread}'})

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
def changeTable(dropdown_value, pathname):
    if dropdown_value == None:
        raise PreventUpdate

    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    index = tuple([int(i) for i in dropdown_value.split('-')])
    data_df = profile.loc[index]

    table = [
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in data_df.columns],
            data=data_df.to_dict('records'), filter_action='native',sort_action='native',
            style_cell={'overflow': 'hidden','textOverflow':'clip' ,'maxWidth': 50,},
            tooltip_data=[{column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()} for row in data_df.to_dict('records')],
            tooltip_duration=None,
            page_action='none',
            style_table={'height': '720px', 'overflowY': 'auto'}
        )
    ]

    return table
