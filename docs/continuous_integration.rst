Continuous Integration
======================

.. image:: https://github.com/ParaToolsInc/taucmdr/workflows/CI/badge.svg?branch=master&event=push
   :target: https://github.com/ParaToolsInc/taucmdr/actions
   :alt: CI Status

TAU Commander uses `GitHub Actions`_ for continuous integration. The workflow
configurations are defined in ``.github/workflows/`` and run automatically on
every push and pull request.

CI Workflows
------------

**CI** (``CI.yml``):
  Installs TAU Commander, runs the full test suite against multiple database
  backends (TinyDB and SQLite), builds the Sphinx documentation, reports code
  coverage to Codecov, and deploys documentation to GitHub Pages on pushes to
  ``master`` or ``unstable``.
Each test run writes ``test-timings.csv`` to ``build/test-results/``, and JUnit XML files too when
unittest-xml-reporting is installed, as it is under tox.  CI and the nightly upload that directory as an
artifact (``taucmdr-unit-test-results-<os>-py<version>-<backend>`` in CI,
``taucmdr-unit-test-results-<os>-<backend>`` in the nightly) and send the JUnit files to `Codecov`_.
Download an artifact with ``gh run download <run ID> -n <artifact name>``.

**Nightly** (``nightly.yml``):
  Runs a more comprehensive nightly build that includes a full TAU installation
  and ``tau_validate`` testing in addition to the standard test suite.

.. _`GitHub Actions`: https://github.com/ParaToolsInc/taucmdr/actions
