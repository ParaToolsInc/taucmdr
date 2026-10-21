#
# Copyright (c) 2016-2026, ParaTools, Inc.
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

import io
import os
import shlex
import tarfile
import tempfile
import warnings
from unittest import mock
from taucmdr import util, tests


def _make_archive(path, links):
    """Write a gzipped tar file with ``pkg/file.txt`` and the symbolic links `links` ({name: target}) in ``pkg/``."""
    with tarfile.open(path, 'w:gz') as tar:
        info = tarfile.TarInfo('pkg')
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        tar.addfile(info)
        data = b'hello\n'
        info = tarfile.TarInfo('pkg/file.txt')
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
        for name, target in links.items():
            info = tarfile.TarInfo('pkg/' + name)
            info.type = tarfile.SYMTYPE
            info.linkname = target
            tar.addfile(info)
    return path


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


class ExtractArchiveTest(tests.TestCase):
    """Tests for :any:`util.extract_archive`."""

    def test_extract_archive(self):
        """Extracting an archive creates its top-level directory, without deprecation warnings."""
        archive = _make_archive(os.path.join(os.getcwd(), 'good.tgz'), {'link.txt': 'file.txt'})
        dest = tempfile.mkdtemp(dir=os.getcwd())
        with warnings.catch_warnings():
            warnings.simplefilter('error', DeprecationWarning)
            topdir = util.extract_archive(archive, dest, show_progress=False)
        self.assertEqual(topdir, os.path.join(dest, 'pkg'))
        with open(os.path.join(topdir, 'link.txt'), encoding='utf-8') as fin:
            self.assertEqual(fin.read(), 'hello\n')

    @tests.skipUnless(hasattr(tarfile, 'data_filter'), "tarfile extraction filters required")
    def test_extract_archive_unsafe_link(self):
        """An archive with a link that points outside the destination raises OSError and isn't extracted."""
        archive = _make_archive(os.path.join(os.getcwd(), 'unsafe.tgz'), {'passwd': '/etc/passwd'})
        dest = tempfile.mkdtemp(dir=os.getcwd())
        with self.assertRaises(OSError):
            util.extract_archive(archive, dest, show_progress=False)
        self.assertFalse(os.path.lexists(os.path.join(dest, 'pkg', 'passwd')))


    def test_extract_archive_truncated(self):
        """A truncated archive, such as an interrupted download, raises OSError."""
        # Create a tarfile, truncate it, and then attempt to extract it, requiring
        # that OSError is raised.
        for with_dir in True, False:
            path = os.path.join(os.getcwd(), f'truncated-{with_dir}.tgz')
            with tarfile.open(path, 'w:gz') as tar:
                if with_dir:
                    info = tarfile.TarInfo('pkg')
                    info.type = tarfile.DIRTYPE
                    tar.addfile(info)
                data = os.urandom(64 * 1024)
                info = tarfile.TarInfo('pkg/data.bin')
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
            with open(path, 'r+b') as fout:
                fout.truncate(os.path.getsize(path) // 2)
            for show_progress in False, True:
                with self.subTest(with_dir=with_dir, show_progress=show_progress):
                    dest = tempfile.mkdtemp(dir=os.getcwd())
                    with self.assertRaises(OSError):
                        util.extract_archive(path, dest, show_progress=show_progress)


class RmtreeTest(tests.TestCase):
    """Tests for :any:`util.rmtree`."""

    def test_onexc(self):
        """rmtree passes each failure's exception to `onexc`, without deprecation warnings."""
        path = tempfile.mkdtemp(dir=os.getcwd())
        with open(os.path.join(path, 'file'), 'w', encoding='utf-8'):
            pass
        failures = []
        with mock.patch('os.unlink', side_effect=PermissionError('not allowed')), warnings.catch_warnings():
            warnings.simplefilter('error', DeprecationWarning)
            util.rmtree(path, onexc=lambda function, failed, exc: failures.append(exc), attempts=1)
        self.assertTrue(failures)
        self.assertIsInstance(failures[0], PermissionError)


class PageOutputTest(tests.TestCase):
    """Tests for :any:`util.page_output`."""

    def test_page_output_uses_pager(self):
        """The text goes to the pager command in ``PAGER``, which may have arguments and a path with a space."""
        pager_dir = tempfile.mkdtemp(prefix='with space', dir=os.getcwd())
        paged = os.path.join(pager_dir, 'paged')
        script = os.path.join(pager_dir, 'pager.sh')
        with open(script, 'w', encoding='utf-8') as fout:
            fout.write('cat > "$1"\n')
        with mock.patch.dict(os.environ, {'PAGER': f'sh {shlex.quote(script)} {shlex.quote(paged)}'}):
            del os.environ['__TAUCMDR_DISABLE_PAGER__']
            util.page_output('h\u00e9llo pager')
        with open(paged, encoding='utf-8') as fin:
            self.assertEqual(fin.read(), 'hello pager')
