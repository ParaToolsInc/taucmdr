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
 * @brief Test that the insertion of wrapper functions works correctly, but ONLY on supported functions.
 */

#include <omp.h>

int main() {
  omp_lock_t       lock1;
  omp_nest_lock_t  lock2;
  omp_sched_t      sched;
  int              mod;

  //**************************************************
  //* Should be replaced by wrapper functions        *
  //*  regardless of "distractions"                  *
  //**************************************************

  omp_init_lock(&lock1); omp_init_nest_lock(&lock2); omp_set_lock(&lock1);
  omp_set_nest_lock(&lock2);  // omp_set_nest_lock(&lock2); 
  omp_unset_lock(&lock1); /*omp_unset_lock(&lock1);*/ omp_unset_nest_lock(&lock2);
  omp_test_lock(&lock1);/*
  omp_test_lock(&lock1);
  */ omp_test_nest_lock(&lock2);

  omp_destroy_lock(&lock1);
  omp_destroy_nest_lock(&lock2);


  //**************************************************
  //* Not now, but planned for the future!           *
  //**************************************************

  omp_set_num_threads(4);
  omp_set_dynamic(0);
  omp_set_schedule(omp_sched_static, 1);
  omp_set_nested(0);
  omp_set_max_active_levels(2);

  //**************************************************
  //* No replacement beyond this point!              *
  //**************************************************

  omp_get_num_threads();
  omp_get_max_threads(); 
  omp_get_thread_num();
  omp_get_num_procs();
  omp_in_parallel();

  omp_get_nested();
  omp_get_dynamic();
  omp_get_schedule(&sched, &mod);
  omp_get_thread_limit();
  omp_get_max_active_levels();
  omp_get_level();
  omp_get_ancestor_thread_num(0);
  omp_get_team_size(0);
  omp_get_active_level();

  omp_get_wtime();
  omp_get_wtick();

  // omp_init_lock(i)
  /* -- omp_init_lock(i) -- */
  /* -- 
        omp_init_lock(i) 
                         -- */
  printf("omp_init_lock(i)   \n");  // omp_init_lock(i)
  printf("omp_init_lock(i)\"test\"omp_init_lock(i)omp_init_lock(i)\"\"\"\n");
}
