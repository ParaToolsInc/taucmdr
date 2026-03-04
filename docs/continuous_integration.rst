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

**Nightly** (``nightly.yml``):
  Runs a more comprehensive nightly build that includes a full TAU installation
  and ``tau_validate`` testing in addition to the standard test suite.

.. _`GitHub Actions`: https://github.com/ParaToolsInc/taucmdr/actions
