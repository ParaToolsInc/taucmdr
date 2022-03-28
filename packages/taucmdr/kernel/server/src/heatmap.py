#
# Copyright (c) 2022, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
""" This file is used for creating the heatmap webpage """

import os

from dash.dependencies import Input, Output
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
import plotly.express as px

from .server import app
from .parser import TauProfileParser

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
    """ This function is used for parsing profile data """
    project_dir = os.environ['PROJECT_DIR']
    trial_path = f'{project_dir}/{project}/{experiment}/{trial}'
    tau_data = TauProfileParser.parse(trial_path)
    profile = tau_data.interval_data()
    profile['Exclusive per Call'] = profile.loc[:, 'Exclusive']/profile.loc[:, 'Calls']
    profile['Inclusive per Call'] = profile.loc[:, 'Inclusive']/profile.loc[:, 'Calls']
    return profile


@app.callback(
    [Output('single-heat-map', 'figure'), Output('path-heat-map','figure')],
    [Input('heatMap-dm-dropdown', 'value'), Input('url', 'pathname')]
)
def make_heat_map(metric, pathname):
    """
    Creates two heat maps
       - one for a single call
       - one for the call path using the current metric and one slected from the dropdown
    Note: only profile files containing "TAU_CALLPATH" data can be shown in a heat map.
    Code from tau2/examples/jupyter_notebooks/PlotlyHeatMaps.ipynb on Github, not 100% bug free

    param:
        metricNum: a STRING that specifiies what data gets shown (Exclusive, Inclusive, Calls, etc.)
    returns:
        heat1: the single call heat map
        heat2: the call path heat map
    """

    project, experiment, trial, _ = [i for i in pathname.split('/') if i != '']
    data_flat = parse_profile(project, experiment, trial)

    top_n = 10
    data_flat.columns = data_flat.columns.to_flat_index()
    num_threads = find_num_threads(data_flat)
    callpaths = create_callpath_data(data_flat)
    #chcks if TAU_CALLPATH data is present in dataframe (profile files)
    if len(callpaths)==0:
        return px.bar(
                title='Unable to create Heat Map, no "TAU_CALLPATH" data in current profile'
               ), px.bar()
    callpaths = trim_data(callpaths, num_threads, top_n, metric)   #col_name == Exclusive
    data = create_func_data(data_flat)
    data = trim_data(data, num_threads, top_n, metric)
    heat1 = show_heat_map_single_call(data, num_threads)
    heat2 = show_heat_map_call_path(callpaths, num_threads)
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
    data = raw_data.loc[0, 0]
    threads = set(i[0] for i in data.index)
    return len(threads)

def trim_data(data, num_threads, top_n, col_name):
    """
    creates and returns a dataframe containing the `top_n` `col_name` column of the `data` DataFrame
    """

    data_frame = None
    cntr = 0
    first = True
    for thread in range(num_threads):
        tmp = data.loc[node, context, thread][[col_name]]
        tmp = tmp.sort_values(by=[col_name], ascending=False)

        if first:
            data_frame = tmp
        else:
            data_frame = data_frame.merge(tmp,
                    how='inner',
                    on=['Timer'],
                    suffixes=(f"_{str(cntr)}", f"_{str(cntr + 1)}")
                )
            cntr += 1
        first = False
    truncated = data_frame[:top_n]
    truncated = truncated.fillna("")
    return truncated

def create_function_labels(data):
    """Creats a list of labels to be displayed on the y axis of heatmap"""
    return list(data.index)

def trim_a_single_call(single_call):
    """Strips and gets rid of the arguments of the timers signature"""
    func_name, _, timer_type = TauProfileParser.extract_from_timer_name(single_call)
    func_name = func_name.strip() if func_name is not None else ""
    timer_type = f"[{timer_type.strip()}]" if timer_type is not None else ""
    single_call = " ".join([timer_type, func_name])
    trimmed = single_call[:single_call.find("(")] if single_call.find("(") != -1 else single_call
    return trimmed

def trim_single_call_data(single_calls):
    functions_labels = [trim_a_single_call(f) for f in single_calls]
    return functions_labels

def trim_call_path_data(call_paths):
    """
    A callpath contains individual calls separated by `=>`
    This function trims each individual call
    """
    functions_labels = []
    for paths in call_paths:
        paths = paths.split(" => ")
        paths = [trim_a_single_call(i) for i in paths]
        label = " => ".join(paths)
        functions_labels.append(label)
    return functions_labels

def create_thread_labels(num_threads):
    """Creates thread labels that are the x-axis labels of our heatmap"""
    return [f"thrd_{str(t)}" for t in range(num_threads)]

def create_heat_map_data(data):
    """Creates a 2d list which is the `heat` data needed for the heat map"""
    heat_map_data = []
    for _, row in data.iterrows():
        values = list(row)
        heat_map_data.append(values)
    return heat_map_data

def show_heat_map(heat_map_data, call_labels, thread_labels):
    """Creates heatmap based on call and thread labels"""
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
    thread_labels, function_labels = create_labels(single_call_data, num_threads)
    function_labels = trim_single_call_data(function_labels)
    heat_map_data = create_heat_map_data(single_call_data)
    return show_heat_map(heat_map_data, function_labels, thread_labels)

def show_heat_map_call_path(call_path_data, num_threads):
    """For call_path"""
    thread_labels, function_labels = create_labels(call_path_data, num_threads)
    function_labels = trim_call_path_data(function_labels)
    heat_map_data = create_heat_map_data(call_path_data)
    return show_heat_map(heat_map_data, function_labels, thread_labels)
