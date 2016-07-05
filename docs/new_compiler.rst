How to Add Support for a New Compiler
=====================================

TL;DR
-----

1. Check existing family definitions in :any:`tau.cf.compiler`.  If the missing compiler's family is already 
   defined then just update the existing definition.  Otherwise declare a new family using the existing declarations
   as an example.  
2. Update :any:`TauInstallation` with any special cases or goofy flags TAU might need to work with the new compiler,
   e.g. ``fc_magic_map`` in :any:`TauInstallation.configure`

-------------------------------------------------------------------------------

The TAU Performance System is extremely sensitive to changes in compilers, so it's important that TAU Commander know
which compilers were used to build both TAU and the user's application.  To help with this, TAU Commander maintains a 
*compiler information knowledgebase* that declares relationships between various compilers, the commands used to invoke
them, and the commands that wrap them.

The knowledgebase looks a bit like this:

.. image:: _static/tau.cf.compiler.png
   :height: 400px

When TAU Commander encounters a compiler command it performs *compiler resolution* to determine all relevent 
information about that compiler.  Given two pieces of information about a compiler (e.g. command line string and role), 
TAU Commander uses the knowlegebase to discover missing information (e.g. family).


Compiler Roles (:any:`CompilerRole`)
------------------------------------

Each individual compiler has a *Role* that is represented by an instance of the :any:`CompilerRole` class.  A 
compiler's role maps a compiler to it's primary language via a keyword.  For example, the `g++` compiler primarily 
functions as a C++ compiler.  It's role keyword is "CXX" and it's language is "C++".  Roles are declared in
:any:`tau.cf.compiler`, e.g.::

   CC_ROLE = CompilerRole('CC', 'C', True)
   CXX_ROLE = CompilerRole('CXX', 'C++', True)
   FC_ROLE = CompilerRole('FC', 'Fortran')
   UPC_ROLE = CompilerRole('UPC', 'Universal Parallel C')


Compiler Families (:any:`CompilerFamily`)
-----------------------------------------

The compiler's family assigns roles to compiler commands and tracks the various command line options used by that
compiler family.  The family name (:any:`CompilerFamily.name`) provides a convinent way to operate on many different
compiler commands at once.  Families are declared in :any:`tau.cf.compiler`, e.g::

   INTEL_COMPILERS = CompilerFamily('Intel', family_regex=r'Intel Corporation')
   INTEL_COMPILERS.add(CC_ROLE, 'icc')
   INTEL_COMPILERS.add(CXX_ROLE, 'icpc')
   INTEL_COMPILERS.add(FC_ROLE, 'ifort')

This declares a new compiler family named "Intel" with a C compiler named "icc", a C++ compiler named "icpc", and a
Forran compiler named "ifort".  If TAU Commander ever needs to discover what family a compiler belongs to, it will 
match the regular expression "Intel Corporation" in the output produced by running the compiler with the version
flags specified by the family (:any:`CompilerFamily.version_flags`).

Multiple compilers can be specified for each role.  The IBM BlueGene/Q Fortran compilers are a bit crazy::

   IBM_BGQ_COMPILERS.add(FC_ROLE, 'bgxlf', 'bgxlf_r', 'bgf77', 'bgfort77', 'bgxlf90', 'bgxlf90_r', 'bgf90', 
                      'bgxlf95', 'bgxlf95_r', 'bgf95', 'bgxlf2003', 'bgxlf2003_r', 'bgf2003', 'bgxlf2008', 
                      'bgxlf2008_r', 'bgf2008')
   
The first compiler command after the role (e.g. ``bgxlf``) is the *preferred* compiler for the role.  That is,
if TAU Commander is ever in a situation where it knows it needs to compile a Fortran file on BlueGene/Q with IBM
compilers then it will first attempt the operation with ``bgxlf``.  If that fails, it will try the next compiler,
and the next, and so on until it ultimately succeeds admits failure.

Compiler Information (:any:`CompilerInfo`)
------------------------------------------

A :any:`CompilerInfo` instance is the abstract representation of a compiler.  It connects a compiler command with it's
role and family. The process of compiler resultion completes by instantiating :any:`CompilerInfo`, i.e. once TAU 
Commander can create a CompilerInfo object then TAU Commander is fully aware of the compiler.  

