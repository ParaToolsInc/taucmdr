/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 1997-2009					   	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/***************************************************************************
**	File 		: Profiler.h					  **
**	Description 	: TAU Profiling Package API			  **
**	Contact		: tau-team@cs.uoregon.edu 		 	  **
**	Documentation	: See http://www.cs.uoregon.edu/research/tau      **
***************************************************************************/

#ifndef _TAU_API_H_
#define _TAU_API_H_

#ifdef TAU_ENABLED

#include <Profile/tau_types.h>
#include <Profile/TauMetaDataTypes.h>
#include <Profile/TauMon.h>
#include <string.h>

#if (defined(TAU_WINDOWS))
#pragma warning( disable : 4786 )
#define TAUDECL __cdecl
#else
#define TAUDECL
#endif /* TAU_WINDOWS */

/* The Fortran API uses function bindings instead of macro bindings.
 * Really, the following #ifndef block should be moved to a new TauCAPI.h file
 * since it only applies to C/C++.
 */
#ifndef TAU_FAPI

#ifndef TAU_DISABLE_API

/* define the easy to use API */
#define TAU_START(name) Tau_start(name)
#define TAU_STOP(name) Tau_stop(name)

/* easy API with tasks */
#define TAU_START_TASK(name, tid) Tau_pure_start_task(name, tid)
#define TAU_STOP_TASK(name, tid) Tau_pure_stop_task(name, tid)

/* for consistency, we provide the long form */
#define TAU_STATIC_TIMER_START TAU_START
#define TAU_STATIC_TIMER_STOP TAU_STOP

#else /* TAU_DISABLE_API is defined! Define these two to nulls */

#define TAU_START(name)
#define TAU_STOP(name)

#endif /* TAU_DISABLE_API */


#define TAU_PROFILE_TIMER(var,name, type, group) static void *var=NULL; Tau_profile_c_timer(&var, name, type, group, #group);
#define TAU_PROFILE_TIMER_DYNAMIC(var,name, type, group) void *var=NULL; Tau_profile_c_timer(&var, name, type, group, #group);

#define TAU_PROFILE_DECLARE_TIMER(var) static void *var=NULL;
#define TAU_PROFILE_CREATE_TIMER(var,name,type,group) Tau_profile_c_timer(&var, name, type, group, #group);

#define TAU_PROFILE_START(var) Tau_lite_start_timer(var, 0);
#define TAU_PROFILE_STOP(var) Tau_lite_stop_timer(var);
#define TAU_PROFILE_STMT(stmt) stmt;

