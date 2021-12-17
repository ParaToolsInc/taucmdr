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

#the blank layout of the heat map page with default values
layout = html.Div(
    children=[
        html.Label('Data Metric:'),
        dcc.Dropdown(
            id='heatMap-dm-dropdown',
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
        dbc.Row([
            dbc.Col(
                children=dcc.Graph(id='single-heat-map')
            ),
            dbc.Col(
                children=dcc.Graph(id='path-heat-map')
            )
        ])
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
    [Output('single-heat-map', 'figure'), Output('path-heat-map','figure')],
    [Input('heatMap-dm-dropdown', 'value'), Input('url', 'pathname')]
)
def make_heat_map(metric, pathname):
    """
    Creates two heat maps, one for a single call and one for the call path using the current metric and one slected from the dropdown
    Note: only profile files containing "TAU_CALLPATH" data can be shown in a heat map.
    Code adapted from tau2/examples/jupyter_notebooks/PlotlyHeatMaps.ipynb on Github, and not 100% bug free

    param:
        metricNum: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        heat1: the single call heat map
        heat2: the call path heat map
    """

    project, experiment, trial, path = [i for i in pathname.split('/') if i != '']
    data_flat = parse_profile(project, experiment, trial)

    TOP_N = 10
    data_flat.columns = data_flat.columns.to_flat_index()
    num_threads = find_num_threads(data_flat)
    callpaths = create_callpath_data(data_flat)
    #chcks if TAU_CALLPATH data is present in dataframe (profile files)
    if len(callpaths)==0:
        return px.bar(title='Unable to create Heat Map, no "TAU_CALLPATH" data in current profile'),px.bar()
    else:
        callpaths = trim_data(callpaths, num_threads, TOP_N, metric)   #col_name == Exclusive
        data = create_func_data(data_flat)
        data = trim_data(data, num_threads, TOP_N, metric)
        heat1=show_heat_map_single_call(data, num_threads)
        heat2=show_heat_map_call_path(callpaths, num_threads) 
        heat1.update_layout(title='Single Call Heat Map')
        heat2.update_layout(title='Full Path Heat Map')

        return heat1, heat2


node, context = 0, 0

def create_func_data(data):
    """
    Everything but the TAU_CALLPATH group
    
    param:
        data: DataFrame
    """
    data = data.loc[~data["Group"].str.contains("TAU_CALLPATH")]
    return data
    
def create_callpath_data(data):
    """
    Only the TAU_CALLPATH group
    
    param:
        data: DataFrame
    """
    data = data.loc[data["Group"].str.contains("TAU_CALLPATH")]
    return data

def find_num_threads(raw_data):
    """
    Finds number of threads found in raw_data
    
    param:
        raw_data: DataFrame (interval_data())
    """
    d = raw_data.loc[0, 0]
    threads = set([i[0] for i in d.index])
    return len(threads)

def trim_data(data, num_threads, top_n, col_name):
    """
    creates and returns a dataframe containing the `top_n` `col_name` column of the `data` DataFrame
    """
    
    df = None
    cntr = 0
    first = True
    for thread in range(num_threads):        
        tmp = data.loc[node, context, thread][[col_name]] 
        tmp = tmp.sort_values(by=[col_name], ascending=False)  
        
        if first: 
            df = tmp
        else: 
            df = df.merge(tmp, how='inner', on=['Timer'], suffixes=(f"_{str(cntr)}", f"_{str(cntr + 1)}"))
            cntr += 1
        first = False
    truncated = df[:top_n]
    truncated = truncated.fillna("")
    return truncated



def create_function_labels(data):
    """Creats a list of labels to be desplayed on the y axis of heatmap"""
    functions_labels = [f for f in data.index]
    return functions_labels

def trim_a_single_call(single_call):
    """Strips and gets rid of the arguments of the timers signature"""
    func_name, location, timer_type = TauProfileParser.extract_from_timer_name(single_call)
    func_name = func_name.strip() if func_name is not None else ""
    timer_type = f"[{timer_type.strip()}]" if timer_type is not None else ""
    single_call = " ".join([timer_type, func_name])
    single_call = single_call[:single_call.find("(")] if single_call.find("(") != -1 else single_call
    return single_call
    
def trim_single_call_data(single_calls):
    functions_labels = [trim_a_single_call(f) for f in single_calls]
    return functions_labels

def trim_call_path_data(call_paths):
    """A callpath contains individual calls separated by `=>`, this function trims each individual call"""
    functions_labels = []
    for f in call_paths:
        f = f.split(" => ")
        f = [trim_a_single_call(i) for i in f]
        label = " => ".join(f)
        functions_labels.append(label)
    return functions_labels

def create_thread_labels(num_threads):
    """Creates thread labels that are the x-axis labels of our heatmap"""
    return [f"thrd_{str(t)}" for t in range(num_threads)]

def create_heat_map_data(data): 
    """Creates a 2d list which is the `heat` data needed for the heat map"""
    heat_map_data = []
    for r in data.iterrows():
        row = [i for i in r[1]]
        heat_map_data.append(row)
    return heat_map_data

def show_heat_map(heat_map_data, call_labels, thread_labels):
    fig = go.Figure(data=go.Heatmap(
                    z=heat_map_data,
                    x=thread_labels,
                    y=call_labels
                ))
    return fig
    
def create_labels(data, num_threads):
    """creates x-axis and y-axis labels"""
    thread_labels = create_thread_labels(num_threads)
    function_labels = create_function_labels(data)
    return thread_labels, function_labels

def show_heat_map_single_call(single_call_data, num_threads):
    """For single calls"""
    thread_labels ,function_labels = create_labels(single_call_data, num_threads)
    function_labels = trim_single_call_data(function_labels)
    heat_map_data = create_heat_map_data(single_call_data)
    return show_heat_map(heat_map_data, function_labels, thread_labels)
    
def show_heat_map_call_path(call_path_data, num_threads):
    """For call_path"""
    thread_labels ,function_labels = create_labels(call_path_data, num_threads)
    function_labels = trim_call_path_data(function_labels)
    heat_map_data = create_heat_map_data(call_path_data)
    return show_heat_map(heat_map_data, function_labels, thread_labels)

