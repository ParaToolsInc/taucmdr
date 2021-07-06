import pandas as pd
from itertools import islice, cycle
import plotly.graph_objs as go
from tau_profile_parser import TauProfileParser
import plotly.express as px
import plotly.io as pio
pio.renderers.default='iframe'
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
import dash_table
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import numpy as np

import config
from app import app

#the blank layout of the runtime breakdown page with default values
layout = html.Div(children = [
    dcc.Graph(id = 'brkdwn graph'), 
    html.Label('Metric:'),
    dcc.Dropdown(id='brkdwn-metric-selector-dropdown', clearable=False, options=config.option_metric_list,value='Exclusive'),
])

#runtime breakdown page callback
@app.callback(Output('brkdwn graph', 'figure'),Input('brkdwn-metric-selector-dropdown', 'value'))
def display_runtime_breakdown(metric):
    """
    Creates the runtime breakdown graph (using Plotly's filled area plot) with the current metric, slected from the dropdown
    param:
        metric: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        the runtime breakdown figure
    """
    metric_data = config.profile_1[[metric]].sort_values(metric,ascending=False)
    brkdwn_data = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
    #sorted_data.drop('Exclusive')
    BREAKDOWN_TOP_N = 9
    if len(brkdwn_data.index)>BREAKDOWN_TOP_N:
        brkdwn_data = pd.concat([brkdwn_data[:BREAKDOWN_TOP_N], brkdwn_data[BREAKDOWN_TOP_N:].sum(level=0).rename({metric: 'Other'})], copy=False)
    for i in range (0,len(brkdwn_data.index)-1):
        for j in range (1, config.TOTAL_THREAD_COUNT):
            #the values add up on each other as the number of threads/nodes increases 
            brkdwn_data.iat[i,j]=brkdwn_data.iat[i,j-1]+brkdwn_data.iat[i,j]
    x=[]
    for i in range (0,config.TOTAL_THREAD_COUNT):
        x.append('{}'.format(i))
    fig = go.Figure()
    for i in range (0, BREAKDOWN_TOP_N+1):
    ### shortening the strings in legend, not working yet###
        newString=brkdwn_data.index[i]
        if brkdwn_data.index[i] != 'Other':
            newString=newString[1:]
        if len(newString)>20:
            subtract = len(brkdwn_data.index[i])-20
            newString[:-subtract]
            #print('Subtracted')
                
        fig.add_trace(go.Scatter(
        x=x, y=brkdwn_data.iloc[i],     #sum(sorted_data.iloc[i][0:i])
        mode='lines',
        line=dict(width=0.5, color=config.colors[i]),
        stackgroup='one',
        groupnorm='percent', # sets the normalization for the sum of the stackgroup
        name='{}'.format(newString),
        ))

    fig.update_layout(
        showlegend=True,
        height=600,
        legend = dict(orientation="h"),
        xaxis_type='category',
        yaxis=dict(
            type='linear',
            range=[1, 100],
            ticksuffix='%'))
    return fig