/* TAU_PROFILE_CREATE_DYNAMIC_AUTO embeds the counter in the name. isPhase = 0 implies a timer */
#define TAU_PROFILE_CREATE_DYNAMIC_AUTO(var, name, type, group)  \
        void *var = NULL;\
        { \
          static int tau_dy_timer_counter = 1; \
          Tau_profile_dynamic_auto(tau_dy_timer_counter++, &var, name, type, group, #group, 0); \
        }

#define TAU_PHASE_CREATE_DYNAMIC_AUTO(var, name, type, group)  \
        void *var##finfo = NULL;\
        { \
          static int tau_dy_timer_counter = 1; \
          Tau_profile_dynamic_auto(tau_dy_timer_counter++, &var##finfo, name, type, group, #group, 0); \
        }

#define TAU_DYNAMIC_TIMER_START(name) Tau_dynamic_start(name, 0);
#define TAU_DYNAMIC_TIMER_STOP(name) Tau_dynamic_stop(name, 0);
#define TAU_DYNAMIC_PHASE_START(name) Tau_dynamic_start(name, 1);
#define TAU_DYNAMIC_PHASE_STOP(name) Tau_dynamic_stop(name, 1);

#define TAU_STATIC_PHASE_START(name) Tau_static_phase_start(name)
#define TAU_STATIC_PHASE_STOP(name)  Tau_static_phase_stop(name)

#define TAU_PHASE_CREATE_STATIC(var, name, type, group) static void *var##finfo = NULL; Tau_profile_c_timer(&var##finfo, name, type, group, Tau_phase_enable_once(#group, &var##finfo))

#define TAU_PHASE_CREATE_DYNAMIC(var, name, type, group) void *var##finfo = NULL; Tau_profile_c_timer(&var##finfo, name, type, group, Tau_phase_enable_once(#group, &var##finfo))

#define TAU_PHASE_START(var) Tau_start_timer(var##finfo, 1, Tau_get_thread())
#define TAU_PHASE_STOP(var) Tau_stop_timer(var##finfo, Tau_get_thread())

#define TAU_ENABLE_GROUP(group)			Tau_enable_group(group);
#define TAU_DISABLE_GROUP(group)		Tau_disable_group(group);
#define TAU_ENABLE_GROUP_NAME(group)            Tau_enable_group_name(group) 
#define TAU_DISABLE_GROUP_NAME(group)           Tau_disable_group_name(group)
#define TAU_ENABLE_ALL_GROUPS()            	Tau_enable_all_groups() 
#define TAU_DISABLE_ALL_GROUPS()            	Tau_disable_all_groups() 
#define TAU_DISABLE_GROUP_NAME(group)           Tau_disable_group_name(group)
#define TAU_GET_PROFILE_GROUP(group)            Tau_get_profile_group(group)

#define TAU_SET_USER_CLOCK_THREAD(value, tid)   Tau_set_user_clock_thread(value, tid);
#define TAU_SET_USER_CLOCK(value)               Tau_set_user_clock(value);
#define TAU_PROFILE_INIT(argc, argv)		Tau_init(argc, argv);
#define TAU_INIT(argc, argv)			Tau_init_ref(argc, argv);
#define TAU_PROFILE_STMT(stmt) stmt;
#define TAU_PROFILE_EXIT(msg)  			Tau_exit(msg);

#define TAU_PROFILE_SET_NODE(node) 		Tau_set_node(node);
#define TAU_PROFILE_GET_NODE()                  Tau_get_node();
#define TAU_PROFILE_SET_CONTEXT(context)	Tau_set_context(context);
#define TAU_PROFILE_GET_CONTEXT()               Tau_get_context();
#define TAU_PROFILE_SET_THREAD(thread)          Tau_set_thread(thread);
#define TAU_PROFILE_GET_THREAD()                Tau_get_thread();

#define TAU_PROFILE_SET_GROUP_NAME(newname) Tau_profile_set_group_name(tauFI,newname);
#define TAU_PROFILE_TIMER_SET_NAME(t, newname)  Tau_profile_set_name(t,newname);
#define TAU_PROFILE_TIMER_SET_TYPE(t, newname)  Tau_profile_set_type(t,newname);
#define TAU_PROFILE_TIMER_SET_GROUP(t, id) Tau_profile_set_group(t,id);
#define TAU_PROFILE_TIMER_SET_GROUP_NAME(t, newname) Tau_profile_set_group_name(t,newname);

#define TAU_PROFILE_TIMER_GET_NAME(timer) Tau_profile_get_name(timer)
#define TAU_PROFILE_TIMER_GET_TYPE(timer) Tau_profile_get_type(timer)
#define TAU_PROFILE_TIMER_GET_GROUP(timer) Tau_profile_get_group(timer)
#define TAU_PROFILE_TIMER_GET_GROUP_NAME(timer) Tau_profile_get_group_name(timer)

#define TAU_REGISTER_THREAD()			Tau_register_thread();	
#define TAU_REGISTER_FORK(nodeid, op) 		Tau_register_fork(nodeid, op);
#define TAU_ENABLE_INSTRUMENTATION()		Tau_enable_instrumentation();
#define TAU_DISABLE_INSTRUMENTATION()		Tau_disable_instrumentation();

/* DB Access */
#define TAU_DB_DUMP()                           Tau_dump();
#define TAU_DB_MERGED_DUMP()                    Tau_mergeProfiles();
#define TAU_DB_DUMP_PREFIX(prefix)              Tau_dump_prefix(prefix);
#define TAU_DB_DUMP_PREFIX_TASK(prefix, task)   Tau_dump_prefix_task(prefix, task);
#define TAU_DB_DUMP_INCR()                      Tau_dump_incr();
#define TAU_DB_PURGE()                          Tau_purge();
#define TAU_GET_FUNC_NAMES(functionList, num)   Tau_the_function_list(&functionList, &num);
#define TAU_DUMP_FUNC_NAMES()                   Tau_dump_function_names();
#define TAU_GET_COUNTER_NAMES(counterList, num) Tau_get_counter_names(&counterList, &num);
#define TAU_GET_FUNC_VALS(v1,v2,v3,v4,v5,v6,v7,v8) Tau_get_function_values(v1,v2,&v3,&v4,&v5,&v6,&v7,&v8);
#define TAU_DUMP_FUNC_VALS(functionList, num)   Tau_dump_function_values(functionList, num);
#define TAU_DUMP_FUNC_VALS_INCR(functionList, num)  Tau_dump_function_values_incr(functionList, num);
#define TAU_GET_EVENT_NAMES(eventList, num)     Tau_get_event_names(&eventList, &num);
#define TAU_GET_EVENT_VALS(v1,v2,v3,v4,v5,v6,v7)   Tau_get_event_vals(v1,v2,&v3,&v4,&v5,&v6,&v7);

/* Runtime "context" access */
#define TAU_QUERY_DECLARE_EVENT(event)            void *event;
#define TAU_QUERY_GET_CURRENT_EVENT(event)        event = Tau_query_current_event();
#define TAU_QUERY_GET_EVENT_NAME(event, str)      str = Tau_query_event_name(event);
#define TAU_QUERY_GET_PARENT_EVENT(event)         event = Tau_query_parent_event(event);

/* Atomic Events */
#define TAU_REGISTER_EVENT(event, name)	static void *event = 0; \
                                 if (event == 0) event = Tau_get_userevent(name);
#define TAU_PROFILER_REGISTER_EVENT(e, msg) TauUserEvent* e () { \
	static TauUserEvent u(msg); return &u; } 
 
#define TAU_REGISTER_CONTEXT_EVENT(event, name)	static void *event = 0; \
                                 if (event == 0) Tau_get_context_userevent(&event, name);  

#define TAU_TRIGGER_CONTEXT_EVENT(eventname, eventvalue) Tau_trigger_context_event(eventname, eventvalue)
#define TAU_TRIGGER_CONTEXT_EVENT_THREAD(eventname, eventvalue, tid) Tau_trigger_context_event_thread(eventname, eventvalue, tid)
#define TAU_TRIGGER_EVENT(eventname, eventvalue) Tau_trigger_userevent(eventname, eventvalue)
#define TAU_EVENT(event, data)			Tau_userevent(event, data);
#define TAU_EVENT_THREAD(event, data, tid)				Tau_userevent_thread(event, data, tid)
#define TAU_CONTEXT_EVENT(event, data)		Tau_context_userevent(event, data);
#define TAU_CONTEXT_EVENT_THREAD(event, data, tid) Tau_context_userevent_thread(event, data, tid);
#define TAU_EVENT_SET_NAME(event, name)	Tau_set_event_name(event, name); 	
#define TAU_REPORT_STATISTICS()		Tau_report_statistics();
#define TAU_REPORT_THREAD_STATISTICS()  Tau_report_thread_statistics();
#define TAU_EVENT_DISABLE_MIN(event) 	Tau_event_disable_min(event);
#define TAU_EVENT_DISABLE_MAX(event)	Tau_event_disable_max(event);
#define TAU_EVENT_DISABLE_MEAN(event)	Tau_event_disable_mean(event);
#define TAU_EVENT_DISABLE_STDDEV(event) Tau_event_disable_stddev(event);

#define TAU_DISABLE_CONTEXT_EVENT(event) Tau_disable_context_event(event);
#define TAU_ENABLE_CONTEXT_EVENT(event) Tau_enable_context_event(event);

#define TAU_ENABLE_TRACKING_MEMORY()	        Tau_enable_tracking_memory()
#define TAU_DISABLE_TRACKING_MEMORY()	        Tau_disable_tracking_memory()
#define TAU_TRACK_MEMORY()		        Tau_track_memory()
#define TAU_TRACK_MEMORY_HERE()	        	Tau_track_memory_here()
#define TAU_TRACK_MEMORY_HEADROOM()        	Tau_track_memory_headroom()
#define TAU_TRACK_MEMORY_HEADROOM_HERE()	Tau_track_memory_headroom_here()
#define TAU_ENABLE_TRACKING_MEMORY_HEADROOM()	Tau_enable_tracking_memory_headroom()
#define TAU_DISABLE_TRACKING_MEMORY_HEADROOM()	Tau_disable_tracking_memory_headroom()
#define TAU_TRACK_POWER()		        Tau_track_power()
#define TAU_TRACK_POWER_HERE()	        	Tau_track_power_here()
#define TAU_ENABLE_TRACKING_POWER()		Tau_enable_tracking_power()
#define TAU_DISABLE_TRACKING_POWER()		Tau_disable_tracking_power()

#define TAU_SET_INTERRUPT_INTERVAL(value)	Tau_set_interrupt_interval(value)

#define TAU_GLOBAL_TIMER(timer, name, type, group) void *TauGlobal##timer(void) \
{ static void *ptr = NULL; \
  Tau_profile_c_timer(&ptr, name, type, group, #group); \
  return ptr; \
} 
#define TAU_GLOBAL_TIMER_START(timer) { void *ptr = TauGlobal##timer(); \
    Tau_start_timer(ptr, 0, Tau_get_thread()); }
#define TAU_GLOBAL_TIMER_STOP()  Tau_global_stop();
#define TAU_GLOBAL_TIMER_EXTERNAL(timer)  extern void* TauGlobal##timer(void);

#define TAU_GLOBAL_PHASE(timer, name, type, group) void * TauGlobalPhase##timer(void) \
{ static void *ptr = NULL; \
  Tau_profile_c_timer(&ptr, name, type, group, #group); \
  return ptr; \
} 

#define TAU_GLOBAL_PHASE_START(timer) { void *ptr = TauGlobalPhase##timer(); \
    Tau_start_timer(ptr, 1, Tau_get_thread()); }

#define TAU_GLOBAL_PHASE_STOP(timer)  { void *ptr = TauGlobalPhase##timer(); \
	Tau_stop_timer(ptr, Tau_get_thread()); }

