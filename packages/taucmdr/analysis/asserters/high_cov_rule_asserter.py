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

"""Asserts rule for detecting a high coefficient of variation"""
from durable.lang import *

from taucmdr.analysis.rules import RuleAsserter


class HighCoVRuleAsserter(RuleAsserter):
    """Asserts a rule for detecting a high coefficient of variation.

    Attributes:
        threshold (float): threshold for a 'high' coefficient of variation
    """

    def __init__(self, threshold, name='High Coefficient of Variance',
                 description='Detects timers with a coefficient of variation over some threshold'):
        super(HighCoVRuleAsserter, self).__init__(name=name, description=description)
        self.threshold = threshold
        self.matches = []

    def assert_rules(self, ruleset):
        """Assert rule for detecting a high coefficient of variation into the designated ruleset.

        Args:
            ruleset (str): The name of the ruleset into which this asserter posts.
        """
        with select(ruleset):
            @when_all( c.mean << (m.type == 'trial_stats') & (m.metric == 'Exclusive') & (m.stat == 'Mean'),
                      c.stddev << (m.type == 'trial_stats') & (m.metric == 'Exclusive') & (m.stat == 'Std. Dev.')
                      & (m.timer == c.mean.timer))
            def match(c):
                if float(c.stddev.value) / float(c.mean.value) > self.threshold:
                    self.matches.append(c.stddev.timer)
