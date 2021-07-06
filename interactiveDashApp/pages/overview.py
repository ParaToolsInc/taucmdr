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
from dash.exceptions import PreventUpdate
import numpy as np

from app import app
import config

#the blank layout of the overview page with default values
layout = html.Div(children=[
    html.Label('Data Metric:'),
    dcc.Dropdown(id='overview-dm-dropdown', clearable=False, options=config.option_metric_list,value='Exclusive'), #566
    dcc.Graph(id='overview',)
])

@app.callback(
    Output('overview', 'figure'),Input('overview-dm-dropdown', 'value'))
def make_overview(metricNum):
    """
    Creates the overview bar plot (using Plotly's bar plot) with the current metric, slected from the dropdown
    param:
        metricNum: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        the overview figure
    """
    metric_data = config.profile_1[[metricNum]].sort_values(metricNum,ascending=False)
    overview_df = metric_data.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
    #if there are more than N timers, only show the first N and put the rest in 'Other'
    if len(overview_df.index)>config.TOP_N:
        overview_df = pd.concat([overview_df[:config.TOP_N], overview_df[config.TOP_N:].sum(level=0).rename({metricNum: 'Other'})], copy=False)
    #the number of nodes/threads is the number of columns
    TOTAL_THREAD_COUNT = len(overview_df.columns)
    indices=['Std. Dev.', 'Mean', 'Max', 'Min']
    for (n,c,t) in overview_df.columns.values:
        indices.append("node {}, thread {}".format(n, t))
    overview_df['Std. Dev.']= overview_df.iloc[:,0:TOTAL_THREAD_COUNT].std(axis=1)
    overview_df['Mean'] = overview_df.iloc[:,0:TOTAL_THREAD_COUNT].mean(axis=1)
    overview_df['Max']= overview_df.iloc[:,0:TOTAL_THREAD_COUNT].max(axis=1)
    overview_df['Min']= overview_df.iloc[:,0:TOTAL_THREAD_COUNT].min(axis=1)
    #puts all stats data before the listing of nodes 
    cols = list(overview_df.columns.values)
    overview_df = overview_df[cols[TOTAL_THREAD_COUNT:TOTAL_THREAD_COUNT+4]+cols[0:TOTAL_THREAD_COUNT]]

    num_indices = len(indices)
    #make actual graph
    data = [go.Bar(
    y=indices[::-1],      # These are the labels on the Y axis. These are reversed so that (0,0,0) ends up on the top
    x=row.values[::-1],   # The timer values also have to be reversed so that they appear with the correct index
    orientation='h',      # Make this a horizontal bar plot (default is vertical)
    hoverinfo='text',     # When hovering over a region, show custom text. 
    # The custom text is the first 75 characters of the timer name.
    text=["<br>".join([index[1][i:i + 75] for i in range(0, len(index[1]), 75)])] * num_indices) 
    for index, row in overview_df.iterrows()]

    data[-1]['marker'] = {'color': '#000000'} # Make the last entry (the "Other" entry) have a black color
    data[-1]['text'] = 'Other'                # Name the last entry "Other"

    layout = go.Layout(
        barmode='stack',     # Specify a stacked bar plot
        showlegend=False,    # Hide the legend
        hovermode='closest', # Only show the pop-up label for the region that the mouse cursor is currently over
        title='{} {}'.format('Exclusive', 'TIME',# A title for the graph
        ) 
    )

    fig = go.Figure(data=data, layout=layout)
    fig.update_layout( width=1000,height=1000)
    return fig


#on click callback
#
@app.callback([Output('url', 'pathname'),Output('url','search')],Input('overview', 'clickData'))
def display_click_data(clickData):
    """
    When a node is clicked on the overview graph this method updates the pathname and search 
    component of the url. This will create a cascading effect of callbacks where the page content 
    will change, the node/thread dropdown on the 'Bar plot by Node' page will update, and as a result
    the the bar plot of that page will update.

    param:
        clickData: the data recieved from a click on the overview plot
    returns:
        the updated pathname and search components of the url
    """
    #won't update if there is no click data
    if clickData is None:
        raise PreventUpdate
    else:
        if clickData['points'][0]['y'] == "Std. Dev.":
            the_link=-4
        elif clickData['points'][0]['y'] == "Mean":
            the_link=-3
        elif clickData['points'][0]['y'] == "Max":
            the_link=-2
        elif clickData['points'][0]['y'] == "Min":
            the_link=-1
        else:
            the_link = clickData['points'][0]['y']
            the_link = the_link[5:-10]
    return '/bar-plot',str(the_link)