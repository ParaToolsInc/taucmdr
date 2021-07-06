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

#the blank layout of the data table page with default values
layout = html.Div(children = [
    html.Label('Choose Node'),
    dcc.Dropdown(id='graph-selector-dropdown4', clearable=False, persistence=True, persistence_type='session', options=config.option_list_2,value=4),
    html.Div(id='table-container', children=[]),
])

#data table page callback
@app.callback(
 [Output('table-container', 'children')],[Input('graph-selector-dropdown4', 'value')])
def changeTable(selectorValue):
    """
    Creates a very interactable data table (using Dash's data table) with the current node, slected from the dropdown
    param:
        selectorValue: the STRING value of the node dropdown, indicating what node to show in the table
    returns:
        a dash data table component with the correct 
    """
    table_df = config.profile_1.loc[(selectorValue-4,0,0)]
    return [dash_table.DataTable(id='table',columns=[{"name": i, "id": i} for i in table_df.columns],
                         data=table_df.to_dict('records'), filter_action='native',sort_action='native',
                         style_cell={'overflow': 'hidden','textOverflow':'clip' ,'maxWidth': 50,},
                         tooltip_data=[{column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()}
                                       for row in table_df.to_dict('records')],
                         tooltip_duration=None,
                        page_action='none',
                        style_table={'height': '720px', 'overflowY': 'auto'}),]