#define TAU_GLOBAL_PHASE_EXTERNAL(timer)  extern void * TauGlobalPhase##timer(void)

/* *CWL* - temporary monitoring interface. These functions must be implemented
   by the monitoring framework. The functions should be implemented in a way
   that does nothing should TAU_MONITORING be unset.
*/
#define TAU_ONLINE_DUMP()                       Tau_mon_onlineDump()

#define TAU_PROFILE_SNAPSHOT(name)              Tau_profile_snapshot(name);
#define TAU_PROFILE_SNAPSHOT_1L(name, expr)     Tau_profile_snapshot_1l(name, expr);

// metadata functions

#define TAU_METADATA(name, value)               Tau_metadata(name, value);
#define TAU_METADATA_ITERATION(name,iteration,value) {char meta_buf[1024]; \
        sprintf(meta_buf,"%s_|_%d",name,iteration); \
        TAU_METADATA(meta_buf,value);}

#define TAU_CONTEXT_METADATA(name, value)       Tau_context_metadata(name, value);

#define TAU_PHASE_METADATA(name, value)         Tau_phase_metadata(name, value);

#define TAU_METADATA_OBJECT(name, key, value) Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_OBJECT); \
        { Tau_metadata_object_t* object = NULL; \
        Tau_metadata_create_object(&object, key, value); \
        name->data.oval = object; }

