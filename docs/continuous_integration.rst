Continuous Integration
======================

.. image:: https://github.com/ParaToolsInc/taucmdr/workflows/CI/badge.svg?branch=master&event=push
   :target: https://github.com/ParaToolsInc/taucmdr/actions
   :alt: CI Status

TAU Commander uses `GitHub Actions`_ for CI, nightly testing, and release publication.  The workflows are in ``.github/workflows/``.


CI (``CI.yml``)
---------------

CI runs on every push and pull request, or upon request.  Each variant installs the system compilers and MPI,
then runs ``tox`` for the version of Python used for testing. ``tox`` builds the wheel, installs it and
runs the whole test suite against the installed copy. The tests run twice for each Python version to cover both
storage backends, TinyDB and SQLite.

On push and pull request, CI tests Python 3.15 on ``ubuntu-24.04`` (x86_64), ``ubuntu-24.04-arm``
(aarch64) and ``macos-latest`` (Apple silicon).  To test the older supported Pythons, run the CI manually and
give the Python versions to test using the ``python-versions`` input::

   gh workflow run CI.yml --ref <branch> -f python-versions='["3.11", "3.12", "3.13", "3.14"]'

The ``ubuntu-24.04`` Python 3.15 TinyDB leg also builds the documentation.  On a push to ``master`` or
``unstable``, the ``deploy-docs`` job publishes them to `GitHub Pages`_ once all tests have passed.


Nightly (``nightly.yml``)
-------------------------

The nightly workflow runs every day at 10:18 UTC, or upon request.  It installs TAU Commander with
``uv tool install``, builds a minimal and then a full set of TAU configurations with
``tau system configure``, runs the test suite under each backend against that installation's ``tau``, and
then runs TAU's ``tau_validate``.


Release (``release.yml``)
-------------------------

The release workflow runs when a ``v*`` tag is pushed.  It builds the sdist and wheel, checks that their
version matches the tag, and publishes them, release candidates to TestPyPI and releases to PyPI.  Run by
hand, it builds and checks the distributions without publishing them.  See :doc:`packaging`.


Test results
------------

Each test run writes ``test-timings.csv`` to ``build/test-results/``, and JUnit XML files too when
unittest-xml-reporting is installed, as it is under tox.  CI and the nightly upload that directory as an
artifact (``taucmdr-unit-test-results-<os>-py<version>-<backend>`` in CI,
``taucmdr-unit-test-results-<os>-<backend>`` in the nightly) and send the JUnit files to `Codecov`_.
Download an artifact with ``gh run download <run ID> -n <artifact name>``.


.. _`GitHub Actions`: https://github.com/ParaToolsInc/taucmdr/actions
.. _`GitHub Pages`: https://paratoolsinc.github.io/taucmdr/
.. _`Codecov`: https://codecov.io/github/ParaToolsInc/taucmdr
