## -*- mode: autoconf -*-

## 
## This file is part of the Score-P software (http://www.score-p.org)
##
## Copyright (c) 2009-2011, 
##    RWTH Aachen University, Germany
##    Gesellschaft fuer numerische Simulation mbH Braunschweig, Germany
##    Technische Universitaet Dresden, Germany
##    University of Oregon, Eugene, USA
##    Forschungszentrum Juelich GmbH, Germany
##    German Research School for Simulation Sciences GmbH, Juelich/Aachen, Germany
##    Technische Universitaet Muenchen, Germany
##
## See the COPYING file in the package base directory for details.
##


# AC_SCOREP_DOXYGEN
#----------------
# Check doxygen related stuff, sets some output variables and the
# AM_CONDITIONALs HAVE_DOXYGEN and HAVE_DOXYGEN_LATEX.
#
AC_DEFUN([AC_SCOREP_DOXYGEN],
[
#if test -z "$have_svnversion"; then
#  AC_CHECK_PROG([have_svnversion], [svnversion], [yes], [no],,)
#fi
AC_PATH_PROG([DOXYGEN], [doxygen])
AM_CONDITIONAL(HAVE_DOXYGEN, test "x${DOXYGEN}" != "x")

have_doxygen_latex="no"
AM_COND_IF([HAVE_DOXYGEN],[
   AC_CHECK_PROG([have_dot], [dot], [yes], [no],,)
   AC_CHECK_PROG([have_pdflatex], [pdflatex], [yes], [no],,)
   AC_CHECK_PROG([have_makeindex], [makeindex], [yes], [no],,)
   if test "x${have_pdflatex}" = xyes && test "x${have_makeindex}" = xyes; then
      have_doxygen_latex="yes"
   fi
])
AC_SUBST([have_doxygen_latex])
AM_CONDITIONAL(HAVE_DOXYGEN_LATEX, test "x${have_doxygen_latex}" = xyes)

# ac_scorep_doxygen_distdir may be passed in from upper level configure
if test ! -n "$ac_scorep_doxygen_distdir"; then
   ac_scorep_doxygen_distdir=""
fi
AC_SUBST([ac_scorep_doxygen_distdir])

])


# AC_SCOREP_DOXYGEN_CONFIG_FILES
#----------------
# Generate Score-P related doxygen configuration files.
#
AC_DEFUN([AC_SCOREP_DOXYGEN_CONFIG_FILES],
[
AC_REQUIRE([AC_SCOREP_SVN_CONTROLLED])
if test "x${ac_scorep_svn_controlled}" = "xyes"; then
   AC_CONFIG_FILES([doc/doxygen-user-common.cfg:vendor/common/build_related/doxygen/doxygen-user-common.cfg.in])
   AC_CONFIG_FILES([doc/doxygen-user-component.cfg:doc/doxygen-user/doxygen-user-component.cfg.in])
   AC_CONFIG_FILES([doc/doxygen-dev.cfg:doc/doxygen-dev/doxygen-dev.cfg.in])
fi
])