#define TAU_METADATA_ARRAY(name, length)        Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_ARRAY); \
		{ Tau_metadata_array_t* array = NULL; \
        Tau_metadata_create_array(&array, length); \
        name->data.aval = array; }

#define TAU_METADATA_STRING(name, value)   Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_STRING); \
        name->data.cval = malloc((sizeof(char))*(strlen(value))); \
        strcpy(name->data.cval, value);

#define TAU_METADATA_INTEGER(name, value)       Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_INTEGER); \
		name->data.ival = value;

#define TAU_METADATA_DOUBLE(name, value)        Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_DOUBLE); \
		name->data.dval = value;

#define TAU_METADATA_TRUE(name)                 Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_TRUE);

#define TAU_METADATA_FALSE(name)                Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_FALSE);

#define TAU_METADATA_NULL(name)                 Tau_metadata_value_t* name = NULL; \
        Tau_metadata_create_value(&name, TAU_METADATA_TYPE_NULL);

#define TAU_STRUCTURED_METADATA(name, invalue)   {  Tau_metadata_object_t* object = NULL; \
        Tau_metadata_create_object(&object, name, invalue); \
		Tau_structured_metadata(object, 0); }

#define TAU_STRUCTURED_CONTEXT_METADATA(object)  {  Tau_metadata_object_t* object = NULL; \
        Tau_metadata_create_object(&object, name, invalue); \
		Tau_structured_metadata(object, 1); }

