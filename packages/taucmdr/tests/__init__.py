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
"""Unit test initializations and utility functions."""

from __future__ import print_function

import os
import sys
import glob
import shutil
import atexit
import tempfile
import unittest
from unittest import skipIf, skipUnless
from taucmdr.util import get_command_output
import warnings
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from taucmdr import logger, TAUCMDR_HOME, EXIT_SUCCESS, EXIT_FAILURE
from taucmdr.error import ConfigurationError
from taucmdr.cf.compiler import InstalledCompiler
from taucmdr.cf.storage.levels import PROJECT_STORAGE, USER_STORAGE, SYSTEM_STORAGE

_DIR_STACK = []
_CWD_STACK = []
_TEMPDIR_STACK = []
_NOT_IMPLEMENTED = []


def _destroy_test_workdir(path):
    onerror = lambda f, p, e: sys.stderr.write("\nERROR: Failed to clean up testing directory %s\n" % p)
    shutil.rmtree(path, ignore_errors=False, onerror=onerror)

def push_test_workdir():
    """Create a new working directory for a unit test.

    Sets the current working directory and :any:`tempfile.tempdir` to the newly created test directory.

    Directories created via this method are tracked.  If any of them exist when the program exits then
    an error message is shown for each.
    """
    path = tempfile.mkdtemp()
    try:
        test_src = os.path.join(TAUCMDR_HOME, '.testfiles', 'foo_launcher')
        test_dst = os.path.join(path, 'foo_launcher')
        shutil.copy(test_src, test_dst)
        get_command_output('%s/foo_launcher' %path)
    except OSError:
        shutil.rmtree(path)
        path = tempfile.mkdtemp(dir=os.getcwd())
    _DIR_STACK.append(path)
    _CWD_STACK.append(os.getcwd())
    _TEMPDIR_STACK.append(tempfile.tempdir)
    os.chdir(path)
    tempfile.tempdir = path

def pop_test_workdir():
    """Recursively deletes the most recently created unit test working directory.

    Restores the current working directory and :any:`tempfile.tempdir` to their values before
    :any:`push_test_workdir` was called.
    """
    tempfile.tempdir = _TEMPDIR_STACK.pop()
    os.chdir(_CWD_STACK.pop())
    _destroy_test_workdir(_DIR_STACK.pop())

def get_test_workdir():
    """Return the current unit test's working directory."""
    return _DIR_STACK[0]

def cleanup():
    """Checks that any files or directories created during testing have been removed."""
    if _DIR_STACK:
        for path in _DIR_STACK:
            sys.stderr.write("\nWARNING: Test directory '%s' still exists, attempting to clean now...\n" % path)
            _destroy_test_workdir(path)
atexit.register(cleanup)


def not_implemented(cls):
    """Decorator for TestCase classes to indicate that the tests have not been written (yet)."""
    msg = "%s: tests have not been implemented" % cls.__name__
    _NOT_IMPLEMENTED.append(msg)
    return unittest.skip(msg)(cls)

def _null_decorator(_):
    return _

def skipUnlessHaveCompiler(role):
    """Decorator to skip test functions when no compiler fills the given role.

    If no installed compiler can fill this role then skip the test and report "<role> compiler not found".

    Args:
        role (_CompilerRole): A compiler role.
    """
    # pylint: disable=invalid-name
    try:
        InstalledCompiler.find_any(role)
    except ConfigurationError:
        return unittest.skip("%s compiler not found" % role)
    return _null_decorator


