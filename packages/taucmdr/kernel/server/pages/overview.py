import os
import re
from .server import app
from .parser import TauProfileParser

import dash
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.graph_objects as go

layout = html.Div([
    html.Label('Data Metric:'),
    dcc.Dropdown(options = [
        {'label':'Exclusive', 'value':'Exclusive'},
        {'label':'Inclusive', 'value':'Inclusive'},
        {'label':'Exclusive per Call', 'value':'Exclusive per Call'},
        {'label':'Inclusive per Call', 'value':'Inclusive per Call'},
        {'label':'Number of Calls', 'value':'Calls'},
        {'label':'Number of Child Calls', 'value':'Subcalls'}
    ], value='Exclusive', id='overview-dm-dropdown', clearable=False),
    dcc.Graph(
        id='overview',
        config={
            'displayModeBar': False
        }
    )
])

def parse_profile(project, experiment, trial):
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tauData = TauProfileParser.parse(trial_path)
    profile = tauData.interval_data()
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
    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    profile = parse_profile(project, experiment, trial)

    metric_data = profile[[dropdown_value]].sort_values(dropdown_value, ascending=False)
    metric_df = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)

    TOP_N = 15
    if len(metric_df.index) > TOP_N:
        metric_df = pd.concat([metric_df[ :TOP_N], metric_df[TOP_N: ].groupby(level=0).sum().rename({dropdown_value: 'Other'})], copy=False)

    indices = ['Std. Dev.', 'Mean', 'Max', 'Min']
    for node, context, thread in metric_df.columns.values:
        indices.append(f'node {node}, context {context}, thread {thread}')

    TOTAL_THREAD_COUNT = len(metric_df.columns)
    metric_df['Std. Dev.'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].std(axis=1)
    metric_df['Mean'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].mean(axis=1)
    metric_df['Max'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].max(axis=1)
    metric_df['Min'] = metric_df.iloc[:, 0:TOTAL_THREAD_COUNT].min(axis=1)

    columns = list(metric_df.columns.values)
    metric_df = metric_df[columns[TOTAL_THREAD_COUNT:TOTAL_THREAD_COUNT+4] + columns[0:TOTAL_THREAD_COUNT]]

    index_count = len(indices)
    data = []
    for idx, row in metric_df.iterrows():
        text=['<br>'.join([idx[1][i:i + 75] for i in range(0, len(idx[1]), 75)])] * index_count
        bar = go.Bar(
            x=row.values[::-1],   
            y=indices[::-1],    
            orientation='h',   
            hoverinfo='text', 
            text=text
        )
        data.append(bar)

    data[-1]['marker'] = {'color': '#000000'} 
    data[-1]['text'] = 'Other' 

    layout = go.Layout(
        barmode='stack', 
        showlegend=False,
        hovermode='closest',
    )   

    fig = go.Figure(data=data, layout=layout)
    fig.update_layout(width=800, height=700)

    fig.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        )
    )
    
    return fig 


# Callback: Update URL when a node is clicked 
@app.callback(
    [Output('url', 'pathname'), Output('url', 'search')],
    Input('overview', 'clickData'),
    State('url', 'pathname')
)
def display_click_data(clickData, pathname):
    if clickData is None:
        raise PreventUpdate
    else:
        project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
        if clickData['points'][0]['y'] == 'Std. Dev.':
            index = 'stddev'
        elif clickData['points'][0]['y'] == 'Mean':
            index = 'mean'
        elif clickData['points'][0]['y'] == 'Max':
            index = 'max'
        elif clickData['points'][0]['y'] == 'Min':
            index = 'min'
        else:
            index = '-'.join(re.findall(r'\b\d+\b', clickData['points'][0]['y']))
        return f'/{project}/{experiment}/{trial}/bar-plot', f'?index={index}'
