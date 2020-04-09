TAU Commander Design
====================

General Definitions
-------------------

:Target:
  A list of configuration options (a "configuration object") that completely describes the hardware and
  software environment in which the TAU Commander workflow will be performed.  This includes, among other things, the
  operating system distribution (e.g. Linux, Darwin, CNL, etc.) CPU architecture (x86_64, ppc64, etc.) compiler
  installation paths, compiler family (e.g. Intel, Cray, PGI, etc.), MPI installation path, and TAU and PDT
  installation paths.

:Application:
  A configuration object that completely describes the features of the application, e.g. does the
  application use MPI?  OpenMP?  CUDA?  Does it have any special compiler requirements?

:Measurement:
  A configuration object that completely describes the measurement approach.  Parameters for
  source-based instrumentation, compiler-based instrumentation, sampling, memory measurement, I/O measurement,
  selective instrumentation, etc. are all listed in this configuration object.

TAM Model
---------

Now we can compose sets of Targets, Applications, and Measurements to form workflows.  This is the *TAM Model*.  Here
are some example workflows.  At this point we're still very general and any tool could do this, not just TAU Commander.

- *Application Performance Analysis*: One target, one application, many measurements.  By holding the target and
  application constant while we vary the measurement config we explore the different performance characteristics of the
  application when executing in a well-defined hardware/software environment.

- *System Benchmarking*: One target, many applications, one measurement.  By holding the target and measurement
  constant while varying the application we explore how well this particular target executes different workloads.

- *Environment Tuning / Compiler Comparison / Hardware Acquisition / Purchasing*:  Many targets, one application,
  one measurement.  By holding the application and measurement constant while varying the target we discover which
  target produces the optimal performance characteristics for a specific application.

The notation for a TAM workflow is (TN1,AN2,MN3) where N[123] are integers or the '*' symbol.  Our above example
workflows are denoted, in order:

- (T1,A1,M*)
- (T1,A*,M1)
- (T*,A1,M1)

TAU Commander Definitions
-------------------------

Now that we have TAM described, here are the rest of the definitions.  These are less general than TAM, more specific
to TAU Commander:

:Experiment:
  A combination of exactly one Target, Application, and Measurement (T1,A1,M1).  The experiment
  completely describes the hardware and software that produce performance data (if any).  Note that *not* producing any
  data is a valid experimental result, i.e. this particular experiment raises a fault in the application.

:Trial:
  The result of performing an experiment including at least the generated performance data (if any), a record
  of the user's runtime environment (e.g. PATH), and timestamps marking the start and end of the trial.  The TAU
  Commander user performs many trial to minimize variance in the dataset.

:Project:
  A container for grouping TAM workflows that relate to a common objective along with the data produced by
  the workflow (i.e. trials).  A project may contain any number of Target, Application, and Measurement objects and
  these objects may be shared between many projects.

TAU Commander Example
---------------------

Suppose I have an application that uses MPI and OpenMP and I want to see how performance varies when I use MPI only,
OpenMP only, or both together on the same target configuration.  I want to show time spent in MPI communication and
OpenMP regions and directives whenever those features are active.

First I create an empty project to hold my configuration objects.  (Or you could create the objects first then add them
to a project later. Or reuse TAM objects from another existing project.  Order doesn't matter.)  Then I create TAM
configuration objects to describe the problem and add them to the project:

- *Target*: One target that includes a compiler that supports OpenMP and a path to an MPI installation.
- *Application*: Three applications: one for MPI only, one for OpenMP only, one for both MPI and OpenMP.
- *Measurement*: Three measurements:  one for MPI only, one for OpenMP only, one for both MPI and OpenMP.

Then for each case that I'm interested in I form experiments by selecting one target, one application, and one
measurement and execute the experiment as many times as I like to produce 1...N trials.  I can produce as many trials
as I like to get a good idea of performance variability in the system.  The gathered data is organized something like
this::

  Project (my-project)
    - Experiment (my-target, MPI, MPI-measurement)
      - Trial_1 ... Trial_N
    - Experiment (my-target, OpenMP, OpenMP-measurement)
      - Trial_1 ... Trial_N
    - Experiment (my-target, MPI_OpenMP, MPI_OpenMP-measurement)
      - Trial_1 ... Trial_N
