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

"""
This file parses the profile data and gets everything set up for data manipulation 
It also creats list components that are used by multiple pages throughout the app 
"""

#parse profile data and put it into a pandas dataframe 
#add exclusive and inclusive per call columns
f = open("pathName.txt", "r")
tauData = TauProfileParser.parse(f.read())
f.close()
profile_1 = tauData.interval_data()
profile_1["Exclusive per Call"] = profile_1.loc[:,'Exclusive']/profile_1.loc[:,'Calls']
profile_1["Inclusive per Call"] = profile_1.loc[:,'Inclusive']/profile_1.loc[:,'Calls']

#get the total thread count
thread_calc = profile_1[['Exclusive']].sort_values('Exclusive',ascending=False)
thread_calc = thread_calc.unstack().sort_values((0, 0, 0), axis=1, ascending=False).transpose().fillna(0)
TOTAL_THREAD_COUNT = len(thread_calc.columns)

#get the max value 
smax = profile_1['Exclusive'].max()
colors_str = "#1f77b4,#aec7e8,#ff7f0e,#ffbb78,#2ca02c,#98df8a,#d62728,#ff9896,#9467bd,#c5b0d5,#8c564b,#c49c94,#e377c2,#f7b6d2,#7f7f7f,#c7c7c7,#bcbd22,#dbdb8d,#17becf,#9edae5,#7fc97f,#beaed4,#fdc086,#ffff99,#386cb0,#f0027f,#bf5b17,#666666,#1b9e77,#d95f02,#7570b3,#e7298a,#66a61e,#e6ab02,#a6761d,#666666,#fbb4ae,#b3cde3,#ccebc5,#decbe4,#fed9a6,#ffffcc,#e5d8bd,#fddaec,#f2f2f2,#393b79,#5254a3,#6b6ecf,#9c9ede,#637939,#8ca252,#b5cf6b,#cedb9c,#8c6d31,#bd9e39,#e7ba52,#e7cb94,#843c39,#ad494a,#d6616b,#e7969c,#7b4173,#a55194,#ce6dbd,#de9ed6,#8dd3c7,#ffffb3,#bebada,#fb8072,#80b1d3,#fdb462,#b3de69,#fccde5,#d9d9d9,#bc80bd,#ccebc5,#ffed6f,#3182bd,#6baed6,#9ecae1,#c6dbef,#e6550d,#fd8d3c,#fdae6b,#fdd0a2,#31a354,#74c476,#a1d99b,#c7e9c0,#756bb1,#9e9ac8,#bcbddc,#dadaeb,#636363,#969696,#bdbdbd,#d9d9d9"
colors = colors_str.split(',')

#set up options for various dropdowns in the dash app 
option_list_to_string = ['Std. Dev.', 'Mean', 'Max', 'Min']    
option_list = [{'label':'Std. Dev.', 'value':0},{'label':'Mean', 'value':1},{'label':'Max', 'value':2},{'label':'Min', 'value':3}]
function_list = []
option_list_2=[]
#CHANGE TOP_N here
TOP_N =25
for i in range (0,TOTAL_THREAD_COUNT):
    ind = i+4
    option_list.append({'label':'Node ({},{},{})'.format(0,0,i), 'value':ind})
    option_list_2.append({'label':'Node ({},{},{})'.format(0,0,i), 'value':ind})
    
for j in range(0,len(profile_1.loc[0,0,0].values)-1):
    function_list.append({'label':'{}'.format(profile_1.loc[0,0,0]["Timer Name"].iloc[[j]]), 'value':j})

option_metric_list = [{'label':'Exclusive', 'value':'Exclusive'},{'label':'Inclusive', 'value':'Inclusive'},{'label':'Exclusive per Call', 'value':'Exclusive per Call'},
                      {'label':'Inclusive per Call', 'value':'Inclusive per Call'},{'label':'Number of Calls', 'value':'Calls'},
                      {'label':'Number of Child Calls', 'value':'Subcalls'}]

option_sortby_list = [{'label':'Same as Visbile Metric', 'value':'Same'},{'label':'Name', 'value':'Timer Name'},]

for k in range (0,len(option_metric_list)):
    option_sortby_list.append(option_metric_list[k])