# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, ParaTools, Inc.
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
"""Wrapper around a plot, providing interactivity support"""
from bokeh.application import Application
from bokeh.application.handlers import Handler
from bokeh.models.tools import HoverTool, TapTool
from bokeh.layouts import layout
from bokeh import plotting


class InteractivePlotHandler(Handler):
    """Holder for plots to be displayed in the Notebook interface.
    In charge of launching or connecting to the Bokeh server instance and
    setting up tools for interactivity."""

    def __init__(self, plots, tooltips=None, size=None):
        super(InteractivePlotHandler, self).__init__()
        if not isinstance(plots, list):
            plots = [plots]
        self.plots = plots
        self.tooltips = tooltips
        self.app = None
        self.size = size or 'scale_width'

    def add_plots(self, plots):
        """Add new plots to the handler"""
        if not isinstance(plots, list):
            plots = [plots]
        self.plots.extend(plots)

    def modify_document(self, doc):
        """This callback performs any necessary modifications to the Document
        to display the required figures

        Args:
            doc (bokeh.document.Document): The document to be rendered
        """
        for plot in self.plots:
            # Enable Hover Tool (shows tooltips on mouseover)
            if self.tooltips:
                hover_tool = HoverTool(tooltips=self.tooltips)
            else:
                hover_tool = HoverTool()
            plot.add_tools(hover_tool)
            plot.toolbar.active_inspect = [hover_tool]
            # Enable Tap Tool (allows clicking on chart glyphs)
            tap_tool = TapTool()
            plot.add_tools(tap_tool)
            plot.toolbar.active_tap = tap_tool
            view = layout(self.plots, sizing_mode=self.size)
        doc.add_root(view)

    def _create_app(self):
        if self.app is None:
            self.app = Application(self)

    def show(self):
        """Display the plots added to this object"""
        self._create_app()
        plotting.show(self.app)