// if the index is greater than the array length, resize?
//#define TAU_METADATA_ARRAY_PUT(array, index, value)  array->data.aval->values[index] = value;
#define TAU_METADATA_ARRAY_PUT(array, index, value) Tau_metadata_array_put(array, index, value);

#define TAU_METADATA_OBJECT_PUT(object, name, value) Tau_metadata_object_put(object, name, value);

#ifdef TAU_PROFILEPARAM
#define TAU_PROFILE_PARAM1L(data,name)  	Tau_profile_param1l(data,name)
#else  /* TAU_PROFILEPARAM */
#define TAU_PROFILE_PARAM1L(data,name)  	
#endif /* TAU_PROFILEPARAM */

#define TAU_TRACE_SENDMSG(type, destination, length) \
        Tau_trace_sendmsg(type, destination, length);
#define TAU_TRACE_RECVMSG(type, source, length) \
        Tau_trace_recvmsg(type, source, length);

#define TAU_TRACE_SENDMSG_REMOTE(type, destination, length, remoteid) \
        Tau_trace_sendmsg_remote(type, destination, length, remoteid);
#define TAU_TRACE_RECVMSG_REMOTE(type, source, length, remoteid) \
        Tau_trace_recvmsg_remote(type, source, length, remoteid);

#define TAU_PROFILER_CREATE(handle, name, type, group)  handle=Tau_get_profiler(name, type, group, #group);
#define TAU_PROFILER_START(handle) Tau_start_timer(handle, 0, Tau_get_thread());
#define TAU_PROFILER_STOP(handle) Tau_stop_timer(handle, Tau_get_thread());
#define TAU_PROFILER_GET_INCLUSIVE_VALUES(handle, data) Tau_get_inclusive_values(handle, (double *) data, Tau_get_thread());
#define TAU_PROFILER_GET_EXCLUSIVE_VALUES(handle, data) Tau_get_exclusive_values(handle, (double *) data, Tau_get_thread());
#define TAU_PROFILER_GET_CALLS(handle, number) Tau_get_calls(handle, number, Tau_get_thread())
#define TAU_PROFILER_GET_CHILD_CALLS(handle, number) Tau_get_child_calls(handle, number, Tau_get_thread());
#define TAU_PROFILER_GET_COUNTER_INFO(counters, numcounters) Tau_get_counter_info((const char ***)counters, numcounters);

#define TAU_CREATE_TASK(taskid) taskid = Tau_create_task()
#define TAU_PROFILER_START_TASK(handle, taskid) Tau_start_timer(handle, 0, taskid);
#define TAU_PROFILER_STOP_TASK(handle, taskid) Tau_stop_timer(handle, taskid);
#define TAU_PROFILER_GET_INCLUSIVE_VALUES_TASK(handle, data, taskid) Tau_get_inclusive_values(handle, (double *) data, taskid)
#define TAU_PROFILER_GET_EXCLUSIVE_VALUES_TASK(handle, data, taskid) Tau_get_exclusive_values(handle, (double *) data, taskid)
#define TAU_PROFILER_GET_CALLS_TASK(handle, number, taskid) Tau_get_calls(handle, number, taskid)
#define TAU_PROFILER_GET_CHILD_CALLS_TASK(handle, number, taskid) Tau_get_child_calls(handle, number, taskid)
#define TAU_PROFILER_GET_COUNTER_INFO_TASK(counters, numcounters, taskid) Tau_get_counter_info((const char ***)counters, numcounters);
#define TAU_PROFILER_SET_INCLUSIVE_VALUES_TASK(handle, data, taskid) Tau_set_inclusive_values(handle, (double *) data, taskid)
#define TAU_PROFILER_SET_EXCLUSIVE_VALUES_TASK(handle, data, taskid) Tau_set_exclusive_values(handle, (double *) data, taskid)
#define TAU_PROFILER_SET_CALLS_TASK(handle, number, taskid) Tau_set_calls(handle, number, taskid)
#define TAU_PROFILER_SET_CHILD_CALLS_TASK(handle, number, taskid) Tau_set_child_calls(handle, number, taskid)

