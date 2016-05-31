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

import os
import sys
import shutil
import atexit
import tempfile
import unittest
import warnings
from tau import logger
import tau
from tau.cli.commands import initialize
from tau.storage.levels import PROJECT_STORAGE

_DIR_STACK = []
_CWD_STACK = []
_TEMPDIR_STACK = []
_NOT_IMPLEMENTED = []
_SYSTEM_DIR = None

def get_stdout():
    """Get data written to unit test stdout.
    
    :any:`unittest` replaces sys.stdout with a StringIO instance when running in buffered mode.
    
    Returns:
        str: Data written to sys.stdout while the test was running.
    """
    # unittest replaces sys.stdout and sys.stderr with StringIO instances when
    # running in buffered mode, but pylint doesn't know that.  
    # pylint: disable=no-member
    return sys.stdout.getvalue()

def get_stderr():
    """Get data written to unit test stderr.
    
    :any:`unittest` replaces sys.stderr with a StringIO instance when running in buffered mode.
    
    Returns:
        str: Data written to sys.stderr while the test was running.
    """
    # unittest replaces sys.stdout and sys.stderr with StringIO instances when
    # running in buffered mode, but pylint doesn't know that.  
    # pylint: disable=no-member
    return sys.stderr.getvalue()

def exec_command(testcase, cmd, argv):
    """Execute a command's main() routine and return the exit code, stdout, and stderr data.
    
    Args:
        testcase (unittest.TestCase): TestCase instance executing the command.
        cmd (type): A command instance that has a `main` callable attribute.
        argv (list): Arguments to pass to cmd.main()
        
    Returns:
        tuple: (retval, stdout, stderr) results of running the command.
    """
    if not hasattr(sys.stdout, "getvalue"):
        testcase.fail("Test must be run in buffered mode")
    try:
        retval = cmd.main(argv)
    except SystemExit as err:
        retval = err.code
    return retval, get_stdout(), get_stderr()

def push_test_workdir():
    """Create a new working directory for a unit test.
    
    Sets the current working directory and :any:`tempfile.tempdir` to the newly created test directory.
    
    Directories created via this method are tracked.  If any of them exist when the program exits then
    an error message is shown for each.
    """
    #if not os.path.exists('tmp'):
    #    os.makedirs('tmp')
    #prefix = os.getcwd() + '/tmp/'
    #path = tempfile.mkdtemp(prefix=prefix)
    path = tempfile.mkdtemp()
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
    def onerror(function, path, excinfo):
        # pylint: disable=unused-argument
        sys.stderr.write("\nERROR: Failed to clean up testing directory %s\n" % path)
    tempfile.tempdir = _TEMPDIR_STACK.pop()
    os.chdir(_CWD_STACK.pop())
    shutil.rmtree(_DIR_STACK.pop(), ignore_errors=False, onerror=onerror)
    
def cleanup():
    """Finish 
    
    Checks that any files or directories created during testing have been removed."""
    for path in _DIR_STACK:
        sys.stderr.write("\nERROR: Test directory '%s' was not cleaned up\n" % path)

atexit.register(cleanup)


def not_implemented(cls):
    """Decorator for TestCase classes to indicate that the tests have not been written (yet)."""
    msg = "%s: tests have not been implemented" % cls.__name__
    _NOT_IMPLEMENTED.append(msg)
    return unittest.skip(msg)(cls)

def fresh_tau():
    """ Reset to fresh environment to test `tau initialize`."""
    shutil.rmtree(os.getcwd()+'/.tau')
    PROJECT_STORAGE._prefix = None
    PROJECT_STORAGE.disconnect_filesystem()


class TestCase(unittest.TestCase):
    """Base class for unit tests.
    
    Performs tests in a temporary directory and reconfigures :any:`tau.logger` to work with :any:`unittest`.
    """
    
    @classmethod
    def setUpClass(cls):
        global _SYSTEM_DIR
        if _SYSTEM_DIR is None:
            _SYSTEM_DIR = tempfile.mkdtemp()
        tau.SYSTEM_PREFIX = _SYSTEM_DIR
        push_test_workdir()
        # Reset stdout logger handler to use buffered unittest stdout
        # pylint: disable=protected-access
        cls._orig_stream = logger._STDOUT_HANDLER.stream
        logger._STDOUT_HANDLER.stream = sys.stdout
        initialize.COMMAND.main(['--project-name', 'proj1', '--target-name', 'targ1'])
        
    @classmethod
    def tearDownClass(cls):
        # Restore original stream to stdout logger handler
        # pylint: disable=protected-access
        PROJECT_STORAGE._prefix = None
        PROJECT_STORAGE.disconnect_filesystem()
        logger._STDOUT_HANDLER.stream = cls._orig_stream
        pop_test_workdir()


class TestRunner(unittest.TextTestRunner):
    """Test suite runner."""
    
    
    def run(self, test):
        retval = super(TestRunner, self).run(test)
        for item in _NOT_IMPLEMENTED:
            print "WARNING: %s" % item
        return retval
    
    
