Packaging and Releasing TAU Commander
=====================================

Versioning
----------

TAU Commander follows semantic versioning (https://semver.org/).
The version number is MAJOR.MINOR.PATCH.COMMIT where COMMIT is the number of
commits since the last tag.  E.g. version 1.3.0.5 is five unreleased commits
after the version 1.3.0 release.

The ``VERSION`` file is created automatically and shows the current version.
It might be out of date.  It's always a good idea to ``make clean`` before
performing any task that depends on a version number.

setup.py
--------

TAU Commander follows the `Python Packaging Guide`_, the same resource that guides package deployment to the
`Python Package Index (PyPI)`_.  All tasks related to packaging and releasing TAU Commander are handled via the
setup.py script in the project root directory.  The script has many commands but most aren't relevent to
TAU Commander.  The important ones are:

:build:
   Build everything needed for a new TAU Commander installation in the ``build`` directory.

:build_sphinx:
   Rebuild TAU Commander developer documentation (which you are currently reading) in the ``build/sphinx`` directory.
   Use the ``--update-gh-pages`` option and associated options (see ``--help``) to update the developer documentation
   on Github (http://paratoolsinc.github.io/taucmdr/).

:test:
   Run all unit tests and pylint.

:release:
   Generate distributable release packages in the ``dist`` directory.
   See the ``--web`` and ``--all`` flags.  You probably want the ``--all`` flag.
   E.g. for a new version release:

   .. code-block:: bash

      git tag v1.3.1
      make clean
      python setup.py release --all

:install:
   Install a TAU Commander distribution. End users must **NEVER** use ``python setup.py install``!  TAU Commander needs
   its own, private, un-shared Python installation to avoid environment contamination when profiling a user's code.
   For example, if the user's Python has a package named "tau" installed in it then both TAU Commander and the user's
   code will break.  The top-level Makefile will call ``python setup.py install`` with appropriate options after
   installing a pristine Python just for TAU Commander. [2]_

Use ``python setup.py <command> --help`` to see command line options for each command.



.. [1] It would be easy to publish TAU Commander to PyPI, but that may lead to users installing TAU Commander in their
   shared Python installation and cause problems when profiling Python applications via TAU Commander.
.. [2] Why not `virtualenv`_?  Because user's are untrustworthy and do ... nonstandard ... things to their Python
   installations.  Asserting that TAU Commander has it's own, private Python installation simplifies installation and
   increases the chances that the installation will work on the first try.  Also, we might not have network access at
   the user's end so we can't count on automatic dependency resolution.

.. _`Python Packaging Guide`: https://packaging.python.org/
.. _`Python Package Index (PyPI)`: https://pypi.python.org/pypi
.. _`virtualenv`: https://virtualenv.pypa.io
