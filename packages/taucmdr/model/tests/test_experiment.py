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

Functions used for unit tests of experiment.py.
"""

from unittest import mock

from taucmdr import tests
from taucmdr.error import ConfigurationError
from taucmdr.cf.storage import StorageRecord
from taucmdr.model import experiment
from taucmdr.model.experiment import Experiment
from taucmdr.model.target import Target


# Attribute definitions exercising every branch of the deprecation map:
# a value that is deprecated then removed, a value that is deprecated with no
# removal version, and an attribute with no deprecation map at all.
_ATTRIBUTES = {
    'widget_source': {
        'type': 'string',
        'deprecated': {
            'download-old': ('2.29.1', '2.32'),
            'download-stale': ('2.30', ''),
            'download-padded': ('2.33.0', '2.34.0'),
        },
    },
    'plain': {
        'type': 'string',
    },
}


class _FakeComponent:
    """Minimal stand-in for a model record: exposes `attributes` and item access."""
    # pylint: disable=too-few-public-methods

    def __init__(self, values, attributes=None):
        self.attributes = attributes if attributes is not None else _ATTRIBUTES
        self._values = values

    def __getitem__(self, key):
        return self._values[key]


class _DetachedExperiment:
    """Stand-in exposing only what Experiment.verify_post_install() needs.

    Avoids project storage: populate() returns a caller-supplied dict and the
    real _check_deprecated_values() is reused unchanged.
    """
    # pylint: disable=too-few-public-methods,protected-access

    _check_deprecated_values = Experiment._check_deprecated_values

    def __init__(self, populated):
        self._populated = populated

    def populate(self):
        """Return the pre-built target/application/measurement mapping."""
        return self._populated


def _detached_target(**fields):
    """Build a Target record that is not backed by any storage container."""
    return Target(StorageRecord(None, None, fields))


class ExperimentDeprecationTest(tests.TestCase):
    """Tests for version-gated deprecation checks of model attribute values."""
    # pylint: disable=protected-access

    @staticmethod
    def _check(comp, tau_ver):
        # _check_deprecated_values() does not use `self`, so no Experiment instance is needed.
        Experiment._check_deprecated_values(None, comp, tau_ver=tau_ver)

    def test_removed_value_raises(self):
        """Value at or past its removal version raises ConfigurationError naming the flag."""
        comp = _FakeComponent({'widget_source': 'download-old'})
        with self.assertRaises(ConfigurationError) as ctx:
            self._check(comp, (2, 32, 0))
        msg = str(ctx.exception)
        self.assertIn('download-old', msg)
        self.assertIn('--widget', msg)
        self.assertIn('removed in TAU 2.32', msg)

    def test_removed_value_boundary(self):
        """Exact removal version raises; one patch level earlier only warns."""
        comp = _FakeComponent({'widget_source': 'download-old'})
        with self.assertRaises(ConfigurationError):
            self._check(comp, (2, 32))
        with self.assertLogs(experiment.LOGGER, level='WARNING'):
            self._check(comp, (2, 31, 9))

    def test_deprecated_value_warns(self):
        """Value between deprecation and removal logs a warning and does not raise."""
        comp = _FakeComponent({'widget_source': 'download-old'})
        with self.assertLogs(experiment.LOGGER, level='WARNING') as cm:
            self._check(comp, (2, 30))
        self.assertEqual(len(cm.output), 1)
        self.assertIn('download-old', cm.output[0])
        self.assertIn('--widget', cm.output[0])
        self.assertIn('deprecated since TAU 2.29.1', cm.output[0])

    def test_deprecated_without_removal_never_raises(self):
        """Empty removal version means the value is never removed, only warned about."""
        comp = _FakeComponent({'widget_source': 'download-stale'})
        with self.assertLogs(experiment.LOGGER, level='WARNING'):
            self._check(comp, (99, 0))

    def test_value_before_deprecation_is_silent(self):
        """Value used with a TAU older than its deprecation version produces no output."""
        comp = _FakeComponent({'widget_source': 'download-old'})
        with mock.patch.object(experiment.LOGGER, 'warning') as warn:
            self._check(comp, (2, 29, 0))
        warn.assert_not_called()

    def test_undeprecated_value_is_silent(self):
        """Value absent from the deprecation map is accepted at any TAU version."""
        comp = _FakeComponent({'widget_source': 'download'})
        with mock.patch.object(experiment.LOGGER, 'warning') as warn:
            self._check(comp, (99, 0))
        warn.assert_not_called()

    def test_unset_attribute_is_skipped(self):
        """Attribute with a deprecation map but no value on the record is ignored."""
        comp = _FakeComponent({'plain': 'download-old'})
        with mock.patch.object(experiment.LOGGER, 'warning') as warn:
            self._check(comp, (99, 0))
        warn.assert_not_called()

    def test_removal_threshold_longer_than_installed(self):
        """Installed '2.34' must count as removed at '2.34.0'; shorter tuple padded, not ranked lower."""
        comp = _FakeComponent({'widget_source': 'download-padded'})
        with self.assertRaises(ConfigurationError):
            self._check(comp, (2, 34))

    def test_deprecation_threshold_longer_than_installed(self):
        """Installed '2.33' must count as deprecated at '2.33.0'."""
        comp = _FakeComponent({'widget_source': 'download-padded'})
        with self.assertLogs(experiment.LOGGER, level='WARNING'):
            self._check(comp, (2, 33))

    def test_padded_compare_below_removal(self):
        """Installed '2.33.9' is deprecated but not yet removed at '2.34.0'."""
        comp = _FakeComponent({'widget_source': 'download-padded'})
        with self.assertLogs(experiment.LOGGER, level='WARNING'):
            self._check(comp, (2, 33, 9))

    def test_version_ge_pads_to_common_width(self):
        """_version_ge() zero-pads whichever side is shorter, for any component count."""
        self.assertTrue(experiment._version_ge((2, 34), (2, 34, 0)))
        self.assertTrue(experiment._version_ge((2, 34, 0), (2, 34)))
        self.assertTrue(experiment._version_ge((2, 35, 1, 1), (2, 35, 1)))
        self.assertFalse(experiment._version_ge((2, 35), (2, 35, 0, 1)))
        self.assertFalse(experiment._version_ge((2, 33, 9), (2, 34)))

    def test_multiple_components_checked(self):
        """Every component passed is inspected, not just the first."""
        clean = _FakeComponent({'widget_source': 'download'})
        removed = _FakeComponent({'widget_source': 'download-old'})
        with self.assertRaises(ConfigurationError):
            Experiment._check_deprecated_values(None, clean, removed, tau_ver=(2, 35))

    def test_target_ompt_source_tr4_tr6_removed(self):
        """Real Target attributes: download-tr4/tr6 are removed in TAU 2.32."""
        for value in ('download-tr4', 'download-tr6'):
            targ = _detached_target(ompt_source=value)
            with self.assertRaises(ConfigurationError) as ctx:
                self._check(targ, (2, 35, 1))
            self.assertIn(value, str(ctx.exception))
            self.assertIn('--ompt', str(ctx.exception))

    def test_target_ompt_source_tr4_deprecated(self):
        """Real Target attributes: download-tr4 only warns on TAU 2.29.1 through 2.31.x."""
        targ = _detached_target(ompt_source='download-tr4')
        with self.assertLogs(experiment.LOGGER, level='WARNING') as cm:
            self._check(targ, (2, 31))
        self.assertIn('--ompt', cm.output[0])

    def test_target_ompt_source_download_accepted(self):
        """Real Target attributes: plain 'download' is neither deprecated nor removed."""
        targ = _detached_target(ompt_source='download')
        with mock.patch.object(experiment.LOGGER, 'warning') as warn:
            self._check(targ, (2, 35, 1))
        warn.assert_not_called()

    def test_verify_post_install_checks_populated_components(self):
        """verify_post_install() runs the deprecation check on target, application, and measurement."""
        clean = _FakeComponent({'widget_source': 'download'})
        populated = {'target': _detached_target(ompt_source='download-tr6'),
                     'application': clean,
                     'measurement': clean}
        with self.assertRaises(ConfigurationError):
            Experiment.verify_post_install(_DetachedExperiment(populated), (2, 35, 1))

    def test_verify_post_install_passes_clean_components(self):
        """verify_post_install() is silent when no component uses a deprecated value."""
        clean = _FakeComponent({'widget_source': 'download'})
        populated = {'target': _detached_target(ompt_source='download'),
                     'application': clean,
                     'measurement': clean}
        with mock.patch.object(experiment.LOGGER, 'warning') as warn:
            Experiment.verify_post_install(_DetachedExperiment(populated), (2, 35, 1))
        warn.assert_not_called()
