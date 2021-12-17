import os
from .server import app
from .parser import TauProfileParser

import dash
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

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
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tauData = TauProfileParser.parse(trial_path)
    profile = tauData.interval_data()
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
    Creates the runtime breakdown graph (using Plotly's filled area plot) with the current metric, slected from the dropdown
    param:
        metric: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        the runtime breakdown figure
    """
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    metric_data = profile[[metric]].sort_values(metric, ascending=False)
    metric_df = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

    BREAKDOWN_TOP_N = 10
    if len(metric_df.index) > BREAKDOWN_TOP_N:
        metric_df = pd.concat([metric_df[ :BREAKDOWN_TOP_N], metric_df[BREAKDOWN_TOP_N: ].groupby(level=0).sum().rename({metric: 'Other'})], copy=False)

    thread_calc = profile[['Exclusive']].sort_values('Exclusive',ascending=False)
    thread_calc = thread_calc.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
    TOTAL_THREAD_COUNT = len(thread_calc.columns)
    
    for i in range(len(metric_df.index)-1):
        for j in range(1, TOTAL_THREAD_COUNT):
            #the values add up on each other as the number of threads/nodes increases 
            metric_df.iat[i,j] = metric_df.iat[i, j-1] + metric_df.iat[i,j]

    x = [str(i) for i in range(TOTAL_THREAD_COUNT)]
    
    fig = go.Figure(layout=go.Layout(height=600, width=900))
    for i in range(len(metric_df)):
        ### shortening the strings in legend, not working yet###
        newString = metric_df.index[i]
        if newString != 'Other':
            newString = newString[1: ]

        if len(newString) > 20:
            subtract = len(metric_df.index[i]) - 20
            newString[ :-subtract]
                
        fig.add_trace(
            go.Scatter(
                x=x, 
                y=metric_df.iloc[i],     #sum(sorted_data.iloc[i][0:i])
                mode='lines',
                line=dict(width=0.5, color=colors[i]),
                stackgroup='one',
                groupnorm='percent', # sets the normalization for the sum of the stackgroup
                name='{}'.format(newString)
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
