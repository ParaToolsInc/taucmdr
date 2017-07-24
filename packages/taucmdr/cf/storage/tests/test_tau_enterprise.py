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

Functions used for unit tests of tau_enterprise.py.
"""

import unittest
import requests
from taucmdr import tests
from taucmdr.cf.storage.tau_enterprise import _TauEnterpriseDatabase

_DATABASE_URL = "http://east03.paratools.com:5000"


class TauEnterpriseStorageTests(tests.TestCase):
    """Unit tests for TauEnterpriseStorage."""

    def setUp(self):
        try:
            self.database = _TauEnterpriseDatabase(_DATABASE_URL)
            self.database.purge()
        except (requests.ConnectionError, requests.HTTPError):
            # Don't bother running any of the tests if we can't connect to the database
            raise unittest.SkipTest

    def test_connect_db(self):
        self.assertEqual(self.database.status, 200,
                         "Got error connecting to database: {}.".format(self.database.status))

    def test_table_insert(self):
        self.database.purge()
        element = {'memory_alloc': False, 'sample': True, 'io': False,
                   'compiler_inst': 'never', 'heap_usage': False,
                   'throttle_per_call': 10, 'opencl': False,
                   'link_only': False, 'reuse_inst_files': False,
                   'callsite': False, 'keep_inst_files': False,
                   'comm_matrix': False, 'source_inst': 'never',
                   'cuda': False, 'profile': 'tau', 'callpath': 100,
                   'trace': 'none', 'mpi': False, 'metrics': [u'TIME'],
                   'openmp': 'ignore', 'projects': [],
                   'throttle': True, 'name': 'sample',
                   'throttle_num_calls': 100000, 'shmem': False}
        record = self.database.table('experiment').insert(element)
        self.assertNotEqual(record.eid, '')
        return record

    def test_table_get(self):
        self.database.purge()
        record_1 = self.test_table_insert()
        record_2 = self.database.table('experiment').get(eid=record_1.eid)
        self.assertDictEqual(record_1.element, record_2.element,
                             "Record retrieved from database different from record inserted.")

    def test_table_count(self):
        self.database.purge()
        table = self.database.table('compiler')
        table.insert({'path': u'/usr/bin/gcc', 'role': 'Host_CC',
                      'uid': '22bf4003', 'family': 'GNU'})
        table.insert({'path': u'/usr/bin/g++', 'role': 'Host_CXX',
                      'uid': '148623fa', 'family': 'GNU'})
        table.insert({'path': u'/usr/bin/gfortran', 'role': 'Host_FC',
                      'uid': '7e1c0e82', 'family': 'GNU'})
        family_size = table.count({'family': 'GNU'})
        self.assertEqual(family_size, 3, "Wrong count for family=GNU")
        role_count = table.count({'role': 'Host_CC'})
        self.assertEqual(role_count, 1, "Wrong count for role=Host_CC")
        nonexistent_count = table.count({'family': 'Intel'})
        self.assertEqual(nonexistent_count, 0, "Found records but no matching records should exist")

    def test_table_search(self):
        self.database.purge()
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello'}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello'}
        element_3 = {'opencl': False, 'mpc': True, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello'}
        table = self.database.table('application')
        eid_1 = table.insert(element_1).eid
        eid_2 = table.insert(element_2).eid
        eid_3 = table.insert(element_3).eid
        result = table.search({'opencl': True})
        self.assertEqual(len(result), 1, "Wrong number of results for opencl=True")
        self.assertEqual(result[0].eid, eid_2, "EIDs don't match for opencl=True")
        self.assertNotEqual(result[0].eid, eid_1, "EIDs match for wrong record for opencl=True")
        self.assertNotEqual(result[0].eid, eid_3, "EIDs match for wrong record for opencl=True")
        result = table.search({'opencl': False})
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=False")
        result = table.search({'opencl': True, 'mpc': True})
        self.assertEqual(len(result), 0, "Wrong number of results for opencl=True, mpc=True")
        result = table.search({'opencl': True, 'mpc': True}, match_any=True)
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=True, mpc=True with match_any")

    def test_table_update(self):
        self.database.purge()
        table = self.database.table('application')
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False}
        element_3 = {'opencl': True, 'mpc': True, 'pthreads': False}
        eid_1 = table.insert(element_1).eid
        eid_2 = table.insert(element_2).eid
        eid_3 = table.insert(element_3).eid
        table.update({'mpc': True}, eids=eid_1)
        updated_element_1 = table.get(eid=eid_1).element
        self.assertDictEqual(updated_element_1, element_3, "Updated element has wrong value")
        table.update({'pthreads': True}, keys={'opencl': True})
        updated_element_2 = table.get(eid=eid_2).element
        updated_element_3 = table.get(eid=eid_3).element
        self.assertTrue(updated_element_2['pthreads'], "Updated field did not change")
        self.assertTrue(updated_element_3['pthreads'], "Updated field did not change")

    def test_table_purge(self):
        self.database.purge()
        table = self.database.table('compiler')
        table.insert({'path': u'/usr/bin/gcc', 'role': 'Host_CC',
                      'uid': '22bf4003', 'family': 'GNU'})
        table.insert({'path': u'/usr/bin/g++', 'role': 'Host_CXX',
                      'uid': '148623fa', 'family': 'GNU'})
        table.insert({'path': u'/usr/bin/gfortran', 'role': 'Host_FC',
                      'uid': '7e1c0e82', 'family': 'GNU'})
        all_count = table.count({})
        self.assertEqual(all_count, 3, "After purge and insert, only just-inserted records should be present")
        table.purge()
        after_purge_count = table.count({})
        self.assertEqual(after_purge_count, 0, "After purge, table should be empty")
