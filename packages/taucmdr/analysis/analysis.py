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
"""Abstract base class for an analysis"""

from abc import ABCMeta, abstractmethod
import uuid

import os

import sys

import six
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from taucmdr import util


class AbstractAnalysis(six.with_metaclass(ABCMeta, object)):
    """Abstract base class for analyses.

    An analysis is a class which processes trial data and produces a visualization or report
    for use in Jupyter's notebook interface. Instances should be able to run the analysis and
    produce the output directly (for interactive use directly in the notebook), create one or
    more Jupyter InputCells (for inserting into an existing notebook), or create an entire
    Jupyter notebook (for starting a new visualization or analysis from the TAU Commander GUI).

    Attributes:
        name (str): The name of the analysis, to be shown in the UI.
        description (str): A description of what the analysis does, to be shown as help text.
    """

    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description

    def __str__(self):
        return self.name

    @abstractmethod
    def run(self, inputs, *args, **kwargs):
        """Runs the analysis on `inputs` directly.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.
        """

    @abstractmethod
    def get_cells(self, inputs, *args, **kwargs):
        """Get Jupyter cells which, when executed in order, perform the analysis.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which perform the analysis.

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.

        """

    @staticmethod
    def _set_notebook_metadata(nb):
        # Set up notebook metadata to identify the kernel used
        nb['metadata']['kernel_info'] = nbformat.NotebookNode()
        nb['metadata']['kernel_info']['name'] = 'python2'

        # Also include the metadata that would be written by JupyterLab to select a specific
        # kernelspec, so that it doesn't prompt the user to select a kernel when the notebook
        # is opened for the first time.
        nb['metadata']['kernelspec'] = nbformat.NotebookNode()
        nb['metadata']['kernelspec']['name'] = 'python2'
        nb['metadata']['kernelspec']['language'] = 'python'
        nb['metadata']['kernelspec']['display_name'] = 'Python 2'

        # And tell CodeMirror what language to use for syntax highlighting.
        nb['metadata']['language_info'] = nbformat.NotebookNode()
        nb['metadata']['language_info']['name'] = 'python'
        nb['metadata']['language_info']['version'] = 2
        nb['metadata']['language_info']['codemirror_mode'] = nbformat.NotebookNode()
        nb['metadata']['language_info']['codemirror_mode']['name'] = 'ipython'
        nb['metadata']['language_info']['codemirror_mode']['version'] = 2

    @staticmethod
    def _create_notebook_from_cells(cells):
        nb = nbformat.v4.new_notebook()
        AbstractAnalysis._set_notebook_metadata(nb)

        # The 'cells' field contains a list of input cells
        nb['cells'] = cells
        return nb

    def create_notebook(self, inputs, path, filename=None, execute=False, *args, **kwargs):
        """Create a Jupyter notebook which, when executed, performs the analysis.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.
            path (str): Path to the directory in which the notebook is to be created.
            filename (str): Name of the file to which the notebook is to be written.
            execute (bool): Whether to execute the notebook before writing it.

        Returns:
            (str): Absolute path to the created notebook

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.

        """
        cells = self.get_cells(inputs, *args, **kwargs)
        nb = self._create_notebook_from_cells(cells)

        # If requested, we do an in-place execute of the notebook. Unfortunately, this is
        # less useful than it might otherwise be, as it doesn't take place in a browser and so
        # any commands that require JavaScript to execute won't actually generate output.
        if execute:
            ep = ExecutePreprocessor(timeout=600, kernel_name='python2')
            ep.preprocess(nb, {'metadata': {'path': path}})

        # Finally, we write out the notebook as a version 4 notebook file
        nb_name = filename if filename else "%s-%s.ipynb" % (self.name, uuid.uuid4().hex)
        file_path = os.path.abspath(os.path.join(path, nb_name))
        with open(file_path, 'w') as nb_file:
            nbformat.write(nb, nb_file)
        return file_path


class Recommendation(object):
    """Recommendation for user action to improve performance

    Attributes:
        name (str): A name for the recommendation. Used as a heading for the notebook section.
        description (str): User facing text explaining what to be done.
                           Displayed in the UI as a checkbox. May contain Markdown formatting.
        cells (list of :obj:`nbformat.NotebookNode`): The Jupyter cells providing details on the recommendation.
        priority (int): A number used to order recommendations. A larger number is more urgent.
        """

    def __init__(self, name=None, description=None, cells=None, priority=0):
        self.name = name
        self.description = description
        self.cells = cells
        self.priority = priority

    def __hash__(self):
        return hash((self.name, self.description, self.cells, self.priority))

    def __lt__(self, other):
        try:
            if self.priority == other.priority:
                return self.name < other.name
            return self.priority < other.priority
        except AttributeError:
            return NotImplemented


class AbstractRecommendationAnalysis(six.with_metaclass(ABCMeta, AbstractAnalysis)):
    """Abstract base class for a recommendation-producing analysis.

    An analysis class which may produce recommendations for actions to be taken
    to improve performance of the application being analyzed. In addition to the cells
    of the analysis itself, a recommendation analysis produces a list of recommendations,
    each of which is associated with one or more notebook cells that provide details on
    the recommendation. Each recommendation also has a priority, so that recommendations
    from multiple analyses can be combined into one report.

    Attributes:
        name (str): The name of the analysis, to be shown in the UI.
        description (str): A description of what the analysis does, to be shown as help text.
    """

    def __init__(self, name=None, description=None):
        super(AbstractRecommendationAnalysis).__init__(name=name, description=description)

    @abstractmethod
    def run(self, inputs, *args, **kwargs):
        """Runs the analysis on `inputs` directly.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.
        """

    @abstractmethod
    def get_recommendations(self, inputs, *args, **kwargs):
        """Get Jupyter cells which, when executed in order, perform the analysis.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.

        Returns:
            list of :obj:`Recommendation`: The recommendations produced by the analysis. May be empty.

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.

        """

    def get_cells(self, inputs, *args, **kwargs):
        """Get Jupyter cells which, when executed in order, perform the analysis.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which perform the analysis.

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.

        """
        cells = []
        recommendations = self.get_recommendations(inputs, *args, **kwargs)
        # Recommendation checkboxes
        checkboxes = ["%%html"]
        for recommendation in sorted(recommendations):
            checkboxes.append('<input type="checkbox">%s</input>' % recommendation.name)
        checkboxes_cell = nbformat.v4.new_code_cell("\n".join(checkboxes))
        cells.append(checkboxes_cell)
        for recommendation in recommendations:
            title_cell = nbformat.v4.new_markdown_cell('# %s' % recommendation.name)
            cells.append(title_cell)
            cells.extend(recommendation.cells)
        return cells
