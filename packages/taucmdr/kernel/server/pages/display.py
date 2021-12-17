from .server import app
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_bootstrap_components as dbc
from flask import request

from . import overview, barplot, correlation, runtime, data, heatmap

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def not_found_layout(pathname):
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
    
def sidebar_layout(project, experiment, trial, path):
    if path:
        return html.Div([
            dbc.Nav([
                dbc.NavLink('Back', href=f'/{project}/{experiment}/{trial}', external_link=True)
            ])
        ])
    else:
        return html.Div([
            html.H5('Menu', className='display-5'),
            html.Hr(),
            html.P('Paraprof-style graphs and tables that visualize TAU profiles', className='lead'),
            html.Hr(),
            dbc.Nav([
                dbc.NavLink('Overview', href=f'/{project}/{experiment}/{trial}/overview', active=(path == 'overview'), external_link=True),
                dbc.NavLink('Bar Plot by Node', href=f'/{project}/{experiment}/{trial}/bar-plot', active=(path == 'bar-plot'), external_link=True),
                dbc.NavLink('Correlation Graph', href=f'/{project}/{experiment}/{trial}/correlation', active=(path == 'correlation'), external_link=True),
                dbc.NavLink('Runtime Breakdown', href=f'/{project}/{experiment}/{trial}/runtime-breakdown', active=(path == 'runtime-breakdown'), external_link=True),
                dbc.NavLink('Data Table by Node', href=f'/{project}/{experiment}/{trial}/data-table', active=(path == 'data-table'), external_link=True),
                dbc.NavLink('Heat Map', href=f'/{project}/{experiment}/{trial}/heat-map', active=(path == 'heat-map'), external_link=True),
            ], vertical=True, pills=True)
        ])

@app.callback(
    [Output('page-sidebar', 'children'), Output('page-content', 'children')],
    Input('url', 'pathname')
)
def display_page(pathname):
    if (pathname == None):
        return None, None

    if (pathname == '/shutdown'):
        shutdown_server()
        return None, None

    directories = [i for i in pathname.split('/') if i != '']
    if (len(directories) < 3) or (len(directories) > 4):
        return not_found_layout(pathname)

    if len(directories) == 3:
        project, experiment, trial = [i for i in directories]
        path = None
    else:
        project, experiment, trial, path = [i for i in directories]
        if len(path.split('?index=')) == 2:
            path, index = path.split('?index=')
        
    sidebar = sidebar_layout(project, experiment, trial, path)

    if path == 'overview':
        return sidebar, overview.layout
    elif path == 'bar-plot':
        return sidebar, barplot.layout
    elif path == 'correlation':
        return sidebar, correlation.layout 
    elif path == 'runtime-breakdown':
        return sidebar, runtime.layout 
    elif path == 'data-table':
        return sidebar, data.layout
    elif path == 'heat-map':
        return sidebar, heatmap.layout 
    else:
        return sidebar, None 
#        return not_found_layout(pathname) 
