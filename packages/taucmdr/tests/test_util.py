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

Functions used for unit tests of util.py.
"""


from taucmdr import util, tests


class HumanSizeTest(tests.TestCase):
    """Class to test the human_size function in utils."""

    def test_humansize(self):
        self.assertEqual(util.human_size(20000000), '19.1MiB')
        with self.assertRaises(TypeError):
            util.human_size('abc')


class ParseBoolTest(tests.TestCase):
    """Class to test the parse_bool function in utils."""

    def test_true(self):
        self.assertTrue(util.parse_bool('yes'))
        with self.assertRaises(TypeError):
            util.parse_bool('ye')

    def test_false(self):
        self.assertFalse(util.parse_bool('off'))
        with self.assertRaises(TypeError):
            util.parse_bool('offf')

    def test_extendtrue(self):
        self.assertTrue(util.parse_bool('2', ['correct', '2', '3', '4', '5'], ['incorrect']))
        with self.assertRaises(TypeError):
            util.parse_bool('6')

    def test_extendfalse(self):
        self.assertFalse(util.parse_bool('incorrect', ['correct', '2', '3', '4', '5'], ['incorrect']))
        with self.assertRaises(TypeError):
            util.parse_bool('incorect')


class IsUrlTest(tests.TestCase):
    """Class to test the is_url function in utils."""

    def test_true(self):
        self.assertTrue(util.is_url("http://www.paratools.com"))

    def test_false(self):
        self.assertFalse(util.is_url("www.paratools.com"))


class CamelCaseTest(tests.TestCase):
    """Class to test the camelcase function in utils."""

    def test_camelcase(self):
        self.assertEqual(util.camelcase("abc_def_ghi"), "AbcDefGhi")


class IsCleanContainerTest(tests.TestCase):
    """Class to test checking whether containers contain disallowed binary data."""

    def test_true(self):
        """Ensure that valid containers and other items are not flagged as being bad."""
        good_dict = {1: True,
                     'this': 'that',
                     'entry': {
                         'item1': 'dog',
                         'list1': [1.0, 2.0, 3.0],
                         'bools': (True, False)
                     },
                     'empty': None,
                     ('tuple', 'keyed'): 'allowed'
                     }
        self.assertTrue(util.is_clean_container(good_dict))
        self.assertTrue(util.is_clean_container({}))
        self.assertTrue(util.is_clean_container(None))
        self.assertTrue(util.is_clean_container([]))
        self.assertTrue(util.is_clean_container(()))
        self.assertTrue(util.is_clean_container(1))
        self.assertTrue(util.is_clean_container(1.0))
        self.assertTrue(util.is_clean_container(False))
        self.assertTrue(util.is_clean_container("string"))
        self.assertTrue(util.is_clean_container(("tuple", 1)))
        self.assertTrue(util.is_clean_container([{}, {}]))
        self.assertTrue(util.is_clean_container(["something", None, {"dict": "value"}, (1, "entry")]))

    def test_false(self):
        """Ensure that bytes, bytearray and memoryview objects in keys and values are detected."""
        bytes_in_key = {'this': 'that', 'dict': {'good': 1, ('ok', b'bad'): 'bytes!'}}
        bytes_in_value = {'this': 'that', 'dict': {
            'good': 1, 'rhyme': [
                ('one', 'fish'),
                ('two', 'fish'),
                ('red', 'fish'),
                ('blue', 'fish')
                ]
            },
            'bad': [1, True, b'Value!!', 2.0, 'string']
        }
        self.assertFalse(util.is_clean_container(b'bad string'))
        self.assertFalse(util.is_clean_container(bytes_in_key))
        self.assertFalse(util.is_clean_container(bytes_in_value))
        self.assertFalse(util.is_clean_container({"key": bytearray(b"bad value")}))
        self.assertFalse(util.is_clean_container(('some', 1, b'tuple')))
        self.assertFalse(util.is_clean_container(['some', True, bytearray(b'list')]))
        self.assertFalse(util.is_clean_container({'key': [{b'bad value', 'good value'}]}))
