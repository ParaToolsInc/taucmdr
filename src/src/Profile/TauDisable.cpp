/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 1997  						   	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/***************************************************************************
**	File 		: TauFAPI.cpp					  **
**	Description 	: TAU Profiling Package wrapper for F77/F90	  **
**	Contact		: tau-team@cs.uoregon.edu 		 	  **
**	Documentation	: See http://www.cs.uoregon.edu/research/tau      **
***************************************************************************/

/* Fortran Wrapper layer for TAU Portable Profiling */

/*****************************************************************************
* The following routines are called by the Fortran program and they in turn
* invoke the corresponding C routines. 
*****************************************************************************/
#include <stdio.h>

typedef unsigned int TauGroup_t;

extern "C" {

void tau_profile_timer_(void **ptr, char *fname, int *flen, char *type, int *tlen, unsigned int *group)
{
}


void tau_profile_start_(void **profiler)
{ 
}

void tau_profile_stop_(void **profiler)
{
}

void tau_profile_exit_(char *msg)
{
}

void tau_db_dump_(void)
{
}

void tau_db_dump_prefix_(char *prefix)
{
}

void tau_profile_init_(int *argc, char **argv)
{
}

void tau_profile_set_node_(int *node)
{
} 

void tau_profile_set_context_(int *context)
{
}

void tau_register_thread_(void)
{
}
/* For IBM compiler */

void tau_profile_timer(void **ptr, char *fname, int *flen, char *type, int *tlen, unsigned int *group)
{
}


void tau_profile_start(void **profiler)
{ 
}

void tau_profile_stop(void **profiler)
{
}

void tau_profile_exit(char *msg)
{
}

void tau_db_dump(void)
{
}

void tau_db_dump_prefix(char *prefix)
{
}

void tau_profile_init(int *argc, char **argv)
{
}

void tau_profile_set_node(int *node)
{
} 

void tau_profile_set_context(int *context)
{
}

/* Cray F90 specific extensions */
#ifdef CRAYKAI
void TAU_REGISTER_THREAD(void)
{
}
#endif /* CRAYKAI */

void tau_trace_sendmsg_(int *type, int *destination, int *length)
{
}

void tau_trace_recvmsg_(int *type, int *source, int *length)
{
}

void tau_register_event_(void **ptr, char *event_name, int *flen)
{
}

void tau_event_(void **ptr, double *data)
{
}

void tau_report_statistics_(void)
{
}

void tau_report_thread_statistics_(void)
{
}

/* dynamic and static timers and phases */
void tau_phase_create_static_(void **ptr, char *infname, int slen)
{
}

void tau_phase_create_dynamic_(void **ptr, char *infname, int slen)
{
}

void tau_profile_timer_dynamic_(void **ptr, char *infname, int slen)
{ 
}

void tau_phase_start_(void **profiler)
{
}

void tau_phase_stop_(void **profiler)
{
}

#ifdef linux
#include <pthread.h>
#pragma weak pthread_create
#pragma weak pthread_exit
int tau_pthread_create (pthread_t * threadp,
		    const pthread_attr_t *attr,
		    void *(*start_routine) (void *),
		    void *arg) {
  return pthread_create(threadp, attr, start_routine, arg);
}

void tau_pthread_exit (void *value_ptr) {
  pthread_exit(value_ptr);
}
#endif

/* Cray F90 specific extensions */
#ifdef CRAYKAI
void _main();
void TAU_PROFILE_TIMER(void **ptr, char *fname, int *flen)
{
}

void TAU_PROFILE_START(void **profiler)
{
}

void TAU_PROFILE_STOP(void **profiler)
{
}

void TAU_PROFILE_EXIT(char *msg)
{
}

void TAU_DB_DUMP(void)
{
}

void TAU_DB_DUMP_PREFIX(char *prefix)
{
}

void TAU_PROFILE_INIT()
{
  _main();
}

void TAU_PROFILE_SET_NODE(int *node)
{
}

void TAU_PROFILE_SET_CONTEXT(int *context)
{
}

void TAU_TRACE_SENDMSG(int *type, int *destination, int *length)
{
}

void TAU_TRACE_RECVMSG(int *type, int *source, int *length)
{
}

void TAU_REGISTER_EVENT(void **ptr, char *event_name, int *flen)
{
}

void TAU_EVENT(void **ptr, double *data)
{
}

void TAU_REPORT_STATISTICS(void)
{
}

void TAU_REPORT_THREAD_STATISTICS(void)
{
}

/* dynamic and static timers and phases */
void TAU_PHASE_CREATE_STATIC(void **ptr, char *infname, int slen)
{
}

void TAU_PHASE_CREATE_DYNAMIC(void **ptr, char *infname, int slen)
{
}

void TAU_PROFILE_TIMER_DYNAMIC(void **ptr, char *infname, int slen)
{ 
}

void TAU_PHASE_START(void **profiler)
{
}

void TAU_PHASE_STOP(void **profiler)
{
}
#endif /* CRAYKAI */

////////////////////////////////////////////////////////////
// Dummy C wrappers
////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////////////
void * tau_get_profiler(char *fname, char *type, TauGroup_t group)
{
  return 0;
}

///////////////////////////////////////////////////////////////////////////
void tau_start_timer(void *profiler, int tid)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_stop_timer(void *profiler, int tid)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_exit(char * msg)
{
}
///////////////////////////////////////////////////////////////////////////
void tau_init(int argc, char **argv)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_set_node(int node)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_set_context(int context)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_callstack(void)
{
}


///////////////////////////////////////////////////////////////////////////
void tau_register_thread(void)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_trace_sendmsg(int type, int destination, int length)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_trace_recvmsg(int type, int source, int length)
{
}

///////////////////////////////////////////////////////////////////////////
// User Defined Events 
///////////////////////////////////////////////////////////////////////////
void * tau_get_userevent(char *name)
{
  return 0;
}

///////////////////////////////////////////////////////////////////////////
void tau_userevent(void *ue, double data)
{
} 

///////////////////////////////////////////////////////////////////////////
void tau_report_statistics(void)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_report_thread_statistics(void)
{
}

///////////////////////////////////////////////////////////////////////////
void tau_event_disable_min(void *ue)
{
} 

///////////////////////////////////////////////////////////////////////////
void tau_event_disable_max(void *ue)
{
} 

///////////////////////////////////////////////////////////////////////////
void tau_event_disable_mean(void *ue)
{
} 

///////////////////////////////////////////////////////////////////////////
void tau_event_disable_stddev(void *ue)
{
} 
///////////////////////////////////////////////////////////////////////////
/* dynamic and static timers and phases */
void tau_phase_create_static(void **ptr, char *infname, int slen)
{
}

void tau_phase_create_dynamic(void **ptr, char *infname, int slen)
{
}

void tau_profile_timer_dynamic(void **ptr, char *infname, int slen)
{ 
}

void tau_phase_start(void **profiler)
{
}

void tau_phase_stop(void **profiler)
{
}
///////////////////////////////////////////////////////////////////////////

void tau_profile_timer__(void **ptr, char *fname, int *flen, char *type, int *tlen, unsigned int *group)
{
}


void tau_profile_start__(void **profiler)
{ 
}

void tau_profile_stop__(void **profiler)
{
}

void tau_profile_exit__(char *msg)
{
}

void tau_db_dump__(void)
{
}

void tau_db_dump_prefix__(char *prefix)
{
}

void tau_profile_init__(int *argc, char **argv)
{
}

void tau_profile_set_node__(int *node)
{
} 

void tau_profile_set_context__(int *context)
{
}

void tau_register_thread__(void)
{
}

/* dynamic and static timers and phases */
void tau_phase_create_static__(void **ptr, char *infname, int slen)
{
}

void tau_phase_create_dynamic__(void **ptr, char *infname, int slen)
{
}

void tau_profile_timer_dynamic__(void **ptr, char *infname, int slen)
{ 
}

void tau_phase_start__(void **profiler)
{
}

void tau_phase_stop__(void **profiler)
{
}
///////////////////////////////////////////////////////////////////////////
// Memory, MAGNET/MUSE event stubs
///////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////
void tau_track_memory(void)
{
} 

void tau_track_memory_here(void)
{
} 

void tau_track_muse_events(void)
{
} 

void tau_enable_tracking_memory(void)
{
} 

void tau_disable_tracking_memory(void)
{
} 

void tau_enable_tracking_muse_events(void)
{
} 

void tau_disable_tracking_muse_events(void)
{
} 

void tau_set_interrupt_interval(int value)
{
} 


//////////////////////////////////////////////////////
void tau_track_memory_(void)
{
} 

void tau_track_memory_here_(void)
{
} 

void tau_track_muse_events_(void)
{
} 

void tau_enable_tracking_memory_(void)
{
} 

void tau_disable_tracking_memory_(void)
{
} 

void tau_enable_tracking_muse_events_(void)
{
} 

void tau_disable_tracking_muse_events_(void)
{
} 

void tau_set_interrupt_interval_(int value)
{
} 

////////////////////////////////////////////////////////////////////////
void tau_track_memory__(void)
{
} 

void tau_track_memory_here__(void)
{
} 

void tau_track_muse_events__(void)
{
} 

void tau_enable_tracking_memory__(void)
{
} 

void tau_disable_tracking_memory__(void)
{
} 

void tau_enable_tracking_muse_events__(void)
{
} 

void tau_disable_tracking_muse_events__(void)
{
} 

void tau_set_interrupt_interval__(int value)
{
}

//////////////////////////////////////////////////////
// MEMORY, MUSE events API
//////////////////////////////////////////////////////
void TAU_TRACK_MEMORY(void)
{
} 

void TAU_TRACK_MEMORY_HERE(void)
{
} 

void TAU_TRACK_MUSE_EVENTS(void)
{
} 

void TAU_ENABLE_TRACKING_MEMORY(void)
{
} 

void TAU_DISABLE_TRACKING_MEMORY(void)
{
} 

void TAU_ENABLE_TRACKING_MUSE_EVENTS(void)
{
} 

void TAU_DISABLE_TRACKING_MUSE_EVENTS(void)
{
} 

void TAU_SET_INTERRUPT_INTERVAL(int value)
{
} 

void Tau_start_timer(void * timer, int phase, int tid) 
{
}

void Tau_stop_timer(void *, int tid) 
{
}
 
void Tau_create_top_level_timer_if_necessary(void)
{
}

void Tau_stop_top_level_timer_if_necessary(void)
{
}

void Tau_profile_c_timer(void **ptr, char *fname, char *type, TauGroup_t group, char *group_name)
{
}

int tau_totalnodes(int set_or_get, int value)
{
  return 0;
}

void Tau_trace_recvmsg(int type, int source, int length)
{
}

void Tau_trace_sendmsg(int type, int destination, int length)
{
}

void Tau_set_node(int node)
{
}


void Tau_bcast_data(int data)
{
}

void Tau_reduce_data(int data)
{
}

void Tau_alltoall_data(int data)
{
}

void Tau_scatter_data(int data)
{
}

void Tau_gather_data(int data)
{
}

void Tau_allgather_data(int data) 
{
}

void Tau_allreduce_data(int data)
{
}

void Tau_scan_data(int data)
{
}

void Tau_reducescatter_data(int data)
{
}

/* alloc/dealloc */
void TAU_ALLOC(void ** ptr, int* line, int *size, char *name, int slen)
{
}

void tau_alloc(void ** ptr, int* line, int *size, char *name, int slen)
{
}

void tau_alloc_(void ** ptr, int* line, int *size, char *name, int slen)
{
}

void tau_alloc__(void ** ptr, int* line, int *size, char *name, int slen)
{
}

void TAU_DEALLOC(void ** ptr, int* line, char *name, int slen) 
{
}

void tau_dealloc(void ** ptr, int* line, char *name, int slen) 
{
}

void tau_dealloc_(void ** ptr, int* line, char *name, int slen) 
{
}

void tau_dealloc__(void ** ptr, int* line, char *name, int slen) 
{
}

void Tau_init_ref(int* argc, char ***argv) 
{
}

void Tau_exit(char *)
{
}

void traceEntry(int id) {
  printf("TAU: traceEntry: id = %d\n", id);
}

void traceExit(int id) {
  printf("TAU: traceExit: id = %d\n", id);
}

void tau_trace_entry(int id) {
  printf("TAU: tau_trace_entry: id = %d\n", id);
}

void tau_trace_exit(int id) {
  printf("TAU: tau_trace_exit : id = %d\n", id);
}

void trace_register_func(char *origname, int id) {
  printf("TAU: trace_register_func : name = %s, id = %d\n", origname, id);
}

void tau_dyninst_cleanup() {
  printf("TAU: Inside tau_dyninst_cleanup\n");
}

void tau_dyninst_init(int isMPI) {
  printf("TAU: tau_dyninst_init: isMPI = %d\n", isMPI);
}

void  tau_register_func(char **func, char** file, int* lineno, 
  int id) {
  printf("TAU: tau_register_func : name = %s, file = %s, line no = %d, id = %d\n", 
	*func, *file, *lineno, id);
}

void  tau_register_loop(char **func, char** file, int* lineno, 
  int id) {
  printf("TAU: tau_register_loop : name = %s, file = %s, line no = %d, id = %d\n", 
	*func, *file, *lineno, id);
}
  
////////////////////////////////////////////////////////////////////////////
} /* extern "C" */

/***************************************************************************
 * $RCSfile: TauDisable.cpp,v $   $Author: sameer $
 * $Revision: 1.16 $   $Date: 2009/03/26 19:15:39 $
 * POOMA_VERSION_ID: $Id: TauDisable.cpp,v 1.16 2009/03/26 19:15:39 sameer Exp $ 
 ***************************************************************************/
