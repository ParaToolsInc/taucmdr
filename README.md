TAU Commander
=============

[![GitHub license][License img]](./LICENSE)
[![Build Status][Build img]](https://travis-ci.org/ParaToolsInc/taucmdr)
[![Coverage Status][Coverage img]](https://codecov.io/github/ParaToolsInc/taucmdr?branch=master)
[![Chat][Gitter img]](https://gitter.im/ParaToolsInc/taucmdr?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

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

- Add TAU Commander to your PATH: `export PATH=/path/to/taucmdr/bin:$PATH`
- Type `tau --help`.

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

[Build img]: https://travis-ci.org/ParaToolsInc/taucmdr.svg?branch=master "Travis-CI build status image"
[Coverage img]: https://codecov.io/github/ParaToolsInc/taucmdr/coverage.svg?branch=master "Unit test code coverage image"
[License img]: https://img.shields.io/badge/license-BSD--3-blue.svg "View BSD-3 License"
[Gitter img]: https://badges.gitter.im/Join%20Chat.svg "Gitter chat image"
