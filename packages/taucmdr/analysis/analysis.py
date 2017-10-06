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

import six
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


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

    def __init__(self, name, description):
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

    def create_notebook(self, inputs, path, execute=False, *args, **kwargs):
        """Create a Jupyter notebook which, when executed, performs the analysis.

        Args:
            inputs (list of :obj:`Model`): The models containing the data to be analyzed.
            path (str): Path to the directory in which the notebook is to be created.
            execute (bool): Whether to execute the notebook before writing it.

        Returns:
            (str): Absolute path to the created notebook

        Raises:
            ConfigurationError: The provided models are not of the type required by the analysis.

        """
        nb = nbformat.v4.new_notebook()
        nb['cells'] = self.get_cells(inputs, *args, **kwargs)
        nb['metadata']['kernel_info'] = nbformat.NotebookNode()
        nb['metadata']['kernel_info']['name'] = 'python2'
        if execute:
            ep = ExecutePreprocessor(timeout=600, kernel_name='python2')
            ep.preprocess(nb, {'metadata': {'path': path}})
        nb_name = "%s-%s.ipynb" % (self.name, uuid.uuid4().hex)
        file_path = os.path.abspath(os.path.join(path, nb_name))
        with open(file_path, 'w') as nb_file:
            nbformat.write(nb, nb_file)
        return file_path

