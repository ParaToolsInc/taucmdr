How to write and run unit tests
===============================

After modifying or creating a file, make sure to check that function works as
expected with unit testing.

Running unit tests
------------------

Run every unit test from the repository root with tox::

   tox -e py315

The argument can be replace with ``py311`` to ``py314`` test the other supported Python versions. 
When run, tox will build a wheel, install it into ``.tox/py315`` and run ``scripts/run_tests.py`` there.
Arguments after ``--`` will be passed through to ``scripts/run_tests.py``.  Without them, tox passes ``-U``.

For quicker runs, a previously built environment can be used::

   .tox/py315/bin/python scripts/run_tests.py [-S] [-U] [-v] [--list] [TEST ...]

The ``TEST`` list is the dotted name of a package, module, class or method; for example, 
``taucmdr.cli.commands.tests.test_initialize``. Giving a package name will runs every test module under it.

Options:

* ``-v`` prints each test's name as it runs.
* ``--list`` prints the selected test IDs without running them.
* ``-U`` points user storage at a temporary directory.
* ``-S`` points system storage at a temporary directory, so TAU and its dependencies are built from scratch.

Test runs keep system storage in the checkout's ``system/`` directory, unless ``__TAUCMDR_SYSTEM_PREFIX__``
is set.

Writing new unit tests
----------------------

Step 1: Create a tests directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Create a a tests directory in the directory where the modified file is located
if one does not already exist.

Step 2: Contents of the tests directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each tests directory should have a ``__init__.py`` file so that the tests can
be discovered. A file called ``test_function_name.py`` should exist for each
file in the directory.

Step 3: Contents of ``test_function_name.py``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each ``test_function_name.py`` file should import the :any:`tau.tests` package. A
separate class should be created for each function that is tested and multiple
test functions may be created in each class in order to run multiple tests on a
single function. Each function should use an ``assert*`` command that checks if
the function produces the expected output.

An example unit test function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Below is an example unit test function for a function that converts a string
to camel case.

::

    class CamelCaseTest(unittest.TestCase):
        def test_camelcase(self):
            self.assertEqual(util.camelcase("abc_def_ghi"), "AbcDefGhi")


Further information on the unit test package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The `page <https://docs.python.org/2/library/unittest.html>`_ has more
information on writing a unit test function.