#define TAU_BCAST_DATA(data)  	                Tau_bcast_data(data)
#define TAU_REDUCE_DATA(data)  	                Tau_reduce_data(data)
#define TAU_ALLTOALL_DATA(data)                 Tau_alltoall_data(data) 
#define TAU_SCATTER_DATA(data)                  Tau_scatter_data(data) 
#define TAU_GATHER_DATA(data)  	                Tau_gather_data(data)
#define TAU_ALLREDUCE_DATA(data)  	        Tau_allreduce_data(data)
#define TAU_WAIT_DATA(data)  	        	Tau_wait_data(data)
#define TAU_ALLGATHER_DATA(data)  	        Tau_allgather_data(data)
#define TAU_REDUCESCATTER_DATA(data)  	        Tau_reducescatter_data(data)
#define TAU_SCAN_DATA(data)  		        Tau_scan_data(data)

/* dead macros */
#define TAU_PROFILE_CALLSTACK()
#define PROFILED_BLOCK(name, type)
#define TAU_ENABLE_TRACKING_MUSE_EVENTS()
#define TAU_DISABLE_TRACKING_MUSE_EVENTS()
#define TAU_TRACK_MUSE_EVENTS()

#endif /* TAU_FAPI */

#endif /* TAU_ENABLED */


/******************************************************************************
* Function prototypes
******************************************************************************/


#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */


TauGroup_t Tau_enable_all_groups(void);
TauGroup_t Tau_disable_all_groups(void);
void Tau_disable_group(TauGroup_t group);
void Tau_enable_group(TauGroup_t group);

void Tau_start(const char *name);
void Tau_stop(const char *name);
void Tau_pure_start_task(const char *name, int tid);
void Tau_pure_stop_task(const char *name, int tid);
int Tau_stop_current_timer();
int Tau_stop_current_timer_task(int tid);
char * Tau_phase_enable(const char *group);

void Tau_dynamic_start(char const * name, int isPhase);
void Tau_dynamic_stop(char const * name, int isPhase);
void Tau_static_phase_start(char const * name);
void Tau_static_phase_stop(char const * name);

void* Tau_get_profiler(const char *name, const char *type, TauGroup_t group, const char *gr_name);

void Tau_get_calls(void *handle, long* values, int tid);
void Tau_set_calls(void *handle, long values, int tid);
void Tau_get_child_calls(void *handle, long* values, int tid);
void Tau_set_child_calls(void *handle, long values, int tid);
void Tau_get_inclusive_values(void *handle, double* values, int tid);
void Tau_set_inclusive_values(void *handle, double* values, int tid);
void Tau_get_exclusive_values(void *handle, double* values, int tid);
void Tau_set_exclusive_values(void *handle, double* values, int tid);
void Tau_get_counter_info(const char ***counterlist, int *numcounters);

int TAUDECL Tau_get_local_tid(void);
int TAUDECL Tau_get_thread(void);
int TAUDECL Tau_get_node(void);
int  Tau_create_task(void);
void Tau_destructor_trigger();

void Tau_profile_set_name(void *ptr, const char *name);
void Tau_profile_set_type(void *ptr, const char *type);
void Tau_profile_set_group(void *ptr, TauGroup_t group);
void Tau_profile_set_group_name(void *ptr, const char *groupname);

const char *Tau_profile_get_group_name(void *ptr);
const char *Tau_profile_get_name(void *ptr);
const char *Tau_profile_get_type(void *ptr);
TauGroup_t Tau_profile_get_group(void *ptr);

