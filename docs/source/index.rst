.. TauCmdr documentation master file, created by
   sphinx-quickstart on Fri Apr 10 14:18:42 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. contents::

.. toctree::
   :maxdepth: 2

   design
   style

Welcome
=======

.. important::
   This documentation is intended for the lucky people **developing** 
   TAU Commander.  If you are a TAU Commander **user** then you should 
   visit `the TAU Commander website`_. If you're looking for information 
   on the `TAU Performance System`_ (the heart of TAU Commander) then you 
   should visit `the TAU project page <http://tau.uoregon.edu/>`.

This document will help you, the TAU Commander developer, contribute to the 
project. For over two decades the `TAU Performance System`_ has been developed 
primarily by graduate students with extreme demands on their time so best 
practices of software design, safety, and maintainability were largely ignored 
in favor of getting results quickly.  This short term thinking ran up an
enormous technical debt in TAU and created a "wet spaghetti" code base where 
TAU developers throw stuff at the wall to see what sticks. The goal of this 
developer's guide to bring a little sanity back to the development cycle and 
take advantage of important software engineering lessons learned in the last 
two decades.

The TAU Commandments
--------------------

1. Thou shalt read and obey the :doc:`style`.
2. Thou shalt read and obey the :doc:`design`.
3. Thou shalt use `pylint`_ 1.4 or later as part of your development cycle.
4. Thou shalt document your code according to the :doc:`style`.
5. **Never** shalt thou develop on the master branch, for that is an abomination.
6. **Never** shalt thou merge broken code to the master branch.
7. **Never** shalt thou *just quickly fix this one thing because I have a hard deadline I forgot and now I really really really need this feature to be part of TAU Commander whatever the cost and oh God I broke it I broke it and everything is on fire*.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _the TAU Commander website: http://www.taucommander.com/
.. _TAU Performance System: http://tau.uoregon.edu/
.. _pylint: http://www.pylint.org/
