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

#the blank layout of the correlation page with default values
layout = html.Div(children=[
    html.Label('Choose First Function'),
    dcc.Dropdown(id='function-selector-dropdown', clearable=False, persistence=True, persistence_type='session',options=config.function_list,value=0), #566
    html.Label('Choose Second Function'),
    dcc.Dropdown(id='function-selector-dropdown2', clearable=False, persistence=True, persistence_type='session', options=config.function_list,value=0), #568
    dcc.Graph(id='graph 2'), 
    html.Label('Data Metric:'),
    dcc.Dropdown(id='scatter-metric-dropdown', clearable=False, persistence=True, persistence_type='session', options=config.option_metric_list,value='Exclusive')
])

#correlation graph page callback
@app.callback(Output('graph 2', 'figure'),[Input('function-selector-dropdown', 'value'),Input('function-selector-dropdown2', 'value'),
     Input('scatter-metric-dropdown', 'value')])
def display_scatter_plot(func1,func2,scat_met):
    """
    Creates the scatter plot (using Plotly's scatter) where different timers are graphed against each other.
    Uses the current timers and metric slected from the dropdowns.

    param:
        func1: the timer that gets graphed along the x axis
        func2: the timer that gets graphed along the y axis
        scat_met: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        the scatter plot figure
    """
    scatter_df = config.profile_1[[scat_met]] #.sort_values(scat_met,ascending=False)  <-- can't do b/c it will mess up picking timer from thread
    scatter_df = scatter_df.unstack().sort_values((0, 0, 0), axis=1).transpose().fillna(0)
    fig = px.scatter(x=scatter_df.iloc[func1].values, y=scatter_df.iloc[func2].values,trendline="ols",trendline_color_override="red",
                 labels={'x':'{}'.format(config.profile_1.loc[0,0,0]["Timer Name"].iloc[[func1]]), 
                         'y':'{}'.format(config.profile_1.loc[0,0,0]["Timer Name"].iloc[[func2]])})
    return fig