int Tau_global_get_insideTAU();
int Tau_global_incr_insideTAU();
int Tau_global_decr_insideTAU();
int Tau_global_getLightsOut();
void Tau_global_setLightsOut();

long Tau_convert_ptr_to_long(void *ptr);
unsigned long Tau_convert_ptr_to_unsigned_long(void *ptr);

/* Runtime "context" access */
void *Tau_query_current_event();
const char *Tau_query_event_name(void *event);
void *Tau_query_parent_event(void *event);

void Tau_disable_context_event(void *event);
void Tau_enable_context_event(void *event);

void Tau_pure_context_userevent(void **u, const char *n);

void Tau_the_function_list(const char ***functionList, int *num);
int Tau_dump_prefix(const char *prefix);
int Tau_dump_prefix_task(const char *prefix, int taskid);

void Tau_get_event_names(const char ***eventList, int *num);
void Tau_get_event_vals(const char **inUserEvents, int numUserEvents,
				  int **numEvents, double **max, double **min,
				   double **mean, double **sumSqr);

void Tau_profile_dynamic_auto(int iteration, void **ptr, char *fname, char *type, TauGroup_t group, char *group_name, int isPhase);
void Tau_exit(const char *msg);

void Tau_specify_mapping_data1(long data, const char *name);

void TAUDECL Tau_profile_c_timer(void **ptr, const char *fname, const char *type, TauGroup_t group, const char *group_name);

void TAUDECL Tau_bcast_data(int data);
void TAUDECL Tau_reduce_data(int data);
void TAUDECL Tau_alltoall_data(int data);
void TAUDECL Tau_scatter_data(int data);
void TAUDECL Tau_gather_data(int data);
void TAUDECL Tau_allreduce_data(int data);
void TAUDECL Tau_allgather_data(int data);
void TAUDECL Tau_wait_data(int data);
void TAUDECL Tau_reducescatter_data(int data);
void TAUDECL Tau_scan_data(int data);
void TAUDECL Tau_set_node(int node);

void TAUDECL Tau_start_timer(void *profiler, int phase, int tid);
int TAUDECL Tau_stop_timer(void *profiler, int tid);
void TAUDECL Tau_lite_start_timer(void *profiler, int phase);
void TAUDECL Tau_lite_stop_timer(void *profiler);
void TAUDECL Tau_pure_start(const char *name);
void TAUDECL Tau_pure_stop(const char *name);

void TAUDECL Tau_trace_sendmsg(int type, int destination, int length);
void TAUDECL Tau_trace_recvmsg(int type, int source, int length);
void TAUDECL Tau_trace_recvmsg_remote(int type, int source, int length, int remoteid);
void TAUDECL Tau_trace_sendmsg_remote(int type, int destination, int length, int remoteid);
void TAUDECL Tau_create_top_level_timer_if_necessary(void);
void TAUDECL Tau_create_top_level_timer_if_necessary_task(int task);
void TAUDECL Tau_stop_top_level_timer_if_necessary(void);

// metadata functions
void TAUDECL Tau_metadata(const char *name, const char *value);
void TAUDECL Tau_phase_metadata(const char *name, const char *value);
void TAUDECL Tau_context_metadata(const char *name, const char *value);
void TAUDECL Tau_metadata_create_value(Tau_metadata_value_t** value, const Tau_metadata_type_t type);
void TAUDECL Tau_metadata_create_object(Tau_metadata_object_t** object, const char* name, Tau_metadata_value_t* value);
void TAUDECL Tau_metadata_create_array(Tau_metadata_array_t** array, const int length);
void TAUDECL Tau_metadata_array_put(Tau_metadata_value_t* array, const int index, Tau_metadata_value_t* value);
void TAUDECL Tau_metadata_object_put(Tau_metadata_value_t* object, const char *name, Tau_metadata_value_t* value);


void TAUDECL Tau_Bg_hwp_counters_start(int *error); 
void TAUDECL Tau_Bg_hwp_counters_stop(int* numCounters, x_uint64 counters[], int* mode, int *error); 
void TAUDECL Tau_Bg_hwp_counters_output(int* numCounters, x_uint64 counters[], int* mode, int* error);

