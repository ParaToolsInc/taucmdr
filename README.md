
THE TAU PERFORMANCE SYSTEM (R)
===============================================================================
http://tau.uoregon.edu

Copyright 1997-2014
Department of Computer and Information Science, University of Oregon
Advanced Computing Laboratory, Los Alamos National Laboratory
Research Center Juelich, ZAM Germany

**NOTE**: Please refer to `tools/src/contrib/LICENSE` files for open
source licenses of other packages that TAU uses internally.


INSTALLATION
===============================================================================

Instructions on installing TAU can be found in the INSTALL file.
Java users should see README.JAVA


OVERVIEW
===============================================================================

TAU is a program and performance analysis tool framework being developed for
the DOE and ASC program at University of Oregon. TAU provides a suite of 
static and dynamic tools that provide graphical user interaction and 
interoperation to form an integrated analysis environment for parallel 
Fortran 95, C, and C++ applications.  In particular, a robust  performance 
profiling facility availble in TAU has been applied extensively in the ACTS 
toolkit.  Also, recent advancements in TAU's code analysis capabilities have 
allowed new static tools to be developed, such as an automatic instrumentation
tool.

The model that TAU uses to profile parallel, multi-threaded C++, C, Fortran 95,
UPC, Python, Chapel and Java programs maintains performance data for each 
thread, context, and node in use by an application.  The profiling 
instrumentation needed to implement the model captures data for functions, 
methods, basic blocks, and statement execution at these levels.  
The instrumentation is complicated, however, by advanced features in the C++ 
language, such as templates and namespaces. All C++ language features are 
supported in the TAU profiling instrumentation, which is available through an 
API at the library or application level.  The API also provides selection of 
profiling groups for organizing and controlling instrumentation.  ACTS software
layers have been instrumented and support for thread profiling has been recently
added.

From the profile data collected, TAU's profile analysis procedures can generate
a wealth of performance information for the user.  It can show the exclusive
and inclusive time spent in each function with nanosecond resolution.  For
templated entities, it shows the breakup of time spent for each instantiation.
Other data includes how many times each function was called, how many profiled
functions did each function invoke, and what the mean inclusive time per call
was.  Time information can also be displayed relative to nodes, contexts, and
threads.  Instead of time, hardware performance data can be shown.  Also,
user-level profiling is possible.

TAU's profile visualization tool, paraprof, provides graphical displays of all
the performance analysis results, in aggregate and per node/context/thread
form.  The user can quickly identify sources of performance bottlenecks in the
application using the graphical interface.  In addition, TAU can generate event
traces that can be displayed with the Vampir trace visualization tool.

TAU is being developed jointly by the University of Oregon, Los Alamos National
Laboratory, and Research Centre J�lich, ZAM, Germany.

