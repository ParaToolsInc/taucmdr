# -*- coding: utf-8 -*-
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

Functions used for unit tests of configuration.py.
"""
#pylint: disable=missing-docstring

import six
from taucmdr import tests, configuration
from taucmdr.cf.storage.levels import PROJECT_STORAGE, ORDERED_LEVELS
from taucmdr.cf.storage.project import ProjectStorageError

class ConfigurationTest(tests.TestCase):
       
    def test_get_unset(self):
        self.reset_project_storage(['--bare'])
        self.assertRaises(KeyError, configuration.get, key='some_key', storage=None)
    
    def test_get_unset_all_levels(self):
        self.reset_project_storage(['--bare'])
        for storage in ORDERED_LEVELS:
            self.assertRaises(KeyError, configuration.get, key='some_key', storage=storage)

    def test_get_no_project(self):
        self.destroy_project_storage()
        self.assertRaises(ProjectStorageError, configuration.get, key='some_key', storage=PROJECT_STORAGE)
        self.assertRaises(KeyError, configuration.get, key='some_key', storage=None)

    def test_put_get(self):
        self.reset_project_storage(['--bare'])
        test_key = 'test_put_get_key'
        test_value = 'test_put_get_value'
        configuration.put(test_key, test_value)
        value = configuration.get(test_key)
        self.assertEqual(test_value, value)

    def test_put_get_all_levels(self):
        self.reset_project_storage(['--bare'])
        for storage in ORDERED_LEVELS:
            test_key = 'test_put_get_all_levels_key_'+storage.name
            test_value = 'test_put_get_all_levels_value_'+storage.name
            configuration.put(test_key, test_value, storage=storage)
            value = configuration.get(test_key, storage=storage)
            self.assertEqual(test_value, value)
            for other_storage in ORDERED_LEVELS:
                if other_storage is not storage:
                    self.assertRaises(KeyError, configuration.get, key=test_key, storage=other_storage)

    def test_put_no_project(self):
        self.destroy_project_storage()
        test_key = 'test_put_no_project_key'
        test_value = 'test_put_no_project_value'
        self.assertRaises(ProjectStorageError, configuration.put, key=test_key, value=test_value)
        for storage in ORDERED_LEVELS:
            if storage is not PROJECT_STORAGE:
                test_key = 'test_put_no_project_key_'+storage.name
                test_value = 'test_put_no_project_value_'+storage.name
                configuration.put(test_key, test_value, storage=storage)
                value = configuration.get(test_key, storage=storage)
                self.assertEqual(test_value, value)
                for other_storage in ORDERED_LEVELS:
                    if other_storage not in (storage, PROJECT_STORAGE):
                        self.assertRaises(KeyError, configuration.get, key=test_key, storage=other_storage)

    def test_delete_unset(self):
        self.reset_project_storage(['--bare'])
        self.assertRaises(KeyError, configuration.delete, key='some_key', storage=None)
        
    def test_parse_config_string(self):
        def check_value_type(put_val, get_val, get_type):
            test_key = 'test_parse_config_string'
            configuration.put(test_key, put_val)
            test_value = configuration.get(test_key)
            self.assertIsInstance(test_value, get_type)
            self.assertEqual(get_val, test_value)
        self.reset_project_storage(['--bare'])
        check_value_type("True", True, bool)
        check_value_type("TRUE", True, bool)
        check_value_type("true", True, bool)
        check_value_type("False", False, bool)
        check_value_type("FALSE", False, bool)
        check_value_type("false", False, bool)
        check_value_type("15", 15, int)
        check_value_type("2.5", 2.5, float)
        check_value_type("Hello", "Hello", six.string_types)
        check_value_type("T", "T", six.string_types)
        check_value_type("F", "F", six.string_types)
        check_value_type("yes", "yes", six.string_types)
        check_value_type("no", "no", six.string_types)
