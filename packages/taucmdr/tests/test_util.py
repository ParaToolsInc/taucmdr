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


class VerifyArchiveTest(tests.TestCase):
    """Tests for :any:`util.verify_archive`."""

    def test_verify_archive_truncated(self):
        """An archive cut short after its first members is refused, though its top-level directory can be read."""
        path = os.path.join(os.getcwd(), 'large.tgz')
        with tarfile.open(path, 'w:gz') as tar:
            info = tarfile.TarInfo('pkg')
            info.type = tarfile.DIRTYPE
            tar.addfile(info)
            data = os.urandom(512 * 1024)
            info = tarfile.TarInfo('pkg/data.bin')
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        util.verify_archive(path)
        with open(path, 'r+b') as fout:
            fout.truncate(os.path.getsize(path) * 3 // 4)
        self.assertEqual(util.archive_toplevel(path), 'pkg')
        with self.assertRaises(OSError):
            util.verify_archive(path)


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


class TemporaryDirectoryTest(tests.TestCase):
    """Tests for :any:`util.mkdtemp`, :any:`util.cleanup_dtemp` and :any:`util.tmpfs_prefix`."""

    def _run_python(self, code, tmpdir):
        user_prefix = tempfile.mkdtemp(dir=os.getcwd())
        env = dict(tests.storage_env(os.environ.get('__TAUCMDR_DB_BACKEND__'), user_prefix), TMPDIR=tmpdir)
        return tests.run_python_subprocess(['-X', 'dev', '-c', code], env=env, cwd=os.getcwd())

    def test_leftover_dtemp_cleaned_at_exit(self):
        """A directory from mkdtemp that's never cleaned up is deleted at exit without a warning."""
        tmpdir = tempfile.mkdtemp(dir=os.getcwd())
        proc = self._run_python('from taucmdr import util\nprint(util.mkdtemp().name)\n', tmpdir)
        self.assertSucceeded(proc)
        path = proc.stdout.strip().splitlines()[-1]
        self.assertTrue(path.startswith(tmpdir), proc.stdout)
        self.assertFalse(os.path.exists(path))
        self.assertNotIn('Implicitly cleaning up', proc.stdout + proc.stderr)

    def test_error_dir_kept_at_exit(self):
        """A directory on the error stack is copied to the temporary directory at exit."""
        tmpdir = tempfile.mkdtemp(dir=os.getcwd())
        code = ("import os\n"
                "from taucmdr import util\n"
                "build = os.path.join(util.mkdtemp().name, 'build')\n"
                "os.mkdir(build)\n"
                "open(os.path.join(build, 'marker'), 'w').close()\n"
                "util.add_error_stack(build)\n")
        proc = self._run_python(code, tmpdir)
        self.assertSucceeded(proc)
        self.assertTrue(os.path.exists(os.path.join(tmpdir, 'build', 'marker')), proc.stdout + proc.stderr)
        self.assertNotIn('Implicitly cleaning up', proc.stdout + proc.stderr)

    def test_error_dir_copy_failure_at_exit(self):
        """A copy of an error directory that fails doesn't stop the exit hook from deleting the other directories."""
        tmpdir = tempfile.mkdtemp(dir=os.getcwd())
        os.mkdir(os.path.join(tmpdir, 'build'))
        code = ("import os\n"
                "from taucmdr import util\n"
                "build = os.path.join(util.mkdtemp().name, 'build')\n"
                "os.mkdir(build)\n"
                "util.add_error_stack(build)\n"
                "print(util.mkdtemp().name)\n")
        proc = self._run_python(code, tmpdir)
        self.assertSucceeded(proc)
        leftover = proc.stdout.splitlines()[0]
        self.assertTrue(leftover.startswith(tmpdir), proc.stdout)
        self.assertFalse(os.path.exists(leftover))
        self.assertNotIn('Implicitly cleaning up', proc.stdout + proc.stderr)

    @staticmethod
    def _record_mkdtemp(made):
        real_mkdtemp = util.mkdtemp
        def record(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            made.append(path)
            return path
        return mock.patch.object(util, 'mkdtemp', side_effect=record)

    def test_tmpfs_prefix_rejected_candidate_removed(self):
        """A candidate that can't run executables is deleted."""
        made = []
        real_check_call = util.subprocess.check_call
        calls = []
        def check_call(*args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                raise util.subprocess.CalledProcessError(1, args[0])
            return real_check_call(*args, **kwargs)
        with self._record_mkdtemp(made), mock.patch('taucmdr.util.subprocess.check_call', side_effect=check_call):
            prefix = util.tmpfs_prefix()
        self.addCleanup(lambda: util.cleanup_dtemp(prefix))
        self.assertGreater(len(made), 1)
        self.assertIs(prefix, made[-1])
        self.assertFalse(os.path.exists(made[0].name))
        self.assertNotIn(made[0], util._DTEMP_STACK)  # pylint: disable=protected-access

    def test_tmpfs_prefix_fallback_kept(self):
        """When free space can't be counted, the first usable candidate is kept and the others are deleted."""
        made = []
        with self._record_mkdtemp(made), mock.patch('taucmdr.util.os.statvfs', side_effect=OSError('no statvfs')):
            prefix = util.tmpfs_prefix()
        self.addCleanup(lambda: util.cleanup_dtemp(prefix))
        self.assertEqual([path for path in made if os.path.isdir(path.name)], [prefix])
        for path in made:
            if path is not prefix:
                self.assertNotIn(path, util._DTEMP_STACK)  # pylint: disable=protected-access

    def test_cleanup_dtemp(self):
        """cleanup_dtemp deletes a directory whether or not mkdtemp made it."""
        path = util.mkdtemp(dir=os.getcwd())
        util.cleanup_dtemp(path)
        self.assertFalse(os.path.exists(path.name))
        self.assertNotIn(path, util._DTEMP_STACK)  # pylint: disable=protected-access
        path = tempfile.TemporaryDirectory(dir=os.getcwd())  # pylint: disable=consider-using-with
        util.cleanup_dtemp(path)
        self.assertFalse(os.path.exists(path.name))

    def test_dtemp_error_warning_names_paths(self):
        """The exit hook's warning gives the full path of each directory it kept."""
        build = os.path.join(tempfile.mkdtemp(dir=os.getcwd()), 'build')
        os.mkdir(build)
        dest = tempfile.mkdtemp(dir=os.getcwd())
        with mock.patch.object(util, '_DTEMP_ERROR_STACK', [build]), mock.patch.object(util, '_DTEMP_STACK', []), \
                mock.patch.object(tempfile, 'tempdir', dest), self.assertLogs(util.LOGGER, 'WARNING') as logs:
            util._cleanup_dtemp()  # pylint: disable=protected-access
        self.assertIn(os.path.join(dest, 'build'), '\n'.join(logs.output))
