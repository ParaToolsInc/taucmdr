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
"""Unit tests of the Runtime Breakdown analysis."""
import os

from taucmdr import tests, TAUCMDR_HOME, EXIT_SUCCESS
from taucmdr import analysis
from taucmdr.analysis.analyses.runtime_breakdown import ANALYSIS as runtime_breakdown_analysis
from taucmdr.analysis.analyses.tests import AnalysisTest
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_cmd
from taucmdr.model.trial import Trial


class RuntimeBreakdownAnalysisTests(AnalysisTest):
    """Unit tests of the Runtime Breakdown analysis."""

    def test_get_runtime_breakdown_analysis(self):
        analysis_from_get_analysis = analysis.get_analysis(runtime_breakdown_analysis.name)
        self.assertIs(runtime_breakdown_analysis, analysis_from_get_analysis)

    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_runtime_breakdown(self):
        self.reset_project_storage(['--mpi', '--profile', 'tau'])
        self.assertManagedBuild(0, MPI_CC, [], 'mpi_hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        trial = Trial.controller(ANALYSIS_STORAGE).one({'number': 0})
        self.assertTrue(trial, "No trial found after run")
        path = runtime_breakdown_analysis.create_notebook(trial, '.', execute=True)
        self.assertTrue(os.path.exists(path), "Notebook should exist after call to create_notebook")

