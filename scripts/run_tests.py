#!/usr/bin/env python3
#
# Copyright (c) 2026, ParaTools, Inc.
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
"""Run TAU Commander's unit tests.

This is a test runner which provides functionality mimicking that provided by the former
``python setup.py test`` command removed from setuptools in v72. It sets environment
variables required by TAU Commander's tests (``__TAUCMDR_SCRIPT__``, ``__TAUCMDR_REPO_DIR__``,
``__TAUCMDR_SYSTEM_PREFIX__``, and ``__TAUCMDR_USER_PREFIX__``). These variables must already be set
when the :py:mod:`taucmdr` module is first loaded, so this must be a standalone script rather than part of
that module.

Usage::

    PYTHONPATH=packages python scripts/run_tests.py [-S] [-U] [-v] [--list] [TEST ...]
"""

import argparse
import importlib
import os
import shutil
import sys
import tempfile
import unittest
import warnings

_FAILED_TEST_PREFIX = 'unittest.loader._FailedTest.'
"""str: Prefix of the ID unittest gives to a test it couldn't load."""


class NoTestsError(Exception):
    """A test name selected no tests."""


def _parse_args(argv):
    parser = argparse.ArgumentParser(prog='run_tests.py', description="Run TAU Commander's unit tests.")
    parser.add_argument('-S', '--system-sandbox', action='store_true',
                        help="Use a temporary sandbox directory for system storage.")
    parser.add_argument('-U', '--user-sandbox', action='store_true',
                        help="Use a temporary sandbox directory for user storage.")
    parser.add_argument('-v', '--verbose', action='store_const', const=2, default=1, dest='verbosity',
                        help="Print each test's name as it runs.")
    parser.add_argument('--list', action='store_true', help="Print the selected test IDs without running them.")
    parser.add_argument('tests', nargs='*', metavar='TEST',
                        help="Tests to run, by dotted name of a package, module, class or method, e.g., "
                             "taucmdr.cli.commands.tests.test_initialize.  Default: run every test.")
    return parser.parse_args(argv)


def _iter_test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from _iter_test_ids(test)
        else:
            yield test.id()


def _load_name(loader, name, top_level_dir):
    # loadTestsFromName() doesn't look inside packages, so discover the tests under a package ourselves.
    try:
        module = importlib.import_module(name)
    except ImportError:
        module = None
    # discover() can't start in a namespace package, which has no __file__
    if module is not None and hasattr(module, '__path__') and getattr(module, '__file__', None):
        return loader.discover(os.path.dirname(os.path.abspath(module.__file__)), pattern='test*.py',
                               top_level_dir=top_level_dir)
    return loader.loadTestsFromName(name)


def _load_tests(names):
    """Load the named tests, or every test if no names are given.

    Args:
        names (list): Dotted names of packages, modules, classes or methods.

    Returns:
        unittest.TestSuite: The selected tests.

    Raises:
        NoTestsError: A name selected no tests.
    """
    # Can't import at top level because env vars have to be set first.
    import taucmdr  # pylint: disable=import-outside-toplevel
    loader = unittest.TestLoader()
    package_dir = os.path.dirname(os.path.abspath(taucmdr.__file__))
    print(f"Testing taucmdr from {package_dir}")
    top_level_dir = os.path.dirname(package_dir)
    if not names:
        return loader.discover(package_dir, pattern='test*.py', top_level_dir=top_level_dir)
    suite = unittest.TestSuite()
    for name in names:
        tests = _load_name(loader, name, top_level_dir)
        if not tests.countTestCases():
            raise NoTestsError(f"'{name}' doesn't contain any tests")
        suite.addTests(tests)
    return suite


def _make_runner(verbosity):
    try:
        import xmlrunner  # pylint: disable=import-outside-toplevel
    except ImportError:
        runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    else:
        # JUnit XML goes in the current directory as TEST-*.xml, where CI collects it for Codecov.
        runner = xmlrunner.XMLTestRunner(output='.', verbosity=verbosity, buffer=True)
    runner.warnings = None
    return runner


def main(argv=None):
    """Run the selected tests.

    Args:
        argv (list): Command line arguments.

    Returns:
        int: 0 if every selected test loaded and every test that ran passed; 1 otherwise.
    """
    args = _parse_args(argv)
    # Ensure that the help text uses the name `tau` instead of the name of this script.
    os.environ['__TAUCMDR_SCRIPT__'] = 'tau'
    os.environ['__TAUCMDR_REPO_DIR__'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ['__TAUCMDR_DISABLE_PAGER__'] = '1'
    sandboxes = []
    for enabled, var, label in ((args.system_sandbox, '__TAUCMDR_SYSTEM_PREFIX__', 'system'),
                                (args.user_sandbox, '__TAUCMDR_USER_PREFIX__', 'user')):
        if enabled:
            path = tempfile.mkdtemp(prefix=f'taucmdr-{label}-')
            os.environ[var] = path
            sandboxes.append(path)
            print(f"Sandboxing {label} storage: {path}")
    if not sys.warnoptions:
        warnings.simplefilter('default')
    # TAU Commander's own code must not use deprecated Python features, so they fail the tests.
    for category in (DeprecationWarning, PendingDeprecationWarning):
        warnings.filterwarnings('error', category=category, module=r'taucmdr(\.|$)')
    try:
        try:
            suite = _load_tests(args.tests)
        except NoTestsError as err:
            print(f"ERROR: {err}")
            return 1
        if args.list:
            test_ids = list(_iter_test_ids(suite))
            for test_id in test_ids:
                print(test_id)
            failed = [test_id[len(_FAILED_TEST_PREFIX):] for test_id in test_ids
                      if test_id.startswith(_FAILED_TEST_PREFIX)]
            if failed:
                print(f"ERROR: Couldn't load {', '.join(failed)}")
                return 1
            return 0
        print(f"Running tests with database backend {os.environ.get('__TAUCMDR_DB_BACKEND__', 'auto')}")
        result = _make_runner(args.verbosity).run(suite)
        from taucmdr.tests import _NOT_IMPLEMENTED  # pylint: disable=import-outside-toplevel,protected-access
        for msg in _NOT_IMPLEMENTED:
            print(f"WARNING: {msg}")
        return 0 if result.wasSuccessful() else 1
    finally:
        for path in sandboxes:
            shutil.rmtree(path, ignore_errors=True)
            if os.path.exists(path):
                print(f"WARNING: Couldn't delete sandbox directory {path}")


if __name__ == '__main__':
    sys.exit(main())
