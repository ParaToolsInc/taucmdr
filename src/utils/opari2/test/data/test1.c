/*
 * This file is part of the Score-P software (http://www.score-p.org)
 *
 * Copyright (c) 2009-2011,
 *    RWTH Aachen University, Germany
 *    Gesellschaft fuer numerische Simulation mbH Braunschweig, Germany
 *    Technische Universitaet Dresden, Germany
 *    University of Oregon, Eugene, USA
 *    Forschungszentrum Juelich GmbH, Germany
 *    German Research School for Simulation Sciences GmbH, Juelich/Aachen, Germany
 *    Technische Universitaet Muenchen, Germany
 *
 * See the COPYING file in the package base directory for details.
 *
 * Testfile for automated testing of OPARI2
 *
 * @authors Bernd Mohr, Peter Philippen
 *
 * @brief Test the parsers ability to find directives and filter strings and comments.
 */

#include <stdio.h>
#ifdef _OPENMP
   #include <omp.h>  //just testing
#endif

int main() {
  printf("before...\n");

  //************************************************
  //* The following pragmas should be instrumented *
  //************************************************

  #pragma omp parallel
  {{
    printf("parallel 1...\n");
  }} //end

  # /*complicated*/ pragma \
                    omp \
    /*more*/        parallel
  {
    printf("parallel 2...\n");
  }
  
  //**************************************
  //* The following should be ignored    *
  //**************************************
  //#pragma omp parallel
  {
    //printf("parallel 1...\n");
  }

/*
  #pragma omp parallel
  {
    printf("parallel 1...\n");
  }
*/


  {
    printf("#pragma omp parallel");
    //  printf("#pragma omp parallel");
    /*  printf("#pragma omp parallel");*/
    /*
    printf("#pragma omp parallel");
    */
    printf("\" and continuation \
in the next line #pragma omp parallel\" \
and especially strange escape character usage\\
n");
  }

  printf("after...\n");
}
