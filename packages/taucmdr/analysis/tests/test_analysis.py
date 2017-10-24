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
"""Unit tests of the Analysis infrastructure."""
import six
from taucmdr import tests
from taucmdr import analysis
from taucmdr.analysis.analysis import AbstractAnalysis


class AnalysisTests(tests.TestCase):
    """Unit tests of the Analysis infrastructure."""

    def test_get_analyses(self):
        analyses = analysis.get_analyses()
        self.assertTrue(analysis, "List of analyses should not be empty")
        for name, analysis_class in six.iteritems(analyses):
            self.assertIsInstance(analysis_class, AbstractAnalysis,
                                  "Objects returned from get_analyses should be analyses")
            self.assertEqual(name, analysis_class.name,
                             "Analysis name should equal name in analysis dict")

    def test_get_analysis(self):
        analyses = analysis.get_analyses()
        for name, analysis_class in six.iteritems(analyses):
            from_get_analysis = analysis.get_analysis(name)
            self.assertIs(analysis_class, from_get_analysis,
                          "Object obtained from get_analysis should match object in get_analyses dict")
