# Interactive Dash App
## What it is:
It’s an interactive webpage application that visualizes TAU profile.x.y.z data using bar plots, scatter plots, tables, and more. It mainly uses pandas, plotly, dash, and ipywidget libraries to run both in JupyterLab as well as independently on a localhost or server. The structure is set up like this:

- app.py
- index.py
- config.py
- pathName.txt
- tau_profile_parser.py
- pages
    - overview.py
    - barPlot.py
    - correlation.py
    - runtimeBrk.py
    - dataTable.py
    - HeatMap.py

It’s run by calling index.py with a file path to the TAU profile.x.y.z files as a command line argument. The TauProfileParser takes these profile files and creates a multi-index pandas data frame. Each page manipulates this data frame to display a specific graph, bar plot, table etc. All code is written in python and the interactivity is depended on dash callbacks. These callbacks call methods and update page content as soon as their input values are changed, without having to reload the page. This allows for clean and connected webpages written exclusively in python. This project was developed in a conda environment with very specific python libraries. These can be found in the environment.yml file. While this project was made to run in-line in JupyterLab, it can also run locally or deployed on a server.

---

### Current Bugs
Currently, most everything should work with a variety of different profile files. However, some labeling may be off on the ‘bar-plot by node’ page if profile files contain numerous threads per node. For example, if there is data for node/thread (0,0,1) & (0,0,2) but also (1,0,1) & (1,0,2) then the labels won’t match up. Also, the heat map page currently only supports one node/thread so any TAU_CALLPATH data across multiple threads will have some problems. Lastly, when navigating from the overview graph to the ‘bar-plot by node’ page by clicking on a specific node/thread, everything in the page content updates, however the sidebar doesn’t set the ‘bar-plot by node’ page active. This does not affect performance, but may lead to some confusion.

---

### Next Steps
Moving forward bugs need to be addressed and support for all types of profiles needs to be ensured. This will require extensive testing with various other profiles and some tweaks in code, especially for the ‘bar-plot by node’ page. Additionally, with the separation of pages by file, more unique graphs can easily be added to this project. Lastly, this project will have to be combined with the interactive TAU dashboard being built with JupyterLab extensions and made sure it can run on CommanderConda. 
