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
"""Test functions.

Functions used for unit tests of TAU Enterprise CLI commands.
"""
import unittest
import uuid
import requests
from requests.packages import urllib3
from taucmdr import tests, ENTERPRISE_URL
from taucmdr.cf.storage.tau_enterprise import _TauEnterpriseDatabase, TauEnterpriseStorage
from taucmdr.cli.commands.enterprise.connect import COMMAND as connect_cmd
from taucmdr.cli.commands.enterprise.disconnect import COMMAND as disconnect_cmd
from taucmdr.cli.commands.enterprise.purge import COMMAND as purge_cmd
from taucmdr.cli.commands.project.push import COMMAND as proj_push_cmd
from taucmdr.cli.commands.project.pull import COMMAND as proj_pull_cmd
from taucmdr.cli.commands.initialize import COMMAND as initialize_cmd
from taucmdr.error import NotConnectedError
from taucmdr.model.project import Project

_TEST_USER_NAME = "tautest"
_TEST_USER_TOKEN = "7905233407184ba9a6602cdaef7907a9"


class TauEnterpriseCLITests(tests.TestCase):
    """Unit tests for `tau enterprise`, `push`, and `pull` commands"""

    def setUp(self):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Generate a random database name so that concurrently running tests don't clobber each other.
            self.db_name = uuid.uuid4().hex[-8:]
            self.database = _TauEnterpriseDatabase(ENTERPRISE_URL, self.db_name, token=_TEST_USER_TOKEN)
            self.database.purge()
            self.storage = TauEnterpriseStorage("db_test", "")
            self.storage.connect_database(url=ENTERPRISE_URL, db_name=self.db_name, token=_TEST_USER_TOKEN)
        except (requests.ConnectionError, requests.HTTPError):
            # Don't bother running any of the tests if we can't connect to the database
            raise unittest.SkipTest

    def test_connect(self):
        self.reset_project_storage()
        stdout, stderr = self.assertCommandReturnValue(0, connect_cmd, [_TEST_USER_NAME, '--key',
                                                       _TEST_USER_TOKEN, '--db', self.db_name])
        self.assertIn('Connected project', stdout, "Expected 'Connected project' but not found")
        self.assertIn('database name %s' % self.db_name, stdout, "Wrong db name")
        self.assertFalse(stderr)
        token, db_name = Project.connected()
        self.assertEqual(token, _TEST_USER_TOKEN, "Project API key not equal to input")
        self.assertEqual(db_name, self.db_name, "Project DB Name not equal to input")

    def test_disconnect(self):
        self.test_connect()
        stdout, stderr = self.assertCommandReturnValue(0, disconnect_cmd, [])
        self.assertFalse(stderr)
        with self.assertRaises(NotConnectedError):
            Project.connected()

    def test_purge(self):
        self.test_connect()
        token, db_name = Project.connected()
        stdout, stderr = self.assertNotCommandReturnValue(0, purge_cmd, [])
        self.assertIn('--force', stderr)
        stdout, stderr = self.assertCommandReturnValue(0, purge_cmd, ['--force'])
        self.assertIn('Tables in %s purged' % db_name, stdout)
        self.assertFalse(stderr)

    def test_push(self):
        self.test_purge()
        stdout, stderr = self.assertCommandReturnValue(0, proj_push_cmd, ['proj1'])
        self.assertIn('Pushed Project', stdout)
        self.assertIn('Pushed Compiler', stdout)
        self.assertIn('Pushed Target', stdout)
        self.assertIn('Pushed Application', stdout)
        self.assertIn('Pushed Measurement', stdout)
        self.assertIn('Pushed Experiment', stdout)

    def test_push_already_present(self):
        self.test_push()
        stdout, stderr = self.assertCommandReturnValue(0, proj_push_cmd, ['proj1'])
        self.assertNotIn('Pushed Project', stdout)
        self.assertNotIn('Pushed Compiler', stdout)
        self.assertNotIn('Pushed Target', stdout)
        self.assertNotIn('Pushed Application', stdout)
        self.assertNotIn('Pushed Measurement', stdout)
        self.assertNotIn('Pushed Experiment', stdout)
        self.assertIn('Skipped Project', stdout)
        self.assertIn('Skipped Compiler', stdout)
        self.assertIn('Skipped Target', stdout)
        self.assertIn('Skipped Application', stdout)
        self.assertIn('Skipped Measurement', stdout)
        self.assertIn('Skipped Experiment', stdout)

    def test_push_wrongname(self):
        self.test_purge()
        stdout, stderr = self.assertNotCommandReturnValue(0, proj_push_cmd, ['proj2'])
        self.assertIn('No Project matching', stderr)

    def test_pull(self):
        self.test_push()
        self.destroy_project_storage()
        self.assertCommandReturnValue(0, initialize_cmd, ['--bare'])
        self.assertCommandReturnValue(0, connect_cmd, [_TEST_USER_NAME, '--key',
                                                                        _TEST_USER_TOKEN, '--db', self.db_name])
        stdout, stderr = self.assertCommandReturnValue(0, proj_pull_cmd, ['proj1'])
        self.assertIn('Pulled Project', stdout)
        self.assertIn('Pulled Compiler', stdout)
        self.assertIn('Pulled Target', stdout)
        self.assertIn('Pulled Application', stdout)
        self.assertIn('Pulled Measurement', stdout)
        self.assertIn('Pulled Experiment', stdout)

    def test_pull_already_present(self):
        self.test_pull()
        stdout, stderr = self.assertCommandReturnValue(0, proj_pull_cmd, ['proj1'])
        self.assertNotIn('Pulled Project', stdout)
        self.assertNotIn('Pulled Compiler', stdout)
        self.assertNotIn('Pulled Target', stdout)
        self.assertNotIn('Pulled Application', stdout)
        self.assertNotIn('Pulled Measurement', stdout)
        self.assertNotIn('Pulled Experiment', stdout)
        self.assertIn('Skipped Project', stdout)
        self.assertIn('Skipped Compiler', stdout)
        self.assertIn('Skipped Target', stdout)
        self.assertIn('Skipped Application', stdout)
        self.assertIn('Skipped Measurement', stdout)
        self.assertIn('Skipped Experiment', stdout)

    def test_pull_wrongname(self):
        self.test_purge()
        stdout, stderr = self.assertNotCommandReturnValue(0, proj_push_cmd, ['proj2'])
        self.assertIn('No Project matching', stderr)
