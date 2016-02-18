How to write and run unit tests
===============================

After modifying or creating a file, make sure to check that function works as
expected with unit testing.

Writing unit tests
------------------

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
Each ``test_function_name.py`` file should import the unittest package. A
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

Running unit tests
------------------

Run the runtests script to execute all unit tests:

::

$ ./runtests

