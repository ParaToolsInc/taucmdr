import os
from .server import app
from .parser import TauProfileParser

import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

import plotly.express as px

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
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tauData = TauProfileParser.parse(trial_path)
    profile = tauData.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile


@app.callback(
    Output('function-dropdowns', 'children'),
    Input('url', 'pathname')
)
def update_dropdowns(pathname):
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)


    functions = [] 
    for j in range(0,len(profile.loc[0,0,0].values)-1):
        functions.append({'label':'{}'.format(profile.loc[0,0,0]["Timer Name"].iloc[[j]]), 'value':j})

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
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
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