class TestCase(unittest.TestCase):
    """Base class for unit tests.

    Performs tests in a temporary directory and reconfigures :any:`taucmdr.logger` to work with :any:`unittest`.
    """
    # Follow the :any:`unittest` code style.
    # pylint: disable=invalid-name

    @classmethod
    def setUpClass(cls):
        push_test_workdir()
        # Reset stdout logger handler to use buffered unittest stdout
        # pylint: disable=protected-access
        cls._orig_stream = logger._STDOUT_HANDLER.stream
        logger._STDOUT_HANDLER.stream = sys.stdout

    @classmethod
    def tearDownClass(cls):
        PROJECT_STORAGE.destroy(ignore_errors=True)
        # Reset stdout logger handler to use original stdout
        # pylint: disable=protected-access
        logger._STDOUT_HANDLER.stream = cls._orig_stream
        pop_test_workdir()

    def run(self, result=None):
        # Whenever running a test, set the terminal size large enough to avoid any regex failures due to line wrap
        logger.TERM_SIZE=(150,150)
        logger.LINE_WIDTH=logger.TERM_SIZE[0]
        logger._STDOUT_HANDLER.setFormatter(logger.LogFormatter(line_width=logger.LINE_WIDTH, printable_only=True))
        # Nasty hack to give us access to what sys.stderr becomes when unittest.TestRunner.buffered == True
        # pylint: disable=attribute-defined-outside-init
        assert result is not None
        self._result_stream = result.stream
        return super(TestCase, self).run(result)

    def reset_project_storage(self, init_args=None):
        """Delete and recreate project storage.

        Effectively the same as::

            > rm -rf .tau
            > tau initialize [init_args]

        Args:
            init_args (list): Command line arguments to `tau initialize`.
        """
        from taucmdr.cli.commands.initialize import COMMAND as initialize_cmd
        PROJECT_STORAGE.destroy(ignore_errors=True)
        argv = ['--project-name', 'proj1', '--target-name', 'targ1', '--application-name', 'app1', '--tau', 'nightly']
        if init_args is not None:
            argv.extend(init_args)
        if '--bare' in argv or os.path.exists(os.path.join(SYSTEM_STORAGE.prefix, 'tau')):
            initialize_cmd.main(argv)
        else:
            # If this is the first time setting up TAU and dependencies then we need to emit output so
            # CI drivers like Travis don't think our unit tests have stalled.
            import time
            import threading
            def worker():
                initialize_cmd.main(argv)
            thread = threading.Thread(target=worker)
            tstart = time.time()
            thread.start()
            self._result_stream.write("\nInitializing TAU and dependencies:\n")
            self._result_stream.write("    @SYSTEM='%s'\n" % SYSTEM_STORAGE.prefix)
            self._result_stream.write("    @USER='%s'\n" % USER_STORAGE.prefix)
            while thread.is_alive():
                time.sleep(5)
                self._result_stream.write('.')
            elapsed = time.time() - tstart
            self._result_stream.writeln('\nTAU initialized in %s seconds' % elapsed)

    def destroy_project_storage(self):
        """Delete project storage.

        Effectively the same as::

            > rm -rf .tau
        """
        PROJECT_STORAGE.destroy(ignore_errors=True)

    def exec_command(self, cmd, argv):
        """Execute a tau command's main() routine and return the exit code, stdout, and stderr data.

        Args:
            cmd (type): A command instance that has a `main` callable attribute.
            argv (list): Arguments to pass to cmd.main()

        Returns:
            tuple: (retval, stdout, stderr) results of running the command.
        """
        # pylint: disable=protected-access
        stdout = StringIO()
        stderr = StringIO()
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        try:
            sys.stdout = stdout
            sys.stderr = stderr
            logger._STDOUT_HANDLER.stream = stdout
            try:
                retval = cmd.main(argv)
            except SystemExit as err:
                retval = err.code
            stdout_value = stdout.getvalue()
            stderr_value = stderr.getvalue()
            orig_stdout.write(stdout_value)
            orig_stderr.write(stderr_value)
            return retval, stdout_value, stderr_value
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            logger._STDOUT_HANDLER.stream = orig_stdout

    def copy_testfile(self, src, dst=None):
        test_src = os.path.join(TAUCMDR_HOME, '.testfiles', src)
        test_dst = os.path.join(get_test_workdir(), dst or src)
        shutil.copy(test_src, test_dst)

    def assertCompiler(self, role, target_name='targ1'):
        from taucmdr.model.target import Target
        targ_ctrl = Target.controller(PROJECT_STORAGE)
        targ = targ_ctrl.one({'name': target_name})
        try:
            return targ.populate(role.keyword)['path']
        except KeyError:
            self.fail("No %s compiler in target '%s'" % (role, target_name))

    def assertCommandReturnValue(self, return_value, cmd, argv):
        retval, stdout, stderr = self.exec_command(cmd, argv)
        self.assertEqual(retval, return_value)
        return stdout, stderr

    def assertNotCommandReturnValue(self, return_value, cmd, argv):
        retval, stdout, stderr = self.exec_command(cmd, argv)
        self.assertNotEqual(retval, return_value)
        return stdout, stderr

    def assertManagedBuild(self, return_value, compiler_role, compiler_args, src):
        from taucmdr.cli.commands.build import COMMAND as build_command
        self.copy_testfile(src)
        cc_cmd = self.assertCompiler(compiler_role)
        args = [cc_cmd] + compiler_args + [src]
        self.assertCommandReturnValue(return_value, build_command, args)

    def assertInLastTrialData(self, value, data_type='tau'):
        from taucmdr.model.project import Project
        trial = Project.selected().experiment().trials()
        data_files = trial[0].get_data_files()
        if data_type == 'tau':
            data = []
            for profile_file in glob.glob(os.path.join(data_files['tau'], 'profile.*.*.*')):
                with open(profile_file) as fin:
                    buff = fin.read()
                    if value in buff:
                        return
                    data.append(buff)
        else:
            raise NotImplementedError
        self.fail("'%s' not found in '%s'" % (value, '\n'.join(data)))


class TestRunner(unittest.TextTestRunner):
    """Test suite runner."""

    def __init__(self, *args, **kwargs):
        super(TestRunner, self).__init__(*args, **kwargs)
        self.buffer = True

    def run(self, test):
        print("Running tests with TinyDB backend")
        PROJECT_STORAGE.set_backend('tinydb')
        result_tinydb = super(TestRunner, self).run(test)

        print("Running tests with SQLite backend")
        PROJECT_STORAGE.set_backend('sqlite')
        result_sqlite = super(TestRunner, self).run(test)

        for item in _NOT_IMPLEMENTED:
            print("WARNING: %s" % item)
        if result_tinydb.wasSuccessful() and result_sqlite.wasSuccessful():
            return EXIT_SUCCESS
        return EXIT_FAILURE
