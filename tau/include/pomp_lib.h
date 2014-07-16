/*************************************************************************/
/* OPARI Version 1.1                                                     */
/* Copyright (c) 2001-2005                                                    */
/* Forschungszentrum Juelich, Zentralinstitut fuer Angewandte Mathematik */
/*************************************************************************/

#ifndef POMP_LIB_H
#define POMP_LIB_H

#ifdef _OPENMP
#include <omp.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

struct ompregdescr {
  char* name;                  /* name of construct                     */
  char* sub_name;              /* optional: region name                 */
  int   num_sections;          /* sections only: number of sections     */
  char* file_name;             /* source code location                  */
  int   begin_first_line;      /* line number first line opening pragma */
  int   begin_last_line;       /* line number last  line opening pragma */
  int   end_first_line;        /* line number first line closing pragma */
  int   end_last_line;         /* line number last  line closing pragma */
  void* data;                  /* space for performance data            */
  struct ompregdescr* next;    /* for linking                           */
};

extern int POMP_MAX_ID;

extern struct ompregdescr* pomp_rd_table[];

extern void POMP_Finalize();
extern void POMP_Init();
extern void POMP_Off();
extern void POMP_On();
extern void POMP_Begin(struct ompregdescr* r);
extern void POMP_End(struct ompregdescr* r);

#ifdef _OPENMP
extern void POMP_Atomic_enter(struct ompregdescr* r);
extern void POMP_Atomic_exit(struct ompregdescr* r);
extern void POMP_Barrier_enter(struct ompregdescr* r);
extern void POMP_Barrier_exit(struct ompregdescr* r);
extern void POMP_Flush_enter(struct ompregdescr* r);
extern void POMP_Flush_exit(struct ompregdescr* r);
extern void POMP_Critical_begin(struct ompregdescr* r);
extern void POMP_Critical_end(struct ompregdescr* r);
extern void POMP_Critical_enter(struct ompregdescr* r);
extern void POMP_Critical_exit(struct ompregdescr* r);
extern void POMP_For_enter(struct ompregdescr* r);
extern void POMP_For_exit(struct ompregdescr* r);
extern void POMP_Master_begin(struct ompregdescr* r);
extern void POMP_Master_end(struct ompregdescr* r);
extern void POMP_Parallel_begin(struct ompregdescr* r);
extern void POMP_Parallel_end(struct ompregdescr* r);
extern void POMP_Parallel_fork(struct ompregdescr* r);
extern void POMP_Parallel_join(struct ompregdescr* r);
extern void POMP_Section_begin(struct ompregdescr* r);
extern void POMP_Section_end(struct ompregdescr* r);
extern void POMP_Sections_enter(struct ompregdescr* r);
extern void POMP_Sections_exit(struct ompregdescr* r);
extern void POMP_Single_begin(struct ompregdescr* r);
extern void POMP_Single_end(struct ompregdescr* r);
extern void POMP_Single_enter(struct ompregdescr* r);
extern void POMP_Single_exit(struct ompregdescr* r);
extern void POMP_Workshare_enter(struct ompregdescr* r);
extern void POMP_Workshare_exit(struct ompregdescr* r);

extern void POMP_Init_lock(omp_lock_t *s);
extern void POMP_Destroy_lock(omp_lock_t *s);
extern void POMP_Set_lock(omp_lock_t *s);
extern void POMP_Unset_lock(omp_lock_t *s);
extern int  POMP_Test_lock(omp_lock_t *s);
extern void POMP_Init_nest_lock(omp_nest_lock_t *s);
extern void POMP_Destroy_nest_lock(omp_nest_lock_t *s);
extern void POMP_Set_nest_lock(omp_nest_lock_t *s);
extern void POMP_Unset_nest_lock(omp_nest_lock_t *s);
extern int  POMP_Test_nest_lock(omp_nest_lock_t *s);
#endif

extern int pomp_tracing;

#ifdef __cplusplus
}
#endif

#endif
