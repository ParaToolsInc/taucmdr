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

Functions used for unit tests of arguments.py.
"""

import os
import argparse
from taucmdr import tests
from taucmdr.cli.arguments import ParsePackagePathAction, ParseBooleanAction


class ParsePackagePathActionTest(tests.TestCase):
    """Tests for the --<package> argument action shared by every software package option."""

    def setUp(self):
        super().setUp()
        self._action = ParsePackagePathAction(option_strings=['--widget'], dest='widget')
        self._namespace = argparse.Namespace()

    def _parse(self, value):
        self._action(None, self._namespace, value)
        return getattr(self._namespace, self._action.dest)

    def test_keywords(self):
        """'download' and 'nightly' are accepted in any case and normalized to lower case."""
        self.assertEqual(self._parse('download'), 'download')
        self.assertEqual(self._parse('DOWNLOAD'), 'download')
        self.assertEqual(self._parse('nightly'), 'nightly')

    def test_false_disables_package(self):
        """Any false-ish value disables the package."""
        for value in ('None', 'false', 'F', 'no', '0'):
            self.assertIsNone(self._parse(value))

    def test_rejected_keywords(self):
        """Values listed in `rejected` are refused with the given reason, regardless of case."""
        action = ParsePackagePathAction(option_strings=['--widget'], dest='widget',
                                        rejected={'download-old': "is no longer supported. Use 'download' instead."})
        for value in ('download-old', 'Download-OLD'):
            with self.assertRaises(argparse.ArgumentError) as ctx:
                action(None, self._namespace, value)
            self.assertIn("'%s' is no longer supported" % value, str(ctx.exception))
            self.assertIn("Use 'download' instead", str(ctx.exception))

    def test_unlisted_keyword_is_a_path(self):
        """Without a `rejected` entry an unknown keyword is just a path that does not exist."""
        with self.assertRaises(argparse.ArgumentError) as ctx:
            self._parse('download-old')
        self.assertIn('Keyword, valid path, or URL required', str(ctx.exception))

    def test_url_kept_verbatim(self):
        """URLs are not touched, so nothing is checked on the local filesystem."""
        for url in ('http://example.com/widget.tgz', 'https://example.com/widget.tgz', 'ftp://example.com/w.tgz'):
            self.assertEqual(self._parse(url), url)

    def test_existing_directory_made_absolute(self):
        """A relative path to an existing directory becomes absolute."""
        os.mkdir('widget-install')
        self.assertEqual(self._parse('widget-install'), os.path.abspath('widget-install'))

    def test_existing_archive_made_absolute(self):
        """A relative path to an existing file (an archive) becomes absolute."""
        with open('widget.tgz', 'w', encoding='utf-8'):
            pass
        self.assertEqual(self._parse('widget.tgz'), os.path.abspath('widget.tgz'))

    def test_home_directory_expanded(self):
        """A leading tilde is expanded before the path is checked."""
        self.assertEqual(self._parse('~'), os.path.expanduser('~'))

    def test_missing_path_rejected(self):
        """A path that exists neither as a directory nor a readable file is rejected."""
        with self.assertRaises(argparse.ArgumentError) as ctx:
            self._parse('no/such/widget.tgz')
        self.assertIn('Keyword, valid path, or URL required', str(ctx.exception))


class ParseBooleanActionTest(tests.TestCase):
    """Tests for the T/F argument action."""

    def setUp(self):
        super().setUp()
        self._action = ParseBooleanAction(option_strings=['--flag'], dest='flag')
        self._namespace = argparse.Namespace()

    def _parse(self, value):
        self._action(None, self._namespace, value)
        return getattr(self._namespace, self._action.dest)

    def test_true_and_false_spellings(self):
        """Common spellings of true and false parse to booleans."""
        for value in ('T', 'true', 'Yes', '1', 'on'):
            self.assertIs(self._parse(value), True)
        for value in ('F', 'false', 'No', '0', 'off'):
            self.assertIs(self._parse(value), False)

    def test_other_values_rejected(self):
        """Anything else is an argument error."""
        with self.assertRaises(argparse.ArgumentError) as ctx:
            self._parse('maybe')
        self.assertIn('Boolean value required', str(ctx.exception))
