import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app
from app import server
import sys
#puts path name in pathName.txt for easy access by config.py
filePath=sys.argv[1]
f = open("pathName.txt", "w")
f.write(filePath)
f.close()
from pages import overview, barPlot, correlation, runtimeBrk, dataTable, heatMap


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "12rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# padding for the page content
CONTENT_STYLE = {
    "margin-left": "14rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

#creates sidebar that allows for navigation between graphs
sidebar = html.Div(
    [
        html.H2("Menu", className="display-4"),
        html.Hr(),
        html.P(
            "Paraprof-style graphs and tables that visualize TAU profiles", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact", external_link=True),
                dbc.NavLink("Bar Plot by Node", href="/bar-plot", active="exact", external_link=True),
                dbc.NavLink("Correlation Graph", href="/correlation", active="exact", external_link=True),
                dbc.NavLink("Runtime Breakdown", href="/runtime-breakdown", active="exact", external_link=True),
                dbc.NavLink("Data Table by Node", href="/data-table", active="exact", external_link=True),
                dbc.NavLink("Heat Map", href="/heat-map", active="exact", external_link=True),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    content
])

 
@app.callback(Output('page-content', 'children'),[Input('url', 'pathname'), Input('url','search')])
def display_page(pathname,search):
    """
    Displays page content based on a change in the pathname of the url. Uses the search component 
    of the url to update the specific bar plot for the 'bar-plot' page.
    param:
        pathname: the current pathname of the url
        search: the current value after the pathname, corresponding to what node was clicked 
    returns:
        the new page content in the form of a page layout
    """
    if pathname == '/':
        return overview.layout
    elif pathname=='/bar-plot':
        print("search: "+search)
        return barPlot.get_layout(search)
    elif pathname == '/correlation':
        return correlation.layout
    elif pathname == '/runtime-breakdown':
        return runtimeBrk.layout
    elif pathname == '/data-table':
        return dataTable.layout
    elif pathname == '/heat-map':
        return heatMap.layout
    elif pathname is not None and '/bar-plot' in pathname:
        print('Pathname: '+pathname)
        return barPlot.get_layout(0)
    else:
        return  dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognized..."),
        ])

#runs the app in-line with jupyter notebook
if __name__ == '__main__':
    app.run_server(mode='inline',debug=False, port=5632,height=800)