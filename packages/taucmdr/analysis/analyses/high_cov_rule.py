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
"""Rule based detection of high coefficient of variation"""

from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.error import ConfigurationError
from taucmdr.model.trial import Trial

import nbformat

import inspect


def run_cov_analysis(trial_id):
    from taucmdr.model.trial import Trial
    from taucmdr.cf.storage.levels import ANALYSIS_STORAGE
    from taucmdr.analysis.asserters.trial_stats_asserter import TrialStatsFactAsserter
    from taucmdr.analysis.asserters.high_cov_rule_asserter import HighCoVRuleAsserter
    from taucmdr.analysis.rules import RuleBasedClassifier

    if isinstance(trial_id, str):
        trial = Trial.controller(ANALYSIS_STORAGE).search_hash(trial_id)[0]
    elif isinstance(trial_id, Trial):
        trial = trial_id
    else:
        raise ValueError("Input must be either a hash or a Trial")

    stats_asserter = TrialStatsFactAsserter()
    cov_asserter = HighCoVRuleAsserter(0.5)
    classifier = RuleBasedClassifier('CoV Classifier', 'trials', [trial],
                                     fact_asserters=[stats_asserter], rule_asserters=[cov_asserter])
    classifier.run()
    return cov_asserter.matches


class HighCoVRule(AbstractAnalysis):

    def __init__(self, name='high-cov-rule', description='High CoV Rule Detector'):
        super(HighCoVRule, self).__init__(name=name, description=description)

    @staticmethod
    def _check_input(inputs, **kwargs):
        if not isinstance(inputs, list):
            inputs = [inputs]
        if not inputs:
            raise ConfigurationError("CoV requires that at least one trial be selected")
        for trial in inputs:
            if not isinstance(trial, Trial):
                raise ConfigurationError("CoV can only be performed for Trials.")
        return inputs

    def get_input_spec(self, inputs, *args, **kwargs):
        pass

    def get_cells(self, inputs, interactive=True, *args, **kwargs):
        """Get Jupyter input cell containing code which will use a rule-based classifier to
        identify timers with a high coefficient of variation.

        Args:
            inputs (:obj:`Trial`): The trial to analyze
            interactive (bool): Whether to create an interactive visualization using IPyWidgets

        Returns:
            list of :obj:`nbformat.NotebookNode`: The cells which identify high CoV trials.

        Raises:
            ConfigurationError: The provided model is not a Trial
        """
        trials = self._check_input(inputs, **kwargs)
        commands = [inspect.getsource(run_cov_analysis)]
        for trial in trials:
            digest = trial.hash_digest()
            commands.append('run_cov_analysis(Trial.controller(ANALYSIS_STORAGE).'
                            'search_hash("%s")[0])' % digest)
        cell_source = "\n".join(commands)
        return [nbformat.v4.new_code_cell(cell_source)]

    def run(self, inputs, *args, **kwargs):
        """Create a barplot as direct notebook output for the specific profile in trial in `inputs`.

        Args:
            inputs (:obj:`Trial`): The trial to visualize

        Raises:
            ConfigurationError: The provided model is not a Trial, or more than one provided
        """
        trials = self._check_input(inputs)
        run_cov_analysis(trials)


ANALYSIS = HighCoVRule()