Note that :any:`CompilerInfo.command` *may not* be the actual command used in the system.  For example, if someone
writes a compiler wrapper script called "intel-c-15" that invokes "icc" then :any:`CompilerInfo.command` will be "icc"
because that is the **real** compiler command.  The connection between the wrapper script and the real command is
made in :any:`InstalledCompiler`.  (This is a very common case on Cray systems where all compilers are invoked via
the Cray compiler wrappers ``cc``, ``CC``, and ``ftn``.)

Compiler Installations (:any:`InstalledCompiler`)
-------------------------------------------------

A :any:`CompilerInfo` instance is abstract.  In the real world, compilers are renamed, wrapped, symlinked, and
generally hacked in ways that cannot be anticipated.  An instance of the :any:`InstalledCompiler` class links a
command in the system (e.g. ``/opt/intel/16.2/bin/intel64/icc``) with the :any:`CompilerInfo` instance that represents
that compiler (e.g. the Intel C compiler, version 16.2), and tracks the additional command line flags that the compiler
may need.  :any:`InstalledCompiler` also tracks compiler *wrappers*. MPI is probably the most common case of compiler 
wrapping, where the command ``mpicc`` is really a script or short program that invokes a C compiler.  Suppose the 
current experiment is configured with ``/usr/local/bin/mpicc`` as the MPI compiler, and that MPI compiler invokes the 
Portland Group C compiler, ``pgcc``.  The wrapped member of the InstalledCompiler instace for ``/usr/local/bin/mpicc`` 
will be another InstalledCompiler instance identifying ``pgcc`` as an installed Portland Group C compiler.  Wrappers
can wrap wrappers as deep as you like, as long as they don't recurse.

Compiler Resolution Example
---------------------------

The assocations defined in the compiler knowlegebase are very powerful.  TAU Commander can draw conclusions about which
compilers should be used, and which compiler flags should be used, at any point in the workflow given a relatively small
ammount of information.  Consider this target creation command::

   tau target create --host-compilers=Intel --mpi-compilers=System

Because the knowledgebase specifies the individual compiler commands for each role in the Intel compiler family, that
command is automatically expanded to::

   tau target create --cc=icc --cxx=icpc --fc=ifort --mpi-cc=mpicc --mpi-cxx=mpicxx --mpi-fc=mpif90

Furthermore, TAU Commander will record in this configuration that ``mpicc`` is a compiler wrapper for the ``icc``
command. Now suppose the user invokes a compilation command::

   tau mpicc foo.c -o foo
   
TAU Commander will probe ``mpicc`` using :any:`CompilerFamily.version_flags` to determine if ``mpicc`` is currently
wrapping ``icc``.  (For example, perhaps the user has forgotten to load the appropriate environment modules.)  
If ``mpicc`` does indeed wrap ``icc``, TAU Commander will check for a TAU installation that supports MPI and 
was configured with compatible Intel compilers.  If no such configuration exists, TAU Commander will create one. 
It will use :any:`CompilerFamily.show_wrapper_flags` to discover how ``mpicc`` alters the ``icc`` command line, and
combine this information with information from the compiler role and family to generate the correct TAU configration
command line, e.g.::

   ./configure -cc=icc -c++=icpc -fortran=intel \
               -mpi -mpiinc=/include/path/a#/include/path/b -mpilib=/lib/path/a#/lib/path/b -mpilibrary="-la -lb"
               .... additional options
               
Note that ``-fortran=intel`` is specified on the TAU command line, even though the original command ``tau mpicc``
had nothing to do with Fortran.  Even more interesting, "intel" isn't the name of the Fortran Intel compiler, but TAU
Commander knows that TAU needs this magic word to be correctly configured for Intel compilers.

Now consider a different case where an incompatible compiler is used.  For example, the currently selected experiment
is configured with GNU compilers but the user issues the command::

   tau ifort foo.f90 -o foo
   
Because TAU Commander knows that "ifort" is an Intel Fortran compiler command it will abort the compilation and tell
the user that they must change their experimental configuration to support Intel compilers before proceeding.  This
resolves a major pain point in TAU where using a TAU configuration for one compiler on code built with a different
compiler can cause all sorts of problems.
