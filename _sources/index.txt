.. TauCmdr documentation master file, created by
   sphinx-quickstart on Fri Apr 10 14:18:42 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome
=======

.. important::
   This documentation is intended for the lucky people **developing** 
   TAU Commander.  If you are a TAU Commander **user** then you should 
   visit `the TAU Commander website`_. If you're looking for information 
   on the `TAU Performance System`_ (the heart of TAU Commander) then you 
   should visit `the TAU project page <http://tau.uoregon.edu/>`_.

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

**Remember:** Code with a pylint score less than **9** will not be accepted to 
the master branch.


The TAU Commandments
====================

1. Thou shalt use `pylint`_ 1.5.4 or later as part of your development cycle.
2. Thou shalt follow the :doc:`design` for it is sacred.
3. Thou shalt style thine code according to the :doc:`style`.
4. Thou shalt document your code according to the :doc:`documentation`.
5. **Never** shalt thou develop on the master branch, for that is an abomination.
6. **Never** shalt thou merge code into the master branch that is failing the continuous integration (CI) tests.
7. **Never** shalt thou *just quickly fix this one thing because I have a hard deadline I forgot and now I really 
   really really need this feature to be part of TAU Commander whatever the cost and oh God I broke it I broke it 
   and everything is on fire*.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   design
   style
   documentation
   new_feature
   new_compiler
   unit_tests
   packaging

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



Modules
=======

.. toctree::
   :maxdepth: 4

   modules



.. _the TAU Commander website: http://www.taucommander.com/
.. _TAU Performance System: http://tau.uoregon.edu/
.. _pylint: http://www.pylint.org/
.. _`unit tests`: ./unit_tests.html

