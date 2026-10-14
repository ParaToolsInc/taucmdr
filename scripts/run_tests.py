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
variables required by TAU Commander's tests (``__TAUCMDR_SCRIPT__``, ``__TAUCMDR_SYSTEM_PREFIX__``,
and ``__TAUCMDR_USER_PREFIX__``). These variables must already be set when the :any:`taucmdr`
module is first loaded, so this must be a standalone script rather than part of that module.

Usage::

    PYTHONPATH=packages python scripts/run_tests.py [-S] [-U] [-v] [--list] [TEST ...]
"""

import argparse
import os
import shutil
import sys
import tempfile
import unittest


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
                        help="List of tests to run by fully-qualified name, e.g., "
                             "taucmdr.cli.commands.tests.test_initialize.  Default: run every test.")
    return parser.parse_args(argv)


def _iter_test_ids(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from _iter_test_ids(test)
        else:
            yield test.id()


def _load_tests(names):
    # Can't import at top level because env vars have to be set first.
    import taucmdr  # pylint: disable=import-outside-toplevel
    loader = unittest.TestLoader()
    if names:
        return loader.loadTestsFromNames(names)
    package_dir = os.path.dirname(os.path.abspath(taucmdr.__file__))
    return loader.discover(package_dir, pattern='test*.py', top_level_dir=os.path.dirname(package_dir))


def _make_runner(verbosity):
    try:
        import xmlrunner  # pylint: disable=import-outside-toplevel
    except ImportError:
        return unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    # JUnit XML goes in the current directory as TEST-*.xml, where CI collects it for Codecov.
    return xmlrunner.XMLTestRunner(output='.', verbosity=verbosity, buffer=True)


def main(argv=None):
    """Run the selected tests.

    Args:
        argv (list): Command line arguments.

    Returns:
        int: 0 if every test that ran passed; 1 otherwise.
    """
    args = _parse_args(argv)
    # Ensure that the help text uses the name `tau` instead of the name of this script.
    os.environ['__TAUCMDR_SCRIPT__'] = 'tau'
    os.environ['__TAUCMDR_DISABLE_PAGER__'] = '1'
    sandboxes = []
    for enabled, var, label in ((args.system_sandbox, '__TAUCMDR_SYSTEM_PREFIX__', 'system'),
                                (args.user_sandbox, '__TAUCMDR_USER_PREFIX__', 'user')):
        if enabled:
            path = tempfile.mkdtemp(prefix=f'taucmdr-{label}-')
            os.environ[var] = path
            sandboxes.append(path)
            print(f"Sandboxing {label} storage: {path}")
    try:
        suite = _load_tests(args.tests)
        if args.list:
            for test_id in _iter_test_ids(suite):
                print(test_id)
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


if __name__ == '__main__':
    sys.exit(main())
