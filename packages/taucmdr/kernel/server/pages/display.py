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
""" This file is used for routing links to their respected displays """ 

from dash.dependencies import Input, Output
from dash import html
import dash_bootstrap_components as dbc
from flask import request

from .server import app
from . import overview, barplot, correlation, runtime, data, heatmap

def shutdown_server():
    """ This function is used for shutting down the server progmatically """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def not_found_layout(pathname):
    """ This function is used for returning 404 errors """
    return (
        html.Div([
            html.H2('Error', className='display-4'),
            html.Hr(),
            dbc.Nav([
                dbc.NavLink('Go back', href='javascript:history.back()')
            ])
        ]),
        dbc.Container([
            html.H1('404: Not found', className='text-danger'),
            html.Hr(),
            html.P(f'The pathname {pathname} was not recognized...')
        ])
    )

sidebar_styles = {
    'sidebar_back': {
        'padding': '1.5rem 1rem',
        'backgroundColor': '#f8f9fa',
        'flex': '0%',
        'height': '100%'
    },
    'sidebar_full': {
        'padding': '1.5rem 1rem',
        'backgroundColor': '#f8f9fa',
        'flex': '20%',
        'height': '100%'
    },
}

def sidebar_layout(project, experiment, trial, path):
    """ This function is used for displaying the sidebar on each webpage """
    if path:
        return html.Div(id='page-sidebar', children=[
            dbc.Nav([
                dbc.NavLink('Back', href=f'/{project}/{experiment}/{trial}', external_link=True)
            ])
        ], style=sidebar_styles['sidebar_back'])
    return html.Div(id='page-sidebar', children=[
        html.H5('Menu', className='display-5'),
        html.Hr(),
        html.P('Paraprof-style graphs and tables that visualize TAU profiles',
                className='lead'),
        html.Hr(),
        dbc.Nav([
            dbc.NavLink('Overview',
                href=f'/{project}/{experiment}/{trial}/overview',
                active=(path == 'overview'),
                external_link=True),
            dbc.NavLink('Bar Plot by Node',
                href=f'/{project}/{experiment}/{trial}/bar-plot',
                active=(path == 'bar-plot'),
                external_link=True),
            dbc.NavLink('Correlation Graph',
                href=f'/{project}/{experiment}/{trial}/correlation',
                active=(path == 'correlation'),
                external_link=True),
            dbc.NavLink('Runtime Breakdown',
                href=f'/{project}/{experiment}/{trial}/runtime-breakdown',
                active=(path == 'runtime-breakdown'),
                external_link=True),
            dbc.NavLink('Data Table by Node',
                href=f'/{project}/{experiment}/{trial}/data-table',
                active=(path == 'data-table'),
                external_link=True),
            dbc.NavLink('Heat Map',
                href=f'/{project}/{experiment}/{trial}/heat-map',
                active=(path == 'heat-map'),
                external_link=True),
        ], vertical=True, pills=True)
    ], style=sidebar_styles['sidebar_full'])

@app.callback(
    [Output('page-sidebar', 'children'), Output('page-content', 'children')],
    Input('url', 'pathname')
)
def display_page(pathname):
    """ This function is used for routing the URL to the correct display """
    if pathname is None:
        return None, None

    if pathname == '/shutdown':
        shutdown_server()
        return None, None

    directories = [i for i in pathname.split('/') if i != '']
    if (len(directories) < 3) or (len(directories) > 4):
        return not_found_layout(pathname)

    if len(directories) == 3:
        project, experiment, trial = directories
        path = None
    else:
        project, experiment, trial, path = directories
        if len(path.split('?index=')) == 2:
            path, _ = path.split('?index=')

    sidebar = sidebar_layout(project, experiment, trial, path)

    if path == 'overview':
        return sidebar, overview.layout
    if path == 'bar-plot':
        return sidebar, barplot.layout
    if path == 'correlation':
        return sidebar, correlation.layout
    if path == 'runtime-breakdown':
        return sidebar, runtime.layout
    if path == 'data-table':
        return sidebar, data.layout
    if path == 'heat-map':
        return sidebar, heatmap.layout
    return sidebar, None
