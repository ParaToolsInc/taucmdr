Packaging and Releasing TAU Commander
=====================================

TAU Commander is a standard Python package, built with setuptools from ``pyproject.toml`` and published to
`PyPI`_ as ``taucmdr``.  It is installed from PyPI it with ``uv tool install taucmdr`` or ``pipx install taucmdr``
(see :doc:`install`).


Versions
--------

setuptools-scm takes the version from git tags, so there's no version number to edit before a release.  A
commit tagged ``v1.7.0`` builds as ``1.7.0``.  Any other commit builds as a development version of the next
patch release: five commits after ``v1.7.0``, the version is ``1.7.1.dev5+g<commit hash>``.  If tracked files
have uncommitted changes, the version also includes a date, e.g. ``1.7.1.dev5+g<commit hash>.d20261029``.
``tau --version`` shows the current version.

Release tags are ``v`` followed by the version, e.g. ``v1.7.0rc1`` for a release candidate and ``v1.7.0``
for the final release.  Always make annotated tags (``git tag -a``).  When a release candidate and the release
are on the same commit, setuptools-scm picks the newer annotated tag; a lightweight ``v1.7.0`` beside an
annotated ``v1.7.0rc1`` would still builds as ``1.7.0rc1``.

A given version number can only be uploaded to PyPI once, even if the files are deleted later, thus, a mistake in a
release necessitates a new version number.


Building
--------

Build the sdist and the wheel with::

   uv build

Both are written to ``dist/``.  The wheel is pure Python and holds the ``taucmdr`` package, including the vendored
TinyDB in ``taucmdr/_vendor/tinydb``, and the ``tau`` launcher in ``taucmdr-<version>.data/scripts/``.  It
installs no other top-level package.  The sdist includes most tracked files, including ``docs/``, ``examples/``
and ``.testfiles/``, but leaves out the CI and tool configuration, such as ``.github/`` and
``.pre-commit-config.yaml``.


Why TAU Commander runs in its own environment
---------------------------------------------

TAU Commander profiles Python programs, so the user's Python packages and TAU Commander's own must never
mix.  If the user's environment had a package named ``tau``, for example, both TAU Commander and the user's
program could import the wrong one.  That's why TAU Commander is only installed with ``uv tool`` or pipx,
which give it a virtual environment of its own, and never with ``pip`` into an environment the user directly
works with.

A separate environment doesn't stop the user's ``PYTHON*`` environment variables from reaching TAU
Commander's interpreter.  ``PYTHONPATH`` or ``PYTHONHOME`` could still change which modules it imports, or
stop it from starting.  The ``tau`` command is therefore a POSIX ``sh`` script (``scripts/tau``) rather than a
script entry point.  It finds the Python interpreter in its own environment and runs ``python -I -m taucmdr``.
Isolated mode (``-I``) makes that interpreter ignore every ``PYTHON*`` variable and the per-user
``site-packages`` directory.  Though inert, the variables nonetheless remain in the environment, so programs run by
TAU Commander continue to see them, so that a profiled Python interpreter will still inherit and honor these variables
even though the interpreter running TAU Commmander ignores them. If ``taucmdr`` starts without isolated mode, for example from
``python -m taucmdr``, ``taucmdr/__main__.py`` runs itself again with ``-I``.


Testing a build before publishing
---------------------------------

There are three ways to get a wheel to try out before publishing to TestPyPI:

* ``uv build`` in a checkout, as above.  Tag the commit locally first (``git tag -a v1.7.0rc1``) to build a
  release version.
* Run the release workflow locally with ``gh act``, which also runs the workflow's checks.  The workflow
  skips its publishing steps under act.  With a local tag on the commit::

     echo '{"ref": "refs/tags/v1.7.0rc1"}' > event.json
     gh act push -W .github/workflows/release.yml -e event.json \
        -P ubuntu-24.04=catthehacker/ubuntu:act-24.04 --artifact-server-path /tmp/act-artifacts

  The wheel and sdist are in ``/tmp/act-artifacts/1/dist/dist.zip``.

  Due to a bug in act v0.2.89's, the artifact server rejects ``actions/upload-artifact@v7``; until that's fixed, add
  ``--local-repository actions/upload-artifact@v7=<checkout of actions/upload-artifact at v4>``.
* Run the release workflow on GitHub on a branch.  A manual run builds and checks the distributions but
  does not publish them::

     gh workflow run release.yml --ref <branch>
     gh run download <run ID> -n dist

  A branch builds a development version, which PyPI would reject if an attempt was made to publish it.


Releasing
---------

1. Make sure CI passes on the branch, both on push and in a manual run on the older Pythons::

      gh workflow run CI.yml --ref <branch> -f python-versions='["3.11", "3.12", "3.13", "3.14"]'

2. Merge the branch into ``master``.
3. Tag a release candidate on ``master`` and push the tag::

      git tag -a v1.7.0rc1 -m "TAU Commander 1.7.0rc1"
      git push origin v1.7.0rc1

   The release workflow (``.github/workflows/release.yml``) builds the sdist and wheel, checks them, and
   publishes tags with ``rc`` in them to `TestPyPI`_ only.
4. Install the release candidate and try it.  Take only TAU Commander's wheel from TestPyPI, so its
   dependencies come from PyPI rather than from whatever uploads TestPyPI has under the same names::

      python3 -m pip download --no-deps --index-url https://test.pypi.org/simple/ --dest rc taucmdr==1.7.0rc1
      uv tool install rc/taucmdr-1.7.0rc1-py3-none-any.whl

5. Tag the release on the same commit, or on a later one if the candidate needed fixes, and push the tag::

      git tag -a v1.7.0 -m "TAU Commander 1.7.0"
      git push origin v1.7.0

   Tags without ``rc`` are published to PyPI.


Setting up publishing
---------------------

The release workflow publishes with PyPI's trusted publishing, so no PyPI password or API token is stored
in GitHub.  Each publish job asks GitHub for a short-lived token that indicates the repository, workflow and
environment in which it runs. PyPI accepts the upload only if those match a publisher registered for the
project.  This setup is needed once per site.

1. On `PyPI`_, add a publisher for the ``taucmdr`` project (a pending publisher, before the first
   release creates the project) with owner ``ParaToolsInc``, repository ``taucmdr``, workflow
   ``release.yml`` and environment ``pypi``.
2. On `TestPyPI`_, which has its own accounts, do the same with environment ``testpypi``.
3. In the GitHub repository's settings, create the environments ``testpypi`` and ``pypi``.  Limit both to
   tags matching ``v*``, so a workflow run from a branch can't publish, and add required reviewers to
   ``pypi`` so each release waits for an approval.


.. _`PyPI`: https://pypi.org/
.. _`TestPyPI`: https://test.pypi.org/
