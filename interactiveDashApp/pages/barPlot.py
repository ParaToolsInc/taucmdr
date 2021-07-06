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

def get_layout(search):
    """
    Creates the layout for the 'bar plot by node' page, with default values and the node number
    param:
        search: the component of the url that contains the node number that was clicked on in the overview plot
    returns:
        the 'bar plot by node' page layout
    """
    if search == '':
        search=0
    layout = html.Div(children=[
        html.Label('Choose Graph'),
        html.Div(id='dropdown-container', children=[dcc.Dropdown(id='graph-selector-dropdown', persistence=True, persistence_type='session', clearable=False,options=config.option_list,value=int(search)+4)]),
        dcc.Graph(id ='graph 1'),
        html.Label('Options'),
        dbc.Row([dbc.Col(children=dcc.Checklist(id='checklist-1',options=[{'label': 'Descending', 'value': '0'}, 
                                                                        {'label': 'Show Meta Data in Panel', 'value': '1'}, 
                                                                    #{'label': 'Show Values as Percent', 'value': '2'}
                                                                    ],value=['0','1'])),
            dbc.Col(children=[html.Label('Metric:'),dcc.Dropdown(id='select-metric', clearable=False, persistence=True, persistence_type='session', options=config.option_metric_list, value='Exclusive')]),
            dbc.Col(children=[html.Label('Sort By:'),dcc.Dropdown(id='sort-by',clearable=False, persistence=True, persistence_type='session', options=config.option_sortby_list, value='Same')]),
            dbc.Col(children=[html.Label('Units:'),dcc.Dropdown(id='select-units', clearable=False, persistence=True, persistence_type='session', options=[{'label':'Mircoseconds', 'value':'Mircoseconds'},
                {'label':'Milliseconds', 'value':'Milliseconds'},{'label':'Seconds', 'value':'Seconds'},
                #{'label':'hr:min:sec', 'value':'hr:min:sec'}
                                                                                                            ],value='Mircoseconds')])
            ]
            ),
        html.Label('Metric',id="metadata"),
        ])
    return layout

@app.callback(Output('sort-by','options'), Input('graph-selector-dropdown','value'))
def change_sort_by(graph_value):
    """
    Changes the Sort-By dropdown to only one option when any of the statistical plots are selected
    param:
        graph_value: the value of the node dropdown, indicating if it's a stat plot or not
    returns:
        the options component of the 'sort-by' dropdown
    """
    if int(graph_value) <4:
        return [{'label':'Same as Visbile Metric', 'value':'Same'}]
    else:
        return config.option_sortby_list

#bar plot page callback
@app.callback([Output('graph 1', 'figure'), Output('metadata', 'children')], [Input("graph-selector-dropdown", 'value'), 
                                                                              Input('checklist-1','value'), Input('select-metric','value'),
                                                                              Input('sort-by','value'),Input('select-units','value')])
