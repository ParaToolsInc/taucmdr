#
# Copyright (c) 2016, ParaTools, Inc.
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
"""Test functions.

Functions used for unit tests of papi_installation.py.
"""

from taucmdr.tests import TestCase
from taucmdr.model.project import Project


class PapiInstallationTest(TestCase):
    """Unit tests for PapiInstallation."""

    def _get_papi_installation(self):
        expr = Project.selected().experiment()
        return expr.populate('target').get_installation('papi')

    def test_parse_metrics_none(self):
        self.reset_project_storage()
        papi = self._get_papi_installation()
        parsed = papi.parse_metrics(['TIME'])
        self.assertEqual([], parsed)

    def test_parse_metrics_preset(self):
        self.reset_project_storage()
        papi = self._get_papi_installation()
        parsed = papi.parse_metrics(['TIME', 'PAPI_TOT_CYC'])
        self.assertEqual(['PAPI_TOT_CYC'], parsed)

    def test_parse_metrics_colon(self):
        self.reset_project_storage()
        papi = self._get_papi_installation()
        parsed = papi.parse_metrics(['TIME', 'PAPI_NATIVE:CPU_CLK_UNHALTED'])
        self.assertEqual(['CPU_CLK_UNHALTED'], parsed)

    def test_parse_metrics_underscore(self):
        self.reset_project_storage()
        papi = self._get_papi_installation()
        parsed = papi.parse_metrics(['TIME', 'PAPI_NATIVE_CPU_CLK_UNHALTED'])
        self.assertEqual(['CPU_CLK_UNHALTED'], parsed)
