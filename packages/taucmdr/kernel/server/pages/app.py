from .server import app
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.io as pio
pio.renderers.default='iframe'

styles = {
    'body': {
        'display': 'flex',
        'height': '100vh'
    },
    'sidebar': {

#        'position': 'fixed',
#        'top': 0,
#        'left': 0,
#        'bottom': 0,
#        'width': '10rem',
        'padding': '1.5rem 1rem',
        'backgroundColor': '#f8f9fa',
        'flex': '20%'
    },
    'content': {
#        'marginLeft': '7rem',
#        'marginRight': '2rem',
        'padding': '1.5rem 1rem',
#        'width': '800px'
        'flex': '80%'
    }
}

app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-sidebar', children=[], style=styles['sidebar']),
    html.Div(id='page-content', children=[], style=styles['content'])
], style=styles['body'])

from . import display, overview, correlation, runtime, data, heatmap
