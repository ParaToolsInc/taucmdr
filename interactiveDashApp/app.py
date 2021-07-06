import dash
import dash_bootstrap_components as dbc
from jupyter_dash import JupyterDash

#if not running app in jupyterLab use this:
#app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

#creats an empty jupyterDash app that's ready to run in jupyterLab
app = JupyterDash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server