#
# Copyright (c) 2020, ParaTools, Inc.
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

Functions used for unit tests of storage_dispatch.py.
"""
import os
import uuid

from taucmdr import tests
from taucmdr.cf.storage.storage_dispatch import StorageDispatch
from taucmdr.tests import get_test_workdir


class StorageDispatchTests(tests.TestCase):
    """Unit tests for SQLiteLocalFileStorage."""

    def setUp(self):
        # Generate a random database name so that concurrently running tests don't interfere.
        self.tinydb_storage = StorageDispatch(uuid.uuid4().hex[-8:], get_test_workdir())
        self.tinydb_storage.set_backend('tinydb')
        self.tinydb_storage.connect_database()
        self.sqlite_storage = StorageDispatch(uuid.uuid4().hex[-8:], get_test_workdir())
        self.sqlite_storage.set_backend('sqlite')
        self.sqlite_storage.connect_database()

    def tearDown(self):
        storage_path = self.tinydb_storage.dbfile
        self.tinydb_storage.disconnect_database()
        try:
            os.remove(storage_path)
        except OSError:
            pass
        storage_path = self.sqlite_storage.dbfile
        self.sqlite_storage.disconnect_database()
        try:
            os.remove(storage_path)
        except OSError:
            pass

    def test_sqlite_dispatch_count(self):
        self.sqlite_storage.purge(table_name='application')
        element_1 = {'name': 'hello1', 'opencl': False, 'mpc': False, 'pthreads': True}
        element_2 = {'name': 'hello2', 'opencl': True, 'mpc': False, 'pthreads': True}
        self.sqlite_storage.insert(element_1, table_name='application')
        self.sqlite_storage.insert(element_2, table_name='application')
        count = self.sqlite_storage.count(table_name='application')
        self.assertEqual(count, 2, "After purge and insert of two elements, two elements should be present")

    def test_sqlite_dispatch_storage_get(self):
        self.sqlite_storage.purge(table_name='application')
        element_1 = {'name': 'hello1', 'opencl': False, 'mpc': False, 'pthreads': True}
        element_2 = {'name': 'hello2', 'opencl': True, 'mpc': False, 'pthreads': True}
        record_1 = self.sqlite_storage.insert(element_1, table_name='application')
        record_2 = self.sqlite_storage.insert(element_2, table_name='application')
        get_result_1 = self.sqlite_storage.get(keys=record_1.eid, table_name='application')
        self.assertEqual(get_result_1.eid, record_1.eid, "EID from insert and EID get should be same")
        self.assertDictEqual(element_1, get_result_1, "Element from insert and get should be same")
        get_result_2 = self.sqlite_storage.get(keys={'opencl':True}, table_name='application')
        self.assertEqual(get_result_2.eid, record_2.eid, "EID from insert and dict get should be same")
        self.assertDictEqual(get_result_2, record_2)

    def test_sqlite_dispatch_storage_search(self):
        self.sqlite_storage.purge(table_name='application')
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello1'}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello2'}
        element_3 = {'opencl': False, 'mpc': True, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello3'}
        eid_1 = self.sqlite_storage.insert(element_1, table_name='application').eid
        eid_2 = self.sqlite_storage.insert(element_2, table_name='application').eid
        eid_3 = self.sqlite_storage.insert(element_3, table_name='application').eid
        result = self.sqlite_storage.search(keys={'opencl': True}, table_name='application')
        self.assertEqual(len(result), 1, "Wrong number of results for opencl=True")
        self.assertEqual(result[0].eid, eid_2, "EIDs don't match for opencl=True")
        self.assertNotEqual(result[0].eid, eid_1, "EIDs match for wrong record for opencl=True")
        self.assertNotEqual(result[0].eid, eid_3, "EIDs match for wrong record for opencl=True")
        result = self.sqlite_storage.search(keys={'opencl': False}, table_name='application')
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=False")
        result = self.sqlite_storage.search(keys={'opencl': True, 'mpc': True}, table_name='application')
        self.assertEqual(len(result), 0, "Wrong number of results for opencl=True, mpc=True")
        result = self.sqlite_storage.search(keys={'opencl': True, 'mpc': True}, table_name='application', match_any=True)
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=True, mpc=True with match_any")
        result= self.sqlite_storage.search(keys={'foo': 'bar'}, table_name='application')
        self.assertTrue(not result, "Search for nonexistent field should return empty")

    def test_sqlite_dispatch_storage_int_value(self):
        self.sqlite_storage.purge(table_name='test')
        eid_1 = self.sqlite_storage.insert({'a': 10}, table_name='test').eid
        eid_2 = self.sqlite_storage.insert({'a': 50}, table_name='test').eid
        eid_3 = self.sqlite_storage.insert({'b': 440}, table_name='test').eid
        result = self.sqlite_storage.search({'a': 10}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], 10, "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_sqlite_dispatch_storage_str_value(self):
        self.sqlite_storage.purge(table_name='test')
        eid_1 = self.sqlite_storage.insert({'a': 'foo'}, table_name='test').eid
        eid_2 = self.sqlite_storage.insert({'a': 'bar'}, table_name='test').eid
        eid_3 = self.sqlite_storage.insert({'b': 'baz'}, table_name='test').eid
        result = self.sqlite_storage.search({'a': 'foo'}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], 'foo', "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_sqlite_dispatch_storage_list_value(self):
        self.sqlite_storage.purge(table_name='test')
        eid_1 = self.sqlite_storage.insert({'a': ['a', 'b']}, table_name='test').eid
        eid_2 = self.sqlite_storage.insert({'a': ['b', 'c']}, table_name='test').eid
        eid_3 = self.sqlite_storage.insert({'b': ['x', 'y']}, table_name='test').eid
        result = self.sqlite_storage.search({'a': ['a', 'b']}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], ['a', 'b'], "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_sqlite_dispatch_storage_update_by_key(self):
        self.sqlite_storage.purge(table_name='updateTest')
        record_1 = self.sqlite_storage.insert({'a': ['one', 'two']}, table_name='updateTest')
        record_2 = self.sqlite_storage.insert({'a': ['three', 'four']}, table_name='updateTest')
        record_3 = self.sqlite_storage.insert({'b': ['five', 'six']}, table_name='updateTest')
        self.sqlite_storage.update({'a': ['new', 'values']}, {'a': ['one', 'two']}, table_name='updateTest')
        after_update_record_1 = self.sqlite_storage.get(keys=record_1.eid, table_name='updateTest')
        after_update_record_2 = self.sqlite_storage.get(keys=record_2.eid, table_name='updateTest')
        after_update_record_3 = self.sqlite_storage.get(keys=record_3.eid, table_name='updateTest')
        self.assertNotEqual(record_1, after_update_record_1, "After update first record should have changed")
        self.assertDictEqual(record_2, after_update_record_2, "After update non-matching record 2 should be same")
        self.assertDictEqual(record_3, after_update_record_3, "After update non-matching record 3 should be same")

    def test_sqlite_dispatch_storage_transaction(self):
        self.sqlite_storage.purge(table_name='application')
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': True,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello1'}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': True,
                     'tbb': False, 'projects': [], 'name': 'hello2'}
        element_3 = {'opencl': False, 'mpc': True, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': True, 'projects': [], 'name': 'hello3'}
        eid_1 = self.sqlite_storage.insert(element_1, table_name='application').eid
        with self.sqlite_storage as database:
            eid_2 = self.sqlite_storage.insert(element_2, table_name='application').eid
        count = self.sqlite_storage.count(table_name='application')
        self.assertEqual(count, 2, "After successful transaction, table should have two elements")
        get_eid_1 = self.sqlite_storage.get(keys=eid_1, table_name='application').eid
        self.assertEqual(eid_1, get_eid_1, "After successful transaction, element 1 should be in table")
        get_eid_2 = self.sqlite_storage.get(keys=eid_2, table_name='application').eid
        self.assertEqual(eid_2, get_eid_2, "After successful transaction, element 2 should be in table")
        try:
            with self.sqlite_storage as database:
                eid_3 = self.sqlite_storage.insert(element_3, table_name='application').eid
                raise RuntimeError
        except RuntimeError:
            pass
        count = self.sqlite_storage.count(table_name='application')
        self.assertEqual(count, 2, "After unsuccessful transaction, table should still have two elements")
        result_3 = self.sqlite_storage.get(keys=eid_3, table_name='application')
        self.assertIsNone(result_3, "After unsuccessful transaction, table should not contain element 3")

    def test_tinydb_dispatch_count(self):
        self.tinydb_storage.purge(table_name='application')
        element_1 = {'name': 'hello1', 'opencl': False, 'mpc': False, 'pthreads': True}
        element_2 = {'name': 'hello2', 'opencl': True, 'mpc': False, 'pthreads': True}
        self.tinydb_storage.insert(element_1, table_name='application')
        self.tinydb_storage.insert(element_2, table_name='application')
        count = self.tinydb_storage.count(table_name='application')
        self.assertEqual(count, 2, "After purge and insert of two elements, two elements should be present")

    def test_tinydb_dispatch_storage_get(self):
        self.tinydb_storage.purge(table_name='application')
        element_1 = {'name': 'hello1', 'opencl': False, 'mpc': False, 'pthreads': True}
        element_2 = {'name': 'hello2', 'opencl': True, 'mpc': False, 'pthreads': True}
        record_1 = self.tinydb_storage.insert(element_1, table_name='application')
        record_2 = self.tinydb_storage.insert(element_2, table_name='application')
        get_result_1 = self.tinydb_storage.get(keys=record_1.eid, table_name='application')
        self.assertEqual(get_result_1.eid, record_1.eid, "EID from insert and EID get should be same")
        self.assertDictEqual(element_1, get_result_1, "Element from insert and get should be same")
        get_result_2 = self.tinydb_storage.get(keys={'opencl': True}, table_name='application')
        self.assertEqual(get_result_2.eid, record_2.eid, "EID from insert and dict get should be same")
        self.assertDictEqual(get_result_2, record_2)

    def test_tinydb_dispatch_storage_search(self):
        self.tinydb_storage.purge(table_name='application')
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello1'}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello2'}
        element_3 = {'opencl': False, 'mpc': True, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello3'}
        eid_1 = self.tinydb_storage.insert(element_1, table_name='application').eid
        eid_2 = self.tinydb_storage.insert(element_2, table_name='application').eid
        eid_3 = self.tinydb_storage.insert(element_3, table_name='application').eid
        result = self.tinydb_storage.search(keys={'opencl': True}, table_name='application')
        self.assertEqual(len(result), 1, "Wrong number of results for opencl=True")
        self.assertEqual(result[0].eid, eid_2, "EIDs don't match for opencl=True")
        self.assertNotEqual(result[0].eid, eid_1, "EIDs match for wrong record for opencl=True")
        self.assertNotEqual(result[0].eid, eid_3, "EIDs match for wrong record for opencl=True")
        result = self.tinydb_storage.search(keys={'opencl': False}, table_name='application')
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=False")
        result = self.tinydb_storage.search(keys={'opencl': True, 'mpc': True}, table_name='application')
        self.assertEqual(len(result), 0, "Wrong number of results for opencl=True, mpc=True")
        result = self.tinydb_storage.search(keys={'opencl': True, 'mpc': True}, table_name='application', match_any=True)
        self.assertEqual(len(result), 2, "Wrong number of results for opencl=True, mpc=True with match_any")
        result = self.tinydb_storage.search(keys={'foo': 'bar'}, table_name='application')
        self.assertTrue(not result, "Search for nonexistent field should return empty")

    def test_tinydb_dispatch_storage_int_value(self):
        self.tinydb_storage.purge(table_name='test')
        eid_1 = self.tinydb_storage.insert({'a': 10}, table_name='test').eid
        eid_2 = self.tinydb_storage.insert({'a': 50}, table_name='test').eid
        eid_3 = self.tinydb_storage.insert({'b': 440}, table_name='test').eid
        result = self.tinydb_storage.search({'a': 10}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], 10, "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_tinydb_dispatch_storage_str_value(self):
        self.tinydb_storage.purge(table_name='test')
        eid_1 = self.tinydb_storage.insert({'a': 'foo'}, table_name='test').eid
        eid_2 = self.tinydb_storage.insert({'a': 'bar'}, table_name='test').eid
        eid_3 = self.tinydb_storage.insert({'b': 'baz'}, table_name='test').eid
        result = self.tinydb_storage.search({'a': 'foo'}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], 'foo', "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_tinydb_dispatch_storage_list_value(self):
        self.tinydb_storage.purge(table_name='test')
        eid_1 = self.tinydb_storage.insert({'a': ['a', 'b']}, table_name='test').eid
        eid_2 = self.tinydb_storage.insert({'a': ['b', 'c']}, table_name='test').eid
        eid_3 = self.tinydb_storage.insert({'b': ['x', 'y']}, table_name='test').eid
        result = self.tinydb_storage.search({'a': ['a', 'b']}, table_name='test')
        self.assertEqual(len(result), 1, "Result should have 1 entry")
        record = result[0]
        self.assertEqual(record['a'], ['a', 'b'], "Retrieved value should be same as stored")
        self.assertEqual(record.eid, eid_1, "Retrieved EID should be same as stored")
        self.assertNotEqual(record.eid, eid_2, "Retrieved EID should NOT be the same as a different record's EID")
        self.assertNotEqual(record.eid, eid_3, "Retrieved EID should NOT be the same as a different record's EID")

    def test_tinydb_dispatch_storage_update_by_key(self):
        self.tinydb_storage.purge(table_name='updateTest')
        record_1 = self.tinydb_storage.insert({'a': ['one', 'two']}, table_name='updateTest')
        record_2 = self.tinydb_storage.insert({'a': ['three', 'four']}, table_name='updateTest')
        record_3 = self.tinydb_storage.insert({'b': ['five', 'six']}, table_name='updateTest')
        self.tinydb_storage.update({'a': ['new', 'values']}, {'a': ['one', 'two']}, table_name='updateTest')
        after_update_record_1 = self.tinydb_storage.get(keys=record_1.eid, table_name='updateTest')
        after_update_record_2 = self.tinydb_storage.get(keys=record_2.eid, table_name='updateTest')
        after_update_record_3 = self.tinydb_storage.get(keys=record_3.eid, table_name='updateTest')
        self.assertNotEqual(record_1, after_update_record_1, "After update first record should have changed")
        self.assertDictEqual(record_2, after_update_record_2, "After update non-matching record 2 should be same")
        self.assertDictEqual(record_3, after_update_record_3, "After update non-matching record 3 should be same")

    def test_tinydb_dispatch_storage_transaction(self):
        self.tinydb_storage.purge(table_name='application')
        element_1 = {'opencl': False, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': True,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': False, 'projects': [], 'name': 'hello1'}
        element_2 = {'opencl': True, 'mpc': False, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': True,
                     'tbb': False, 'projects': [], 'name': 'hello2'}
        element_3 = {'opencl': False, 'mpc': True, 'pthreads': False,
                     'shmem': False, 'mpi': False, 'cuda': False,
                     'linkage': 'dynamic', 'openmp': False,
                     'tbb': True, 'projects': [], 'name': 'hello3'}
        eid_1 = self.tinydb_storage.insert(element_1, table_name='application').eid
        with self.tinydb_storage as database:
            eid_2 = self.tinydb_storage.insert(element_2, table_name='application').eid
        count = self.tinydb_storage.count(table_name='application')
        self.assertEqual(count, 2, "After successful transaction, table should have two elements")
        get_eid_1 = self.tinydb_storage.get(keys=eid_1, table_name='application').eid
        self.assertEqual(eid_1, get_eid_1, "After successful transaction, element 1 should be in table")
        get_eid_2 = self.tinydb_storage.get(keys=eid_2, table_name='application').eid
        self.assertEqual(eid_2, get_eid_2, "After successful transaction, element 2 should be in table")
        try:
            with self.tinydb_storage as database:
                eid_3 = database.insert(element_3, table_name='application').eid
                raise RuntimeError
        except RuntimeError:
            pass
        count = self.tinydb_storage.count(table_name='application')
        self.assertEqual(count, 2, "After unsuccessful transaction, table should still have two elements")
        result_3 = self.tinydb_storage.get(keys=eid_3, table_name='application')
        self.assertIsNone(result_3, "After unsuccessful transaction, table should not contain element 3")
