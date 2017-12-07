# -*- coding: utf-8 -*- #
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

"""Asserts summary statistics about trials"""
import six
from taucmdr.analysis.analysis import AbstractAnalysis
from taucmdr.analysis.rules import FactAsserter
from taucmdr.model.trial import Trial
from taucmdr.analysis.analyses.trial_barplot import ANALYSIS as trial_barplot_analysis


class TrialStatsFactAsserter(FactAsserter):
    """Asserts summary statistics about trials"""

    def __init__(self, name='Trial Stats', description='Asserts summary statistics about trials'):
        super(TrialStatsFactAsserter, self).__init__(name=name, description=description)

    def assert_facts(self, models, ruleset, host):
        """For each of the available summary statistics about a timer, this asserts a fact of the form

            {
                'trial': hash of the trial (str),
                'metric': name of the metric (e.g., Inclusive, Exclusive) (str),
                'timer': name of the timer (str),
                stat_name: stat_value (float)
            }

            where stat_name is one of the summary statistics calculated in Trial Barplot
            (e.g., Max, Min, Mean, Std. Dev.).

        args:
            models (list of :obj:`Trial`): Trial objects to be processed.
            ruleset (str): the name of the ruleset into which this asserter posts.
            host (:obj:`durable.lang.host`): the durable rules host into which this asserter posts.

        """
        metrics = AbstractAnalysis.get_metric_names(models, numeric_only=True)
        for trial in models:
            if not isinstance(trial, Trial):
                continue
            for metric in metrics:
                trial_summaries = [result[1] for result in trial_barplot_analysis.run(trial, metric=metric)]
                for trial_summary in trial_summaries:
                    for stat_name, stat_values in six.iteritems(trial_summary):
                        for timer_name, timer_value in six.iteritems(stat_values):
                            fact = {'type': 'trial_stats', 'trial': trial.hash_digest(), 'metric': metric,
                                    'timer': timer_name, 'stat': stat_name, 'value': str(timer_value)}
                            host.assert_fact(ruleset, fact)
