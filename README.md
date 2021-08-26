TAU Commander
=============

[![GitHub license][License img]](./LICENSE)
[![CI][CI img]](https://github.com/ParaToolsInc/taucmdr/actions)
[![Build Status][Build img]](https://travis-ci.org/ParaToolsInc/taucmdr)
[![Coverage Status][Coverage img]](https://codecov.io/github/ParaToolsInc/taucmdr?branch=master)

![The TAU Commander performance engineering solution consists of an
intuitive, client-side application and cloud-hosted data analysis,
storage, and visualization services.](docs/_static/taucmdr.png)

TAU Commander from [ParaTools, Inc.](http://www.paratools.com/) is a
production-grade performance engineering solution that makes
[The TAU Performance System](http://tau.uoregon.edu/) users more productive.
It presents a simple, intuitive, and systemized interface that guides users
through performance engineering workflows and offers constructive feedback
in case of error.  TAU Commander also enhances the performance engineer's
ability to mine actionable information from the application performance
data by connecting to a [suite of cloud-based data analysis, storage,
visualization, and reporting services](http://www.taucommander.com/).

TAU Commander is especially useful for porting, developing, modernizing,
benchmarking, and purchasing efforts where the intricacies of multi-layered
software parallelism are difficult to intuit.  The principal components of
TAU Commander are:

  - An intuitive user interface for the
  [TAU Performance System](http://tau.uoregon.edu/) that simplifies the
  process of acquiring and displaying software performance data on a
  variety of computer systems.
  - A suite of cloud-based performance data analysis, storage, visualization,
  and reporting services that enhances the performance engineer's ability
  to mine actionable information from software application performance data.

Getting Started
===============

Install TAU Commander to the default location:

  - `make install`

Or, to install to a different location:

  - `make install INSTALLDIR=/path/to/installation`

Add TAU Commander to your PATH:

  - bash-like shells (nearly everyone):
    - `export PATH=/path/to/taucmdr/bin:$PATH`
  - csh-like shells (nearly everyone else):
    - `set path=(/path/to/taucmdr/bin $path)`

Initialize a new TAU project:

  - `cd /path/to/your/code`
  - `tau initialize`

Building Tau Commander JupyterLab Extension
===========================================

Build the Docker image:

  - `make dev-container`

Run the newly created Docker image:

  - `make run-container`

Change directories to where the extension resides:

  - `cd $HOME/src/jupyter/tau_commander`

Install the node packages:

  - `jlpm`

Build the extension:

  - `jlpm run build`

Installing Tau Commander JupyterLab Extension
=============================================

Install the extension:

  - `jupyter labextension install $HOME/src/jupyter/tau_commander`

Launch the extension:

  - `tau commander`

Building conda package of Jupyterlab with Tau Commander prepackaged
===================================================================

Change directories to where jupyterlab delux resides:

  - `cd $HOME/src/jupyter`

Install the jupyterlab delux dependencies:

  - `./install_delux_dep.sh`

Use cookiecutter to create a new recipe:

  - `cookiecutter jupyterlab_delux`

Change directories to the newly created recipe:

  - `cd jupyterlab_{{ cookiecutter.project_slug }}`

Add the JupyterLab extension installation commands in `recipe/bld.bat` and `recipe/build.sh`. They will have the structure:
  
  - `jupyter labextension install $HOME/src/jupyter/tau_commander --no-build`

Generate the conda package:

  - `conda build -c conda-forge recipe`

The newly generated conda package is located in:

  - `$HOME/taucmdr/conda/conda-bld/noarch/jupyter_lab{{ cookiecutter.project_slug }}.tar.bz2`

Install the extension with:

  - `conda install jupyter_lab{{ cookiecutter.project_slug }}.tar.bz2`

Launch the extension with:

  - `tau commander`

Need help?
==========

  - Add `--help` to any TAU Commander command line to see command line usage.
  - Use `tau help` to view online documentation.  (Very incomplete at the moment.)
  - Contact support@paratools.com with questions or feedback.

Developers
==========

TAU Commander developers should visit the [developer documentation](http://paratoolsinc.github.io/taucmdr/).

Acknowledgements
================

This work is supported by the United States Department of Energy under
DoE SBIR grant DE-SC0009593.

The work on extending TAU Commander for OpenSHMEM was supported by the
United States Department of Defense (DoD) and used resources of the
Computational Research and Development Programs and the Oak Ridge
Leadership Computing Facility (OLCF) at Oak Ridge National Laboratory.

---------------------------------------------------------------------------

[CI img]: https://github.com/ParaToolsInc/taucmdr/workflows/CI/badge.svg?branch=GH-Actions&event=push "GH Actions CI image"
[Build img]: https://travis-ci.org/ParaToolsInc/taucmdr.svg?branch=master "Travis-CI build status image"
[Coverage img]: https://codecov.io/github/ParaToolsInc/taucmdr/coverage.svg?branch=master "Unit test code coverage image"
[License img]: https://img.shields.io/badge/license-BSD--3-blue.svg "View BSD-3 License"
