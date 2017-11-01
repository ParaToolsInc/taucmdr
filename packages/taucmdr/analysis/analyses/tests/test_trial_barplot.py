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
"""Unit tests of the Trial Bar Plot analysis."""
import os

from taucmdr import tests, TAUCMDR_HOME, EXIT_SUCCESS
from taucmdr import analysis
from taucmdr.analysis.analyses.tests import AnalysisTest
from taucmdr.analysis.analyses.trial_barplot import ANALYSIS as trial_bar_plot_analysis
from taucmdr.cf.compiler.host import CC
from taucmdr.cf.compiler.mpi import MPI_CC
from taucmdr.cf.storage.levels import PROJECT_STORAGE
from taucmdr.cli.commands.trial.create import COMMAND as trial_create_cmd
from taucmdr.model.trial import Trial


class TrialBarPlotVisualizerTests(AnalysisTest):
    """Unit tests of the Trial Bar Plot analysis."""

    def test_get_trial_bar_plot_analysis(self):
        analysis_from_get_analysis = analysis.get_analysis(trial_bar_plot_analysis.name)
        self.assertIs(trial_bar_plot_analysis, analysis_from_get_analysis)

    def test_trial_bar_plot(self):
        self.reset_project_storage()
        self.assertManagedBuild(0, CC, [], 'hello.c')
        self.assertCommandReturnValue(0, trial_create_cmd, ['./a.out'])
        trial = Trial.controller(PROJECT_STORAGE).one({'number': 0})
        self.assertTrue(trial, "No trial found after run")
        path = trial_bar_plot_analysis.create_notebook(trial, '.', execute=True)
        self.assertTrue(os.path.exists(path), "Notebook should exist after call to create_notebook")

    @tests.skipUnlessHaveCompiler(MPI_CC)
    def test_summary_stats(self):
        self.reset_project_storage(['--mpi', '--profile', 'tau'])
        self.assertManagedBuild(0, MPI_CC, [], 'mpi_hello.c')
        self.assertCommandReturnValue(EXIT_SUCCESS, trial_create_cmd, ['mpirun', '-np', '4', './a.out'])
        trial = Trial.controller(PROJECT_STORAGE).one({'number': 0})
        self.assertTrue(trial, "No trial found after run")
        results = trial_bar_plot_analysis.run(trial, "Exclusive")
        self.assertTrue(results, "Results from analysis run should be non-empty")
        first_result = results[0]
        trial_results = first_result[1]
        self.assertTrue('Mean' in trial_results)
        self.assertTrue('Min' in trial_results)
        self.assertTrue('Max' in trial_results)
        self.assertTrue('Std. Dev.' in trial_results)
        self.assertTrue('.TAU application' in trial_results['Mean'])
        self.assertTrue('.TAU application' in trial_results['Min'])
        self.assertTrue('.TAU application' in trial_results['Max'])
        self.assertTrue('.TAU application' in trial_results['Std. Dev.'])
        self.assertTrue(trial_results['Min']['.TAU application'] <= trial_results['Max']['.TAU application'])
        self.assertTrue(trial_results['Min']['.TAU application'] <= trial_results['Mean']['.TAU application'])
        self.assertTrue(trial_results['Mean']['.TAU application'] <= trial_results['Max']['.TAU application'])
        self.assertNotEqual(trial_results['Std. Dev.']['.TAU application'], 0.0)