def display_bar_plot(nodeNum, checklistArr, metricNum, sortNum, unitNum):
    """
    Creates the bar plot (using Plotly's bar plot) based on the node number and data from the page dropdowns
    param:
        nodeNum: the STRING value of the node dropdown, indicating what node graph to show
        checklistArr: an list of ints indicating what checkboxes are selected
        metricNum: a STRING that specifies what type of data gets shown (Exclusive, Inclusive, Calls, etc.)
        sortNum: a STRING that specifies what the data is sorted by (Exclusive, Inclusive, Calls, etc.)
        unitNum: a STRING that specifies what units are shown on the bar labels
    returns:
        current_graph: the bar plot figure
        current_text: the meta data text that's shown in the bottom left corner
    """
    if (sortNum=='Same'):
        sortNum=metricNum
    if unitNum == 'Milliseconds':
        divisorNum = 1000
    elif unitNum == 'Seconds':
        divisorNum = 1000000
    else:
        divisorNum = 1
    fig = make_subplots(specs=[[{"secondary_y": True}]]) #secondary_y=True associates the right side yaxis
    if(nodeNum<4):
    ##### MAKE STATS DF's ##########
        new_metric_data = config.profile_1[[metricNum]] #.sort_values(sortValueNum,ascending=False)
        new_metric_data = new_metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
        new_metric_data['Std. Dev.']= new_metric_data.iloc[:,0:config.TOTAL_THREAD_COUNT].std(axis=1)
        new_metric_data['Mean'] = new_metric_data.iloc[:,0:config.TOTAL_THREAD_COUNT].mean(axis=1)
        new_metric_data['Max']= new_metric_data.iloc[:,0:config.TOTAL_THREAD_COUNT].max(axis=1)
        new_metric_data['Min']= new_metric_data.iloc[:,0:config.TOTAL_THREAD_COUNT].min(axis=1)
        index = config.option_list_to_string[nodeNum]
        new_metric_data = new_metric_data.sort_values(index, ascending=False)
        truncated_metric_data = pd.concat([new_metric_data[:config.TOP_N], new_metric_data[config.TOP_N:].sum(level=0).rename({metricNum: 'Other'})], copy=False)
        #creates labels for stats plots
        dfIndexArray=[]
        for dfIndex in truncated_metric_data.index.values:
            if dfIndex == 'Other':
                dfIndexArray.append(dfIndex)
            else:
                theStr = ''.join(dfIndex)
                theStr=theStr[len(metricNum):]
                dfIndexArray.append(theStr)
        fig.add_trace(go.Bar(x=truncated_metric_data[index], y=dfIndexArray, orientation='h', marker=dict(
        # Pick the next color from the list. If we run out of colors, start over
            color=list(islice(cycle(config.colors), config.thread_calc.shape[0])),),    
                text=round(truncated_metric_data[index]/divisorNum,3), # Label the entries with the timer time based on the units dropdown
                textposition='outside'),secondary_y=True)
    else:
        current_df = config.profile_1.loc[(nodeNum-4,0,0)].sort_values(sortNum,ascending=False)
        current_df = pd.concat([current_df[:20], current_df[20:].sum(level=0).rename({metricNum: 'Other'})], copy=False)
        if len(current_df.index)>config.TOP_N:
            current_df = current_df.iloc[:config.TOP_N,:]        
        fig.add_trace(go.Bar(x=current_df[metricNum], y=current_df.index.values, orientation='h', marker=dict(
                # Pick the next color from the list. If we run out of colors, start over.
                color=list(islice(cycle(config.colors), current_df.shape[0])),),    
                        text=round(current_df[metricNum]/divisorNum,3),# Label the entries with the timer time based on the units dropdwon
                        textposition='outside'),secondary_y=True)
    fig.update_layout(width=1200,height=500,    xaxis=dict(
        # Expand the X axis range a bit so that the bars don't appear right at the edge, and to leave space for the labels
        range=[-0.1 * config.smax, config.smax * 1.5]
    ),margin=dict(l=20, r=300, t=20, b=20),)
    fig.update_xaxes(autorange='reversed') #Makes the bars start on the right side
    fig.update_yaxes(autorange='reversed') #Makes top to bottom go from largest to smallest
    current_graph = fig
    #updates the metadata component based on what's checked in the checklist
    if '0' in checklistArr:
        current_graph.update_yaxes(autorange='reversed')
    else:
        current_graph.update_yaxes(autorange=True)
    if '1' in checklistArr:
        current_text = dbc.Col(children=[dbc.Row(children=[html.Label("Metric: {}".format(metricNum))]), 
                                         dbc.Row(children=[html.Label("Sort By Value: {}".format(sortNum))]),
                                         dbc.Row(children=[html.Label("Units: {}".format(unitNum))])
        ]) 
    else:
        current_text=html.Label("",hidden=True)
    return current_graph, current_text