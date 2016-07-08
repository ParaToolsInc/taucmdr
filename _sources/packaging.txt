Packaging and Releasing TAU Commander
=====================================

TL;DR
-----

Building a new TAU Commander release package is as simple as::

   python setup.py build_release  # Creates build/taucmdr-VERSION.sh

Users install the release with::

   ./taucmdr-VERSION.sh [options]


-------------------------------------------------------------------------------


There are two parts to getting the TAU Commander tool into a user's hands:

:Packaging:
   Collecting all the TAU Commander Python files into a single archive file called a **distribution**.  Distributions
   are built via the setup.py script as described below and, like most Python packages, they do not include 
   dependencies. TAU, PDT, and Python are *not* included in a TAU Commander distribution.  TAU Commander distributions 
   are not fit for user consumption. [1]_

:Releasing:
   Bundling a TAU Commander distribution with supporting files and scripts to form a complete software **release**
   ready for installation by the user.  A release will either include all of TAU Commander's dependencies in the 
   release itself, or provide scripts or metadata of some kind that ensure the missing dependencies are installed 
   before TAU Commander is.
   

setup.py
--------

TAU Commander follows the `Python Packaging Guide`_, the same resource that guides package deployment to the 
`Python Package Index (PyPI)`_.  All tasks related to packaging and releasing TAU Commander are handled via the 
setup.py script in the project root directory.  The script has many commands but most aren't relevent to 
TAU Commander.  The important ones are:

:build:
   Build a new TAU Commander distribution in the ``build`` directory. 
   Use this to see what's included in the distribution.

:build_sphinx:
   Rebuild TAU Commander developer documentation (which you are currently reading) in the ``build/sphinx`` directory.
   Use the ``--update-gh-pages`` option and associated options (see ``--help``) to update the developer documentation 
   on Github (http://paratoolsinc.github.io/taucmdr/). 
   
:test:
   Run all unit tests and pylint.
   
:install:
   Install a TAU Commander distribution. **NEVER** use ``python setup.py install`` directly!  TAU Commander must have 
   its own, private, un-shared Python installation to avoid environment contamination when profiling a user's code.  
   For example, if the user's Python has a package named "tau" installed in it then both TAU Commander and the user's 
   code will break.  The top-level Makefile will call ``python setup.py install`` with appropriate options after 
   installing a pristine Python just for TAU Commander. [2]_ Should always be used with ``--prefix`` and 
   ``--install-scripts`` options.
   
:build_release:
   Build a new TAU Commander release file, ``taucmdr-VERSION.sh``, in the ``build`` directory.
   
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

