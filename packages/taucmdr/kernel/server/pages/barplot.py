import os
from .server import app
from .parser import TauProfileParser

import dash
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
from itertools import islice, cycle

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

layout = html.Div(children=[
        html.Label('Choose Graph'),
        html.Div(
            id='bar-dropdown-container', 
            children=[
                dcc.Dropdown(
                    id='bar-graph-selector-dropdown', 
                    persistence=True, 
                    persistence_type='session',
                    clearable=False,
                )
            ]
        ),
        dcc.Graph(
            id='graph-1',
            config={
                'displayModeBar': False
            }
        ),
        html.Label('Options'),
        dbc.Row([
            dbc.Col(
                children=dcc.Checklist(
                    id='checklist-1', 
                    options=[
                        {'label': 'Descending', 'value': '0'}
                    ], 
                    value=['0']
                )
            ),
            dbc.Col(
                children=[
                    html.Label('Metric:'),
                    dcc.Dropdown(
                        id='select-metric',
                        persistence=True,
                        persistence_type='session',
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
                    )
                ]
            ),
            dbc.Col(
                children=[
                    html.Label('Sort By:'),
                    dcc.Dropdown(
                        id='sort-by',
                        persistence=True,
                        persistence_type='session',
                        clearable=False,
                        options=[],
                        value='Same'
                    )
                ]
            ),
            dbc.Col(
                children=[
                    html.Label('Units:'),
                    dcc.Dropdown(
                        id='select-units',
                        persistence=True,
                        persistence_type='session',
                        clearable=False,
                        options=[
                            {'label': 'Seconds', 'value': 'Seconds'},
                            {'label': 'Milliseconds', 'value': 'Milliseconds'},
                            {'label': 'Microseconds', 'value': 'Microseconds'}
                        ],
                        value='Milliseconds'
                    )
                ]
            )
        ]),
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

# Callback: Update dropdown component on URL change
@app.callback(
    Output('bar-dropdown-container', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def update_dropdown_component(pathname, pathsearch):
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    graph_selector_options = [
        {'label': 'Std. Dev.', 'value': 'stddev'},
        {'label': 'Mean', 'value': 'mean'},
        {'label': 'Max', 'value': 'max'},
        {'label': 'Min', 'value': 'min'}
    ]
    for node, context, thread in profile.unstack().index.values:
        graph_selector_options.append({'label': f'Node ({node}, {context}, {thread})', 'value': f'{node}-{context}-{thread}'})

    if pathsearch:
        value = pathsearch.split('?index=')[1]
    else:
        value = 'stddev'
    
    return dcc.Dropdown(
        id='bar-graph-selector-dropdown', 
        persistence=True, 
        persistence_type='session',
        clearable=False,
        options=graph_selector_options,
        value=value
    )

@app.callback(
    [Output('sort-by','options'), Output('sort-by', 'value')],
    Input('bar-graph-selector-dropdown', 'value')
)
def update_sort_by_options(dropdown_value):
    if dropdown_value in {'stddev', 'mean', 'max', 'min'}:
        return [{'label': 'Same as Visible Metric', 'value': 'Same'}], 'Same'
    else:
        return [
            {'label': 'Same as Visible Metric', 'value': 'Same'},
            {'label': 'Name', 'value': 'Timer Name'}, 
            {'label': 'Exclusive', 'value': 'Exclusive'},
            {'label': 'Inclusive', 'value': 'Inclusive'},
            {'label': 'Exclusive per Call', 'value': 'Exclusive per Call'},
            {'label': 'Inclusive per Call', 'value': 'Inclusive per Call'},
            {'label': 'Number of Calls', 'value': 'Calls'},
            {'label': 'Number of Child Calls', 'value': 'Subcalls'}
        ], 'Same'


@app.callback(
    Output('graph-1', 'figure'),#, Output('metadata', 'children')],
    [
        Input('bar-graph-selector-dropdown', 'value'), 
        Input('checklist-1', 'value'), 
        Input('select-metric', 'value'), 
        Input('sort-by', 'value'),
        Input('select-units', 'value'),
        Input('url', 'pathname')
    ], prevent_initial_call=True
)
def display_bar_plot(node, checklist, metric, sort, unit, pathname):
    if node == None:
        raise PreventUpdate

    if sort == 'Same':
        sort = metric

    divisor = {
        'Seconds': 1000000,
        'Milliseconds': 1000,
        'Microseconds': 1
    }[unit]

    fig = make_subplots(specs=[
        [{'secondary_y': True}]
    ])

    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)
    if node in {'stddev', 'mean', 'max', 'min'}:
        metric_data = profile[[metric]]
        metric_df = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

        TOTAL_THREAD_COUNT = len(metric_df.columns)
        metric_df['Std. Dev.'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].std(axis=1)
        metric_df['Mean'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].mean(axis=1)
        metric_df['Max'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].max(axis=1)
        metric_df['Min'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].min(axis=1)

        index = {
           'stddev': 'Std. Dev.', 
           'mean': 'Mean', 
           'max': 'Max', 
           'min': 'Min'
        }[node] 
        
        metric_df = metric_df.sort_values(index, ascending=False)

        TOP_N = 15
        if len(metric_df.index) > TOP_N:
            metric_df = pd.concat([metric_df[ :TOP_N], metric_df[TOP_N: ].groupby(level=0).sum().rename({metric: 'Other'})], copy=False)

        df_indices = []
        for index_name in metric_df.index.values:
            if index_name == 'Other':
                df_indices.append(index_name)

            else:
                new_index_name = ''.join(index_name)
                new_index_name = new_index_name[len(metric):]
                df_indices.append(new_index_name)

        thread_calc = profile[['Exclusive']].sort_values('Exclusive', ascending=False)
        thread_calc = thread_calc.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
        smax = metric_df[index].max()

        fig.add_trace(
            go.Bar(
                x=metric_df[index]/divisor,
                y=df_indices,
                orientation='h',
                marker=dict(
                    color=list(islice(cycle(colors), thread_calc.shape[0]))
                ),
                text=round(metric_df[index] / divisor, 3),
                textposition='auto',
                cliponaxis=False
            ), 
            secondary_y=True
        )

    else:
        index = tuple([int(i) for i in node.split('-')])
        metric_data = profile.loc[index].sort_values(sort, ascending=False)

        TOP_N = 15
        metric_df = pd.concat([metric_data[ :TOP_N], metric_data[TOP_N: ].groupby(level=0).sum().rename({metric: 'Other'})], copy=False)
        if len(metric_df.index) > TOP_N:
            metric_df = metric_df.iloc[ :TOP_N, :]
        
        smax = metric_df[metric].max()

        fig.add_trace(
            go.Bar(
                x=metric_df[metric]/divisor,
                y=metric_df.index.values,
                orientation='h',
                marker=dict(
                    color=list(islice(cycle(colors), metric_df.shape[0]))
                ),
                text=round(metric_df[metric] / divisor, 3),
                textposition='auto'
            ),
            secondary_y=True
        )
   
    fig.update_layout(
        margin=dict(
            l=20,
            r=10,
            t=10,
            b=10
        )
    )

    fig.update_xaxes(range=[-0.01 * smax / divisor, 1.1 * smax / divisor])
#    fig.update_xaxes(autorange='reversed')
    fig.update_yaxes(autorange='reversed')

    if '0' in checklist:
        fig.update_yaxes(autorange='reversed')
    else:
        fig.update_yaxes(autorange=True)

    return fig
