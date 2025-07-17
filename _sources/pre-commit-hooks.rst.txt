TAU Commander git hooks
=======================

.. contents::

Introduction
------------

TAU Commander developers and contributors should enable the local git hooks.
The purpose of these hooks is to catch simple style, syntax, and other miscellaneous errors
before they are committed to the repository and free up CI testing resources to find more complicate problems.
The hooks will only check files (and the specific lines of code) touched in a given commit, and,
therefore, can be used to help incrementally implement new style standards or other requirements.

Getting Setup
-------------

The `pre-commit`_ package has been added to ``requirements-dev.txt`` and therefore will be installed
when the other development packages are installed using ``pip``:

::

   $ pip install -r requirements-dev.txt

You can also install ``pre-commit`` manually with ``pip`` (or ``pip3``), using macOS Homebrew, or various other package managers.

Once pre-commit is installed on your system or in your virtualenv, you can follow the `online instructions`_ for setting up a local repository.
It is recommended that you remove any local git hooks you may have already installed before installing the TAU Commander hooks,
as sometimes hooks can assume the existence of other hooks and do sneaky things like stashing changes and then popping them.
If you have any such hooks installed, then pre-commit hook(s) may overwrite one of them.
Hooks get installed into ``.git/hooks`` and it is worth having alook at what is there and removing any existing hooks.

Finally, you can proceed with installing the hooks into your local TAU Commander git repository:

::

   $ cd ~/src/taucmdr
   $ pre-commit --version
   # >= pre-commit 2.2.0
   $ ls -la .git/hooks
   # Should be empty
   $ pre-commit install
   # Optionally, see if your branch has any violations
   $ pre-commit run --all-files

.. _pre-commit: https://pre-commit.com
.. _online instructions: https://pre-commit.com/#quick-start