void Tau_set_user_clock(double value);
void Tau_set_user_clock_thread(double value, int tid);

void Tau_init(int argc, char **argv);
void Tau_init_ref(int* argc, char ***argv);
void Tau_set_context(int context);
void Tau_set_thread(int thread);
void Tau_callstack(void);
int Tau_dump(void);
int Tau_mergeProfiles();
int Tau_dump_incr(void);
void Tau_purge(void);
void Tau_theFunctionList(const char ***functionList, int *num);
void Tau_dump_function_names();
void Tau_get_counter_names(const char ***counterList, int *num);
void Tau_get_function_values(const char **inFuncs, int numOfFuncs,
				    double ***counterExclusiveValues,
				    double ***counterInclusiveValues,
				    int **numOfCalls, int **numOfSubRoutines,
				    const char ***counterNames, int *numOfCounters);
void Tau_dump_function_values(const char **functionList, int num);
void Tau_dump_function_values_incr(const char **functionList, int num);
void Tau_register_thread();
void Tau_register_fork(int nodeid, enum TauFork_t opcode);
void* TAUDECL Tau_get_userevent(char const * name);
void Tau_get_context_userevent(void **ptr, const char *name);
void Tau_trigger_context_event(const char *name, double data);
void Tau_trigger_context_event_thread(const char *name, double data, int tid);
void Tau_trigger_userevent(const char *name, double data);
void Tau_userevent(void *event, double data);
void Tau_userevent_thread(void *event, double data, int tid);
void Tau_context_userevent(void *event, double data);
void Tau_context_userevent_thread(void *event, double data, int tid);
void Tau_set_event_name(void *event, char * name);
void Tau_report_statistics(void);
void Tau_report_thread_statistics(void);
void Tau_event_disable_min(void *event);
void Tau_event_disable_max(void *event);
void Tau_event_disable_mean(void *event);
void Tau_event_disable_stddev(void *event);
TauGroup_t Tau_enable_group_name(char const * group);
TauGroup_t Tau_disable_group_name(char const * group);
TauGroup_t Tau_get_profile_group(char *group);
void Tau_track_memory(void);
void Tau_enable_tracking_memory(void);
void Tau_disable_tracking_memory(void);
void Tau_set_interrupt_interval(int value);
void Tau_enable_instrumentation(void);
void Tau_disable_instrumentation(void);
void Tau_global_stop(void);
char * Tau_phase_enable_once(const char *group, void **ptr);

void Tau_profile_snapshot(const char *name);
void Tau_profile_snapshot_1l(const char *name, int number);
void Tau_collate_onlineDump();

void Tau_enable_tracking_memory_headroom();
void Tau_disable_tracking_memory_headroom();
void Tau_track_memory_here(void);
void Tau_track_memory_headroom(void);
void Tau_track_power(void);
void Tau_track_power_here(void);
void Tau_enable_tracking_power();
void Tau_disable_tracking_power();
void Tau_track_memory_headroom_here(void);
void Tau_profile_param1l(long data, const char *dataname);

void Tau_mark_group_as_phase(void *ptr);
char const * Tau_append_iteration_to_name(int iteration, char const * name, int slen);

#ifdef __cplusplus
/* Include the C++ API header */
#include <Profile/TauCppAPI.h>
#else /* __cplusplus */
/* These can't be used in C, only C++, so they are dummy macros here */
#define TAU_PROFILE(name, type, group) 
#define TAU_DYNAMIC_PROFILE(name, type, group) 
#define TYPE_STRING(profileString, str)
#define TAU_CT(obj)
#endif /* __cplusplus */ 


#ifdef __cplusplus
} /* for extern "C" */
#endif /* __cplusplus */

/**************************************************************************/

#endif /* _TAU_API_H_ */
/***************************************************************************
 * $RCSfile: TauAPI.h,v $   $Author: cheelee $
 * $Revision: 1.116 $   $Date: 2010/06/08 01:09:52 $
 * POOMA_VERSION_ID: $Id: TauAPI.h,v 1.116 2010/06/08 01:09:52 cheelee Exp $ 
 ***************************************************************************/
