Installing TAU Commander
========================

TAU Commander needs Python 3.11 or newer.  It installs into its own virtual environment with
`uv <https://docs.astral.sh/uv/>`_ or `pipx <https://pipx.pypa.io/>`_.  Don't install it into a
Python environment you use for other work: when TAU Commander profiles Python code, packages in that
environment could conflict with its own.

TAU Commander builds TAU and the packages it uses from source, so it needs C, C++ and Fortran
compilers, ``make``, ``cmake`` and ``m4``.  Installing from a checkout also needs ``git``.  On Ubuntu::

   sudo apt install gcc g++ gfortran make cmake m4 git

Most people want a :ref:`per-user-install`.  In a :ref:`shared-install`, a system administrator installs
TAU Commander once and builds TAU for all users.  Either kind works without internet access after an
:ref:`offline-install`.


.. _per-user-install:

Per-user install
----------------

Install from a checkout of TAU Commander::

   uv tool install /path/to/taucmdr

or, with pipx::

   pipx install /path/to/taucmdr

Either one installs ``tau`` in ``~/.local/bin``.  If that directory isn't on your ``PATH``,
``uv tool update-shell`` (or ``pipx ensurepath``) adds it.  Then initialize a project in the directory
with your code::

   cd /path/to/your/code
   tau initialize

It is not necessary to configure anything ahead of time.  The first time a project needs TAU or packages it depends upon,
TAU Commander downloads and builds them, and later projects reuse them.


.. _shared-install:

Shared install
--------------

In a shared install, a system administrator installs TAU Commander in a shared directory and builds TAU
configurations there once.  Users load a module file and use those builds.  TAU Commander builds
anything else a user needs that is not present at system-level in their own ``~/.local/taucmdr``.

The shared builds go in a *system prefix*, a directory set by the ``TAUCMDR_SYSTEM_PREFIX`` environment
variable.  Without it there's no shared level, and each user's installation builds private copies of TAU
and its dependencies.

These example steps use ``/opt/taucmdr`` and a group named ``tauadmin`` for the administrators who maintain it.
Adapt these steps for your own system.

1. Create the directories.  They belong to the administrators' group and have the setgid bit set, so
   everything installed and built there belongs to that group too::

      install -d -m 2775 -g tauadmin /opt/taucmdr /opt/taucmdr/system

2. Install TAU Commander with uv.  ``UV_PYTHON_INSTALL_DIR`` keeps the Python interpreter that uv downloads in the
   shared directory as well, as otherwise the installed ``tau`` would use a Python in the administrator's home directory,
   which users can't read::

      export UV_TOOL_DIR=/opt/taucmdr/tools
      export UV_TOOL_BIN_DIR=/opt/taucmdr/bin
      export UV_PYTHON_INSTALL_DIR=/opt/taucmdr/python
      uv tool install --python 3.12 /path/to/taucmdr

   uv warns that ``/opt/taucmdr/bin`` isn't on your ``PATH``; the module file created in the next step adds it.

3. Write a module file in a directory of module files, here ``/opt/taucmdr/modulefiles``.  For Lmod,
   ``taucmdr.lua``:

   .. code-block:: lua

      prepend_path("PATH", "/opt/taucmdr/bin")
      setenv("TAUCMDR_SYSTEM_PREFIX", "/opt/taucmdr/system")

   For Environment Modules (Tcl), ``taucmdr``:

   .. code-block:: tcl

      #%Module1.0
      prepend-path PATH /opt/taucmdr/bin
      setenv TAUCMDR_SYSTEM_PREFIX /opt/taucmdr/system

4. Build the TAU configurations with the module loaded::

      module use /opt/taucmdr/modulefiles
      module load taucmdr
      tau system configure

   This builds the packages TAU uses, and TAU configurations for every combination of PAPI, OpenMP,
   MPI, SHMEM and CUDA that the compilers allow.  Users' projects reuse those packages, and TAU
   Commander builds any other TAU configuration a project needs in the user's own storage.  The other
   ``tau initialize`` options choose the compilers and packages, e.g. ``--mpi-wrappers``.
   ``--tau-config=minimal`` builds only one small TAU configuration, which is quicker for checking
   the installation, but then each user's installation will build the packages TAU requires.

5. As root, make the installation read-only for everyone else::

      chmod -R a+rX,o-w /opt/taucmdr

Users then load the module and run ``tau initialize`` as usual.

After upgrading TAU Commander, run ``tau system configure`` again to ensure that any new
TAU configurations introduced by the new version are rebuilt.

To use an existing TAU installation by default instead of the ones TAU Commander builds, give its
path::

   tau system configure --tau-config=/path/to/tau


.. _offline-install:

Offline install
---------------

On a system without internet access, TAU Commander and its Python dependencies install from a
directory of wheels, and TAU and the packages it builds come from a directory of source archives.
You prepare both on a computer with internet access and copy them over.

On a computer with internet access:

1. Build TAU Commander's wheel and download its dependencies.  They're pure Python, so one
   ``wheelhouse`` works on any platform with a supported Python::

      cd /path/to/taucmdr
      uv build --wheel --out-dir wheelhouse
      python3 -m pip download --dest wheelhouse wheelhouse/taucmdr-*.whl

2. Download the source archives of TAU and the packages it builds (about 1.2 GB) into ``bundle``::

      uv tool install /path/to/taucmdr
      tau system fetch bundle

   ``tau system fetch`` exits with an error if it couldn't download an archive from any of its
   mirrors; run it again to retry.

3. Copy ``wheelhouse``, ``bundle`` and the ``uv`` executable (``which uv``) to the other computer.

On the computer without internet access:

4. Ensure that Python 3.11 or newer is installed.

5. Install TAU Commander from the wheelhouse::

      uv tool install --offline --no-index --find-links wheelhouse --python /usr/bin/python3.12 taucmdr

   With pipx instead::

      pipx install --python /usr/bin/python3.12 --pip-args="--no-index --find-links=wheelhouse" taucmdr

6. Add the source archives to a system prefix.  For a shared install, follow :ref:`shared-install`
   with two changes.  In step 2, install from the wheelhouse as in step 5 above, with ``--python``
   set to a Python that users can read.  Before step 4, import the archives::

      tau system import bundle

   For a per-user install, set ``TAUCMDR_SYSTEM_PREFIX`` to a directory of your own and import the
   archives there.  Set it in a startup file read by every shell so that
   scripts and batch jobs get it too::

      export TAUCMDR_SYSTEM_PREFIX=$HOME/taucmdr-system
      tau system import bundle

