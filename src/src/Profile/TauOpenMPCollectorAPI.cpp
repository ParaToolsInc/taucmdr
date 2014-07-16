#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#ifdef TAU_IBM_OMPT
#include <lomp/omp.h>
#endif /* TAU_IBM_OMPT */

#include "omp_collector_api.h"
#include "omp.h"
#include <stdlib.h>
#include <stdio.h> 
#include <string.h> 
#include <stdbool.h> 
#include "dlfcn.h" // for dynamic loading of symbols
#ifdef MERCURIUM_EXTRA
# define RTLD_DEFAULT   ((void *) 0)
#endif
#include "Profiler.h"
#ifdef TAU_USE_LIBUNWIND
#define UNW_LOCAL_ONLY
#include <libunwind.h>
#endif
#include "TauEnv.h"
#include <Profile/TauBfd.h>
#ifdef TAU_MPC
#include <Profile/MPCThreadLayer.h>
#endif

/* An array of this struct is shared by all threads. To make sure we don't have false
 * sharing, the struct is 64 bytes in size, so that it fits exactly in
 * one (or two) cache lines. That way, when one thread updates its data
 * in the array, it won't invalidate the cache line for other threads. 
 * This is very important with timers, as all threads are entering timers
 * at the same time, and every thread will invalidate the cache line
 * otherwise. */
struct Tau_collector_status_flags {
    char idle; // 4 bytes
    char busy; // 4 bytes
    char parallel; // 4 bytes
    char ordered_region_wait; // 4 bytes
    char ordered_region; // 4 bytes
    char task_exec; // 4 bytes
    char looping; // 4 bytes
    char acquired; // 4 bytes
    char waiting; // 4 bytes
	unsigned long regionid; // 8 bytes
	unsigned long taskid; // 8 bytes
    int *signal_message; // preallocated message for signal handling, 8 bytes
    int *region_message; // preallocated message for region handling, 8 bytes
    int *task_message; // preallocated message for task handling, 8 bytes
    char _pad[128-((3*sizeof(int*))+(9*sizeof(char))+(2*sizeof(unsigned long)))];
};

/* This array is shared by all threads. To make sure we don't have false
 * sharing, the struct is 64 bytes in size, so that it fits exactly in
 * one (or two) cache lines. That way, when one thread updates its data
 * in the array, it won't invalidate the cache line for other threads. 
 * This is very important with timers, as all threads are entering timers
 * at the same time, and every thread will invalidate the cache line
 * otherwise. */
#if defined __INTEL__COMPILER
__declspec (align(64)) static struct Tau_collector_status_flags Tau_collector_flags[TAU_MAX_THREADS] = {0};
#elif defined __GNUC__
static struct Tau_collector_status_flags Tau_collector_flags[TAU_MAX_THREADS] __attribute__ ((aligned(64))) = {{0}};
#else
static struct Tau_collector_status_flags Tau_collector_flags[TAU_MAX_THREADS] = {0};
#endif

// this is map of region names, indexed by region id.
static std::map<unsigned long, char*> region_names;
static std::map<unsigned long, char*> task_names;

#ifdef TAU_MPC
//static sctk_thread_mutex_t writelock = SCTK_THREAD_MUTEX_INITIALIZER;
//#define TAU_OPENMP_SET_LOCK sctk_thread_mutex_lock(&writelock)
//#define TAU_OPENMP_UNSET_LOCK sctk_thread_mutex_lock(&writelock)
#define TAU_OPENMP_SET_LOCK RtsLayer::LockDB();
#define TAU_OPENMP_UNSET_LOCK RtsLayer::UnLockDB();
#define TAU_OPENMP_INIT_LOCK 
#else
static omp_lock_t writelock;
#define TAU_OPENMP_SET_LOCK omp_set_lock(&writelock)
#define TAU_OPENMP_UNSET_LOCK omp_unset_lock(&writelock)
#define TAU_OPENMP_INIT_LOCK omp_init_lock(&writelock)
#endif

static int Tau_collector_enabled = 1;

extern "C" void Tau_disable_collector_api() {
  // if we didn't initialize the lock, we will crash...
  if (!TauEnv_get_openmp_runtime_enabled()) return;
  //TAU_OPENMP_SET_LOCK;
  Tau_collector_enabled = 0;
  //TAU_OPENMP_UNSET_LOCK;
}

static const char* __UNKNOWN__ = "UNKNOWN";

extern const int OMP_COLLECTORAPI_HEADERSIZE;
char OMP_EVENT_NAME[35][50]= {
    "OMP_EVENT_FORK",
    "OMP_EVENT_JOIN",
    "OMP_EVENT_THR_BEGIN_IDLE",
    "OMP_EVENT_THR_END_IDLE",
    "OMP_EVENT_THR_BEGIN_IBAR",
    "OMP_EVENT_THR_END_IBAR",
    "OMP_EVENT_THR_BEGIN_EBAR",
    "OMP_EVENT_THR_END_EBAR",
    "OMP_EVENT_THR_BEGIN_LKWT",
    "OMP_EVENT_THR_END_LKWT",
    "OMP_EVENT_THR_BEGIN_CTWT",
    "OMP_EVENT_THR_END_CTWT",
    "OMP_EVENT_THR_BEGIN_ODWT",
    "OMP_EVENT_THR_END_ODWT",
    "OMP_EVENT_THR_BEGIN_MASTER",
    "OMP_EVENT_THR_END_MASTER",
    "OMP_EVENT_THR_BEGIN_SINGLE",
    "OMP_EVENT_THR_END_SINGLE",
    "OMP_EVENT_THR_BEGIN_ORDERED",
    "OMP_EVENT_THR_END_ORDERED",
    "OMP_EVENT_THR_BEGIN_ATWT",
    "OMP_EVENT_THR_END_ATWT",
    /* new events created by UH */
    "OMP_EVENT_THR_BEGIN_CREATE_TASK",
    "OMP_EVENT_THR_END_CREATE_TASK_IMM",
    "OMP_EVENT_THR_END_CREATE_TASK_DEL",
    "OMP_EVENT_THR_BEGIN_SCHD_TASK",
    "OMP_EVENT_THR_END_SCHD_TASK",
    "OMP_EVENT_THR_BEGIN_SUSPEND_TASK",
    "OMP_EVENT_THR_END_SUSPEND_TASK",
    "OMP_EVENT_THR_BEGIN_STEAL_TASK",
    "OMP_EVENT_THR_END_STEAL_TASK",
    "OMP_EVENT_THR_FETCHED_TASK",
    "OMP_EVENT_THR_BEGIN_EXEC_TASK",
    "OMP_EVENT_THR_BEGIN_FINISH_TASK",
    "OMP_EVENT_THR_END_FINISH_TASK"
};

#if defined(TAU_USE_OMPT)
// this is an array of state names for the OMPT interface.
// For some reason, OMPT doesn't provide a fast lookup
// for states based on the ID, so we have to make our own.
// The states are enumerated, but not consecutive. :(
// 128 should be enough, there aren't that many states.
// but the bitcodes go up to about 110.
static std::string* OMPT_STATE_NAMES[128] = {0};
static int OMPT_NUM_STATES;
#endif

const int OMP_COLLECTORAPI_HEADERSIZE=4*sizeof(int);

static int (*Tau_collector_api)(void*) = NULL;

using namespace std;
using namespace tau;

extern FunctionInfo * Tau_create_thread_state_if_necessary(const char* thread_state);
extern FunctionInfo * Tau_create_thread_state_if_necessary_string(std::string thread_state);

extern "C" char * TauInternal_CurrentCallsiteTimerName(int tid);

void Tau_get_region_id(int tid) {
    // if not available, return something useful
    if (Tau_collector_api == NULL) {
        Tau_collector_flags[tid].regionid = 0UL;
	    return;
	}
    // query the thread state
    int rc = (Tau_collector_api)(Tau_collector_flags[tid].region_message);
    Tau_collector_flags[tid].regionid = (unsigned long)Tau_collector_flags[tid].region_message[4];
	if (rc !=0) {
      TAU_VERBOSE("Error getting region id from ORA!\n");
	}
    return;
}

void Tau_get_task_id(int tid) {
    // if not available, return something useful
    if (Tau_collector_api == NULL) {
        Tau_collector_flags[tid].taskid = 0UL;
	    return;
	}
    // query the thread state
    int rc = (Tau_collector_api)(Tau_collector_flags[tid].task_message);
    Tau_collector_flags[tid].taskid = (unsigned long)Tau_collector_flags[tid].task_message[4];
	if (rc !=0) {
      TAU_VERBOSE("Error getting task id from ORA!\n");
	}
    return;
}

#if !defined (TAU_OPEN64ORC) && \
!defined (TAU_MPC) && \
(defined (__GNUC__) && \
defined (__GNUC_MINOR__) && \
defined (__GNUC_PATCHLEVEL__))
extern "C" void * Tau_get_gomp_proxy_address(void);
#endif

#ifdef TAU_BFD

/*
 *-----------------------------------------------------------------------------
 * Simple hash table to map function addresses to region names/identifier
 *-----------------------------------------------------------------------------
 */

struct OmpHashNode
{
  OmpHashNode() { }

  TauBfdInfo info;		///< Filename, line number, etc.
  char * location;
};

extern void Tau_delete_hash_table(void);

struct OmpHashTable : public TAU_HASH_MAP<unsigned long, OmpHashNode*>
{
  OmpHashTable() { }
  virtual ~OmpHashTable() {
    Tau_delete_hash_table();
  }
};

static OmpHashTable & OmpTheHashTable()
{
  static OmpHashTable htab;
  return htab;
}

static tau_bfd_handle_t & OmpTheBfdUnitHandle()
{
  static tau_bfd_handle_t OmpbfdUnitHandle = TAU_BFD_NULL_HANDLE;
  if (OmpbfdUnitHandle == TAU_BFD_NULL_HANDLE) {
    RtsLayer::LockEnv();
    if (OmpbfdUnitHandle == TAU_BFD_NULL_HANDLE) {
      OmpbfdUnitHandle = Tau_bfd_registerUnit();
    }
    RtsLayer::UnLockEnv();
  }
  return OmpbfdUnitHandle;
}

void Tau_delete_hash_table(void) {
  // clear the hash map to eliminate memory leaks
  OmpHashTable & mytab = OmpTheHashTable();
  for ( TAU_HASH_MAP<unsigned long, OmpHashNode*>::iterator it = mytab.begin(); it != mytab.end(); ++it ) {
    OmpHashNode * node = it->second;
    if (node->location) {
        free (node->location);
    }
    delete node;
  }
  mytab.clear();
#ifdef TAU_BFD
  Tau_delete_bfd_units();
#endif
}

// this function won't actually do the backtrace, but rather get the function
// info for frame pointer of the outlined region.
char * get_proxy_name(unsigned long ip) {
    char * location = NULL;
    tau_bfd_handle_t & OmpbfdUnitHandle = OmpTheBfdUnitHandle();
	if (ip == 0) {
        location = (char*)malloc(strlen(__UNKNOWN__)+1);
        strcpy(location, __UNKNOWN__);
		return location;
	}
    RtsLayer::LockDB();
    OmpHashNode * node = OmpTheHashTable()[ip];
    if (!node) {
        node = new OmpHashNode;
        Tau_bfd_resolveBfdInfo(OmpbfdUnitHandle, ip, node->info);
        // Build routine name for TAU function info
        unsigned int size = strlen(node->info.funcname) + strlen(node->info.filename) + 128;
        char * routine = (char*)malloc(size);
        if (TauEnv_get_bfd_lookup()) {
            sprintf(routine, "%s [{%s} {%d,0}]", node->info.funcname, node->info.filename, node->info.lineno);
        } else {
            sprintf(routine, "[%s] UNRESOLVED %s ADDR %p", node->info.funcname, node->info.filename, (void*)ip);
        }
	node->location = routine;
        OmpTheHashTable()[ip] = node;
    }
    RtsLayer::UnLockDB();
    location = (char*)malloc(strlen(node->location)+1);
    strcpy(location, node->location);
    return location;
}
#else /* defined (TAU_BFD) */
// this function will just format the instruction pointer
char * get_proxy_name(unsigned long ip) {
    char * location = NULL;
	if (ip == 0) {
        location = (char*)malloc(strlen(__UNKNOWN__)+1);
        strcpy(location, __UNKNOWN__);
		return location;
	}
    location = (char*)malloc(128);
    sprintf(location, "UNRESOLVED ADDR %p", (void*)ip);
    return location;
}
#endif /* defined (TAU_BFD) */

#ifdef TAU_UNWIND
typedef struct {
    unsigned long pc;
    int moduleIdx;
    char *name;
} Tau_collector_api_CallSiteInfo;

char * show_backtrace (int tid, int offset) {
    char * location = NULL;
    unw_cursor_t cursor; unw_context_t uc;
	memset(&cursor,0,sizeof(cursor));
	memset(&uc,0,sizeof(uc));
    unw_word_t ip;

    tau_bfd_handle_t & OmpbfdUnitHandle = OmpTheBfdUnitHandle();

    unw_getcontext(&uc);
    unw_init_local(&cursor, &uc);
    int index = 0;
    static int basedepth = -1;
    int depth = basedepth + offset;

    while (unw_step(&cursor) > 0) {
        if (++index >= depth) {
            unw_get_reg(&cursor, UNW_REG_IP, &ip);
            RtsLayer::LockDB();
			OmpHashNode * node = OmpTheHashTable()[ip];
            if (!node) {
              node = new OmpHashNode;
              Tau_bfd_resolveBfdInfo(OmpbfdUnitHandle, ip, node->info);
              // Build routine name for TAU function info
              unsigned int size = strlen(node->info.funcname) + strlen(node->info.filename) + 128;
              char * routine = (char*)malloc(size);
              if (TauEnv_get_bfd_lookup()) {
                sprintf(routine, "%s [{%s} {%d,0}]", node->info.funcname, node->info.filename, node->info.lineno);
              } else {
                sprintf(routine, "[%s] UNRESOLVED %s ADDR %p", node->info.funcname, node->info.filename, (void*)ip);
              }
			  node->location = routine;
              OmpTheHashTable()[ip] = node;
            }
            RtsLayer::UnLockDB();
			//TAU_VERBOSE("%d %d %d %s\n",basedepth, depth, index, node->location); fflush(stderr);
			if (basedepth == -1) {
				if (strncmp(node->info.funcname,"Tau_", 4) == 0) {  // in TAU
			    	continue; // keep unwinding
				} else if (strncmp(node->info.funcname,"addr=<", 6) == 0) { // in OpenMP runtime
			    	continue; // keep unwinding
				}
#if defined (TAU_OPEN64ORC)
				else if (strncmp(node->info.funcname,"__ompc_", 7) == 0) { // in OpenUH runtime
			    	continue; // keep unwinding
				}
#elif defined (__INTEL_COMPILER)
				else if (strncmp(node->info.funcname,"my_parallel_region_create", 25) == 0) { // in OMPT wraper (see below)
			    	continue; // keep unwinding
				} else if (strncmp(node->info.funcname,"__kmp", 5) == 0) { // in Intel runtime
			    	continue; // keep unwinding
				}
#elif defined(TAU_USE_OMPT) || defined(TAU_IBM_OMPT)
				else if (strncmp(node->info.funcname,"my_", 3) == 0) { // in OMPT wraper (see below)
			    	continue; // keep unwinding
				}
#else /* assume we are using gcc */
				else if (strncmp(node->info.funcname,"tau_GOMP", 8) == 0) {  // in GOMP wrapper
			    	continue; // keep unwinding
				} else if (strncmp(node->info.funcname,"__wrap_GOMP", 11) == 0) {  // in GOMP wrapper
			    	continue; // keep unwinding
				} else if (strncmp(node->info.funcname,"GOMP_", 5) == 0) {  // in GOMP runtime
			    	continue; // keep unwinding
				} else if (strncmp(node->info.funcname,"__ompc_event_callback", 21) == 0) { // in GOMP wrapper
			    	continue; // keep unwinding
				} 
#endif
				// stop unwinding
				basedepth = index;
			}
            location = (char*)malloc(strlen(node->location)+1);
            strcpy(location, node->location);
            break;
        }
    }
    return location;
}
#endif

extern "C" void Tau_get_current_region_context(int tid, unsigned long ip, bool task) {
    char * tmpStr = NULL;
#if !defined (TAU_OPEN64ORC) && \
(defined (__GNUC__) && \
defined (__GNUC_MINOR__) && \
defined (__GNUC_PATCHLEVEL__)) // IBM OMPT and Generic ORA support requires unwinding
#if !defined (TAU_USE_OMPT)  // OMPT already has the frame pointer
    // make a call to the GOMP wrapper to get the outlined function pointer
    ip = (unsigned long)Tau_get_gomp_proxy_address();
#endif
    // convert the address to source information
    tmpStr = get_proxy_name(ip); // find our top level timer
#elif defined(TAU_UNWIND) && defined(TAU_BFD) // need them both
    // unfortunately, for regular ORA support we need to unwind the call stack
    if (TauEnv_get_openmp_runtime_context() == 2) { // region
      tmpStr = show_backtrace(tid, 0); // find our source location
      if (tmpStr == NULL) {
          // fall back to the top level timer
          tmpStr = TauInternal_CurrentCallsiteTimerName(tid); // use the top level timer
          //tmpStr = (char*)__UNKNOWN__;
      }
    } else { // timer or none
      tmpStr = TauInternal_CurrentCallsiteTimerName(tid); // use the top level timer
    }
#else
    tmpStr = TauInternal_CurrentCallsiteTimerName(tid); // use the top level timer
#endif
    if (tmpStr == NULL) {
        tmpStr = strdup((char*)__UNKNOWN__);
    }

	// save the region name for the worker threads in this team to access
	if (task) {
	    //TAU_VERBOSE("Task %lu has name %s\n", Tau_collector_flags[tid].taskid, tmpStr);
        TAU_OPENMP_SET_LOCK;
	    task_names[Tau_collector_flags[tid].taskid] = strdup(tmpStr);
        TAU_OPENMP_UNSET_LOCK;
	} else {
	    //TAU_VERBOSE("Region %lu has name %s\n", Tau_collector_flags[tid].regionid, tmpStr);
        TAU_OPENMP_SET_LOCK;
	    region_names[Tau_collector_flags[tid].regionid] = strdup(tmpStr);
        TAU_OPENMP_UNSET_LOCK;
	}
	free (tmpStr);
    return;
}

/* Using the region or task ID, get our event context */
extern "C" char * Tau_get_my_region_context(int tid, int forking, bool task) {
    char * tmpStr = NULL;
#if !defined (TAU_OPEN64ORC) && \
!defined (TAU_MPC) && \
(defined (__GNUC__) && \
defined (__GNUC_MINOR__) && \
defined (__GNUC_PATCHLEVEL__))
    // if using the GOMP wrapper, we don't have a region or task ID
	// so use the outlined function address
    unsigned long ip = (unsigned long)Tau_get_gomp_proxy_address();
    tmpStr = get_proxy_name(ip);
#else // not GOMP...
    if (task) {
        TAU_OPENMP_SET_LOCK;
        tmpStr = task_names[Tau_collector_flags[tid].taskid];
        TAU_OPENMP_UNSET_LOCK;
	    //TAU_VERBOSE("Thread %d, Task %lu has name %s\n", tid, Tau_collector_flags[tid].taskid, tmpStr);
	} else {
        TAU_OPENMP_SET_LOCK;
#if defined (TAU_IBM_OMPT) // IBM OMPT switches things up...
        tmpStr = region_names[Tau_collector_flags[tid].taskid];
#else // not IBM OMPT
        tmpStr = region_names[Tau_collector_flags[tid].regionid];
#endif // TAU_IBM_OMPT
        TAU_OPENMP_UNSET_LOCK;
	    //TAU_VERBOSE("Thread %d, Region %lu has name %s\n", tid, Tau_collector_flags[tid].regionid, tmpStr);
	}
#endif // check for GOMP
    if (tmpStr == NULL)
        tmpStr = strdup((char*)__UNKNOWN__);
    return tmpStr;
}

extern "C" void Tau_pure_start_openmp_task(const char * n, const char * t, int tid);

/*__inline*/ void Tau_omp_start_timer(const char * state, int tid, int use_context, int forking, bool task) {
  // 0 means no context wanted
  if (use_context == 0 || TauEnv_get_openmp_runtime_context() == 0) {
    //  no context for the event
    Tau_pure_start_openmp_task(state, "", tid);
  } else {
    int contextLength = 10;
    char * regionIDstr = NULL;
    char * tmpStr = Tau_get_my_region_context(tid, forking, task);
    contextLength = strlen(tmpStr);
	regionIDstr = (char*)malloc(contextLength + 32);
    sprintf(regionIDstr, "%s: %s", state, tmpStr);
    Tau_pure_start_openmp_task(regionIDstr, "", tid);
	//free(tmpStr);
    free(regionIDstr);
  }
}

/*__inline*/ void Tau_omp_stop_timer(const char * state, int tid, int use_context) {
    if (Tau_collector_enabled) {
      Tau_stop_current_timer_task(tid);
    }
}

extern "C" void Tau_omp_event_handler(OMP_COLLECTORAPI_EVENT event) {
    // THIS is here in case the very last statement in the
    // program is a parallel region - the worker threads
    // may exit AFTER thread 0 has exited, which triggered
    // the worker threads to stop all timers and dump.
    if (!Tau_collector_enabled || 
        !Tau_RtsLayer_TheEnableInstrumentation()) return;

    Tau_global_incr_insideTAU();

    int tid = Tau_get_thread();
    //fprintf(stderr, "** Thread: %d, (i:%d b:%d p:%d w:%d o:%d t:%d) EVENT:%s **\n", tid, Tau_collector_flags[tid].idle, Tau_collector_flags[tid].busy, Tau_collector_flags[tid].parallel, Tau_collector_flags[tid].ordered_region_wait, Tau_collector_flags[tid].ordered_region, Tau_collector_flags[tid].task_exec, OMP_EVENT_NAME[event-1]); fflush(stderr);

	// query the ORA to get the region id
    Tau_get_region_id (tid);

    switch(event) {
        case OMP_EVENT_FORK:
            Tau_get_current_region_context(tid, 0LU, false);
            Tau_omp_start_timer("OpenMP_PARALLEL_REGION", tid, 1, 1, false);
            Tau_collector_flags[tid].parallel++;
            break;
        case OMP_EVENT_JOIN:
            if (Tau_collector_flags[tid].parallel>0) {
                Tau_omp_stop_timer("OpenMP_PARALLEL_REGION", tid, 1);
                Tau_collector_flags[tid].parallel--;
            }
            break;
        case OMP_EVENT_THR_BEGIN_IDLE:
            // sometimes IDLE can be called twice in a row
            if (Tau_collector_flags[tid].idle == 1 && 
                    Tau_collector_flags[tid].busy == 0) {
                break;
            }
            if (Tau_collector_flags[tid].busy == 1) {
                Tau_omp_stop_timer("OpenMP_PARALLEL_REGION", tid, 1);
                Tau_collector_flags[tid].busy = 0;
            }
            Tau_collector_flags[tid].idle = 1;
            break;
        case OMP_EVENT_THR_END_IDLE:
            Tau_omp_start_timer("OpenMP_PARALLEL_REGION", tid, 1, 1, false);
            Tau_collector_flags[tid].busy = 1;
            Tau_collector_flags[tid].idle = 0;
            break;
        case OMP_EVENT_THR_BEGIN_IBAR:
            Tau_omp_start_timer("OpenMP_IMPLICIT_BARRIER", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_IBAR:
            Tau_omp_stop_timer("OpenMP_IMPLICIT_BARRIER", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_EBAR:
            Tau_omp_start_timer("OpenMP_EXPLICIT_BARRIER", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_EBAR:
            Tau_omp_stop_timer("OpenMP_EXPLICIT_BARRIER", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_LKWT:
            Tau_omp_start_timer("OpenMP_LOCK_WAIT", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_LKWT:
            Tau_omp_stop_timer("OpenMP_LOCK_WAIT", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_CTWT:
            Tau_omp_start_timer("OpenMP_CRITICAL_SECTION_WAIT", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_CTWT:
            Tau_omp_stop_timer("OpenMP_CRITICAL_SECTION_WAIT", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_ODWT:
            // for some reason, the ordered region wait is entered twice for some threads.
            if (Tau_collector_flags[tid].ordered_region_wait == 0) {
                Tau_omp_start_timer("OpenMP_ORDERED_REGION_WAIT", tid, 1, 0, false);
            }
            Tau_collector_flags[tid].ordered_region_wait = 1;
            break;
        case OMP_EVENT_THR_END_ODWT:
            if (Tau_collector_flags[tid].ordered_region_wait == 1) {
                Tau_omp_stop_timer("OpenMP_ORDERED_REGION_WAIT", tid, 1);
            }
            Tau_collector_flags[tid].ordered_region_wait = 0;
            break;
        case OMP_EVENT_THR_BEGIN_MASTER:
            Tau_omp_start_timer("OpenMP_MASTER_REGION", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_MASTER:
            Tau_omp_stop_timer("OpenMP_MASTER_REGION", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_SINGLE:
            Tau_omp_start_timer("OpenMP_SINGLE_REGION", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_SINGLE:
            Tau_omp_stop_timer("OpenMP_SINGLE_REGION", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_ORDERED:
            // for some reason, the ordered region is entered twice for some threads.
            if (Tau_collector_flags[tid].ordered_region == 0) {
                Tau_omp_start_timer("OpenMP_ORDERED_REGION", tid, 1, 0, false);
                Tau_collector_flags[tid].ordered_region = 1;
            }
            break;
        case OMP_EVENT_THR_END_ORDERED:
            if (Tau_collector_flags[tid].ordered_region == 1) {
                Tau_omp_stop_timer("OpenMP_ORDERED_REGION", tid, 1);
            }
            Tau_collector_flags[tid].ordered_region = 0;
            break;
        case OMP_EVENT_THR_BEGIN_ATWT:
            Tau_omp_start_timer("OpenMP_ATOMIC_REGION_WAIT", tid, 1, 0, false);
            break;
        case OMP_EVENT_THR_END_ATWT:
            Tau_omp_stop_timer("OpenMP_ATOMIC_REGION_WAIT", tid, 1);
            break;
        case OMP_EVENT_THR_BEGIN_CREATE_TASK:
            // Open64 doesn't actually create a task if there is just one thread.
            // In that case, there won't be an END_CREATE.
			
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
#if defined (TAU_OPEN64ORC)
            if (omp_get_num_threads() > 1) {
                Tau_omp_start_timer("OpenMP_CREATE_TASK", tid, 0, 0, false);
            }
#else
            Tau_omp_start_timer("OpenMP_CREATE_TASK", tid, 1, 0, false);
#endif
            break;
        case OMP_EVENT_THR_END_CREATE_TASK_IMM:
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
            Tau_omp_stop_timer("OpenMP_CREATE_TASK", tid, 0);
            break;
        case OMP_EVENT_THR_END_CREATE_TASK_DEL:
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
            Tau_omp_stop_timer("OpenMP_CREATE_TASK", tid, 0);
            break;
        case OMP_EVENT_THR_BEGIN_SCHD_TASK:
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
            Tau_omp_start_timer("OpenMP_SCHEDULE_TASK", tid, 0, 0, false);
            break;
        case OMP_EVENT_THR_END_SCHD_TASK:
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
            Tau_omp_stop_timer("OpenMP_SCHEDULE_TASK", tid, 0);
            break;
// these events are somewhat unstable with OpenUH
        case OMP_EVENT_THR_BEGIN_SUSPEND_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            //Tau_omp_start_timer("OpenMP_SUSPEND_TASK", tid, 0, 0, false);
            break;
        case OMP_EVENT_THR_END_SUSPEND_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            //Tau_omp_stop_timer("OpenMP_SUSPEND_TASK", tid, 0);
            break;
        case OMP_EVENT_THR_BEGIN_STEAL_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            //Tau_omp_start_timer("OpenMP_STEAL_TASK", tid, 0, 0, false);
            break;
        case OMP_EVENT_THR_END_STEAL_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            //Tau_omp_stop_timer("OpenMP_STEAL_TASK", tid, 0);
            break;
        case OMP_EVENT_THR_FETCHED_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            break;
        case OMP_EVENT_THR_BEGIN_EXEC_TASK:
	        // query the ORA to get the task id
            Tau_get_task_id (tid);
            Tau_omp_start_timer("OpenMP_EXECUTE_TASK", tid, 1, 0, false);
            Tau_collector_flags[tid].task_exec += 1;
            break;
        case OMP_EVENT_THR_BEGIN_FINISH_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            // When we get a "finish task", there might be a task executing...
            // or there might not.
            if (Tau_collector_flags[tid].task_exec > 0) {
                Tau_omp_stop_timer("OpenMP_EXECUTE_TASK", tid, 0);
                Tau_collector_flags[tid].task_exec -= 1;
            }
            //Tau_omp_start_timer("OpenMP_FINISH_TASK", tid, 0, 0, false);
            break;
        case OMP_EVENT_THR_END_FINISH_TASK:
	        // query the ORA to get the task id
            //Tau_get_task_id (tid);
            //Tau_omp_stop_timer("OpenMP_FINISH_TASK", tid, 0);
            break;
		case OMP_EVENT_THR_RESERVED_IMPL:
			break;
		case OMP_EVENT_LAST:
			break;
    }
    Tau_global_decr_insideTAU();
    return;
}

static bool initializing = false;
static bool initialized = false;

#if TAU_DISABLE_SHARED
extern int __omp_collector_api(void *);
#endif

extern "C" int Tau_initialize_collector_api(void) {
    //if (Tau_collector_api != NULL || initializing) return 0;
    if (initialized || initializing) return 0;
    if (!TauEnv_get_openmp_runtime_enabled()) {
      TAU_VERBOSE("COLLECTOR API disabled.\n"); 
      return 0;
    }

#if defined(TAU_USE_OMPT) || defined(TAU_IBM_OMPT)
    TAU_VERBOSE("COLLECTOR API disabled, using OMPT instead.\n"); 
    return 0;
#endif

    initializing = true;

    TAU_OPENMP_INIT_LOCK;

#if TAU_DISABLE_SHARED
	Tau_collector_api = &__omp_collector_api;
#else

#if defined (TAU_BGP) || defined (TAU_BGQ) || defined (TAU_CRAYCNL)
    // these special systems don't support dynamic symbol loading.
    *(void **) (&Tau_collector_api) = NULL;

#else

    // this funny code is to avoid a warning from the compiler, because
	// dlsym returns a void*
    //*(void **) (&Tau_collector_api) = dlsym(RTLD_DEFAULT, "__omp_collector_api");
    void *temp_fptr = dlsym(RTLD_DEFAULT, "__omp_collector_api");
	memcpy(&Tau_collector_api, &temp_fptr, sizeof(temp_fptr));
    if (Tau_collector_api == NULL) {

#if defined (__INTEL_COMPILER)
        char * libname = "libiomp5.so";
#elif defined (__GNUC__) && defined (__GNUC_MINOR__) && defined (__GNUC_PATCHLEVEL__)

#ifdef __APPLE__
        char * libname = (char*)("libgomp_g_wrap.dylib");
#else /* __APPLE__ */
        char * libname = (char*)("libTAU-gomp.so");
#endif /* __APPLE__ */

#else /* assume we are using OpenUH */
        char * libname = (char*)("libopenmp.so");
#endif /* __GNUC__ __GNUC_MINOR__ __GNUC_PATCHLEVEL__ */

        TAU_VERBOSE("Looking for library: %s\n", libname); fflush(stdout); fflush(stderr);
        void * handle = dlopen(libname, RTLD_NOW | RTLD_GLOBAL);

        if (handle != NULL) {
            TAU_VERBOSE("Looking for symbol in library: %s\n", libname); fflush(stdout); fflush(stderr);
            // this funny code is to avoid a warning from the compiler, because
	        // dlsym returns a void*
            //*(void **) (&Tau_collector_api) = dlsym(handle, "__omp_collector_api");
            void *temp_fptr = dlsym(handle, "__omp_collector_api");
	        memcpy(&Tau_collector_api, &temp_fptr, sizeof(temp_fptr));
        }
    }
    // set this now, either it's there or it isn't.
    initialized = true;
#endif //if defined (BGL) || defined (BGP) || defined (BGQ) || defined (TAU_CRAYCNL)

    if (Tau_collector_api == NULL) {
        TAU_VERBOSE("__omp_collector_api symbol not found... collector API not enabled. \n"); fflush(stdout); fflush(stderr);
        initializing = false;
        return -1;
    }
#endif // TAU_DISABLE_SHARED
    TAU_VERBOSE("__omp_collector_api symbol found! Collector API enabled. \n"); fflush(stdout); fflush(stderr);

    int rc = 0;

    /*test: check for request start, 1 message */
    int * message = (int *)malloc(OMP_COLLECTORAPI_HEADERSIZE+sizeof(int));
	memset(message, 0, OMP_COLLECTORAPI_HEADERSIZE+sizeof(int));
    message[0] = OMP_COLLECTORAPI_HEADERSIZE;
    message[1] = OMP_REQ_START;
    message[2] = OMP_ERRCODE_OK;
    message[3] = 0;
    rc = (Tau_collector_api)(message);
    //TAU_VERBOSE("__omp_collector_api() returned %d\n", rc); fflush(stdout); fflush(stderr);
    free(message);

    /*test for request of all events*/
    int i;
    int num_req=OMP_EVENT_THR_END_FINISH_TASK; /* last event */
    if (TauEnv_get_openmp_runtime_events_enabled()) {
      int register_sz = sizeof(OMP_COLLECTORAPI_EVENT) + sizeof(unsigned long *);
      int message_sz = OMP_COLLECTORAPI_HEADERSIZE + register_sz;
	  //printf("Register size: %d, Message size: %d, bytes: %d\n", register_sz, message_sz, num_req*message_sz+sizeof(int));
      message = (int *) malloc(num_req*message_sz+sizeof(int));
	  memset(message, 0, num_req*message_sz+sizeof(int));
	  int * ptr = message;
      for(i=0;i<num_req;i++) {  
	      //printf("Ptr: %p\n", ptr);
          ptr[0] = message_sz;
          ptr[1] = OMP_REQ_REGISTER;
          ptr[2] = OMP_ERRCODE_OK;
          ptr[3] = 0;
          ptr[4] = OMP_EVENT_FORK + i;  // iterate over the events
          unsigned long * lmem = (unsigned long *)(ptr+5);
          *lmem = (unsigned long)Tau_omp_event_handler;
		  ptr = ptr + 7;
      } 
      rc = (Tau_collector_api)(message);
      TAU_VERBOSE("__omp_collector_api() returned %d\n", rc); fflush(stdout); fflush(stderr);
      free(message);
	}

    // preallocate messages, because we can't malloc when signals are
    // handled
    int state_rsz = sizeof(OMP_COLLECTOR_API_THR_STATE);
    int currentid_rsz = sizeof(unsigned long);
    int task_rsz = sizeof(int);
    for(i=0;i<omp_get_max_threads();i++) {  
	    // for getting thread state
        Tau_collector_flags[i].signal_message = (int*)malloc(OMP_COLLECTORAPI_HEADERSIZE+state_rsz+sizeof(int));
        memset(Tau_collector_flags[i].signal_message, 0, (OMP_COLLECTORAPI_HEADERSIZE+state_rsz+sizeof(int)));
        Tau_collector_flags[i].signal_message[0] = OMP_COLLECTORAPI_HEADERSIZE+state_rsz;
        Tau_collector_flags[i].signal_message[1] = OMP_REQ_STATE;
        Tau_collector_flags[i].signal_message[2] = OMP_ERRCODE_OK;
        Tau_collector_flags[i].signal_message[3] = state_rsz;
        // for getting region id
        Tau_collector_flags[i].region_message = (int *)malloc(OMP_COLLECTORAPI_HEADERSIZE+currentid_rsz+sizeof(int));
        memset(Tau_collector_flags[i].region_message, 0, (OMP_COLLECTORAPI_HEADERSIZE+currentid_rsz+sizeof(int)));
        Tau_collector_flags[i].region_message[0] = OMP_COLLECTORAPI_HEADERSIZE+currentid_rsz;
        Tau_collector_flags[i].region_message[1] = OMP_REQ_CURRENT_PRID;
        Tau_collector_flags[i].region_message[2] = OMP_ERRCODE_OK;
        Tau_collector_flags[i].region_message[3] = currentid_rsz;
        // for getting task id
        Tau_collector_flags[i].task_message = (int *)malloc(OMP_COLLECTORAPI_HEADERSIZE+task_rsz+sizeof(int));
        memset(Tau_collector_flags[i].task_message, 0, (OMP_COLLECTORAPI_HEADERSIZE+task_rsz+sizeof(int)));
        Tau_collector_flags[i].task_message[0] = OMP_COLLECTORAPI_HEADERSIZE+task_rsz;
        Tau_collector_flags[i].task_message[1] = OMP_REQ_CURRENT_PRID;
        Tau_collector_flags[i].task_message[2] = OMP_ERRCODE_OK;
        Tau_collector_flags[i].task_message[3] = task_rsz;
    }

#ifdef TAU_UNWIND
    //Tau_Sampling_register_unit(); // not necessary now?
#endif

    if (TauEnv_get_openmp_runtime_states_enabled() == 1) {
    // now, for the collector API support, create the 12 OpenMP states.
    // preallocate State timers. If we create them now, we won't run into
    // malloc issues later when they are required during signal handling.
      TAU_OPENMP_SET_LOCK;
      Tau_create_thread_state_if_necessary("OMP_UNKNOWN");
      Tau_create_thread_state_if_necessary("OMP_OVERHEAD");
      Tau_create_thread_state_if_necessary("OMP_WORKING");
      Tau_create_thread_state_if_necessary("OMP_IMPLICIT_BARRIER"); 
      Tau_create_thread_state_if_necessary("OMP_EXPLICIT_BARRIER");
      Tau_create_thread_state_if_necessary("OMP_IDLE");
      Tau_create_thread_state_if_necessary("OMP_SERIAL");
      Tau_create_thread_state_if_necessary("OMP_REDUCTION");
      Tau_create_thread_state_if_necessary("OMP_LOCK_WAIT");
      Tau_create_thread_state_if_necessary("OMP_CRITICAL_WAIT");
      Tau_create_thread_state_if_necessary("OMP_ORDERED_WAIT");
      Tau_create_thread_state_if_necessary("OMP_ATOMIC_WAIT");
      Tau_create_thread_state_if_necessary("OMP_TASK_CREATE");
      Tau_create_thread_state_if_necessary("OMP_TASK_SCHEDULE");
      Tau_create_thread_state_if_necessary("OMP_TASK_SUSPEND");
      Tau_create_thread_state_if_necessary("OMP_TASK_STEAL");
      Tau_create_thread_state_if_necessary("OMP_TASK_FINISH");
      TAU_OPENMP_UNSET_LOCK;
    }

    initializing = false;
    return 0;
}

extern "C" void __attribute__ ((destructor)) Tau_finalize_collector_api(void);

extern "C" void Tau_finalize_collector_api(void) {
    if (!initialized) return;
    TAU_OPENMP_SET_LOCK;
    std::map<unsigned long, char*>::iterator it = region_names.begin();
    while (it != region_names.end()) {
      std::map<unsigned long, char*>::iterator eraseme = it;
      ++it;
	  free(eraseme->second);
      region_names.erase(eraseme);
    }
    region_names.clear();
    it = task_names.begin();
    while (it != task_names.end()) {
      std::map<unsigned long, char*>::iterator eraseme = it;
      ++it;
	  free(eraseme->second);
      task_names.erase(eraseme);
    }
    task_names.clear();
    TAU_OPENMP_UNSET_LOCK;
    return;
#if 0
    TAU_VERBOSE("Tau_finalize_collector_api()\n");

    omp_collector_message req;
    void *message = (void *) malloc(4);   
    int *sz = (int *) message; 
    *sz = 0;
    int rc = 0;

    /*test check for request stop, 1 message */
    message = (void *) malloc(OMP_COLLECTORAPI_HEADERSIZE+sizeof(int));
    Tau_fill_header(message, OMP_COLLECTORAPI_HEADERSIZE, OMP_REQ_STOP, OMP_ERRCODE_OK, 0, 1);
    rc = (Tau_collector_api)(message);
    TAU_VERBOSE("__omp_collector_api() returned %d\n", rc);
    free(message);
#endif
}

extern "C" int Tau_get_thread_omp_state(int tid) {
    // if not available, return something useful
    if (Tau_collector_api == NULL) return -1;
    OMP_COLLECTOR_API_THR_STATE thread_state = THR_LAST_STATE;
    // query the thread state
    (Tau_collector_api)(Tau_collector_flags[tid].signal_message);
    thread_state = (OMP_COLLECTOR_API_THR_STATE)Tau_collector_flags[tid].signal_message[4];
    // return the thread state
    return (int)(thread_state);
}

#ifdef TAU_USE_OMPT

/********************************************************
 * The functions below are for the OMPT 4.0 interface.
 * ******************************************************/

/* 
 * This header file implements a dummy tool which will execute all
 * of the implemented callbacks in the OMPT framework. When a supported
 * callback function is executed, it will print a message with some
 * relevant information.
 */

/* MPC is using the latest version of the interface. Intel might also be using
 * the latest version. IBM is lagging behind - we only have access to the 
 * June 2013 version that supports an older interface. */
#ifdef TAU_MPC
// updated header
#include <ompt.h>
__thread int __local_tau_tid = -1;
int check_local_tid(void) {
/*
  if (__local_tau_tid == -1) {
    fprintf(stderr,"NEW THREAD!"); fflush(stderr);
    __local_tau_tid = MPCThreadLayer::RegisterThread();
    fprintf(stderr," %d\n",__local_tau_tid); fflush(stderr);
  }
*/
  return __local_tau_tid;
}
#define ompt_event_section_begin ompt_event_sections_begin 
#define ompt_event_section_end ompt_event_sections_end 
#else
#include <ompt.h>
// old event names
#define ompt_event_parallel_begin ompt_event_parallel_create 
#define ompt_event_parallel_end ompt_event_parallel_exit 
#define ompt_event_task_begin ompt_event_task_create 
#define ompt_event_task_end ompt_event_task_exit 
#define ompt_event_thread_begin ompt_event_thread_create 
#define ompt_event_thread_end ompt_event_thread_exit 
#define ompt_event_implicit_task_begin ompt_event_implicit_task_create 
#define ompt_event_implicit_task_end ompt_event_implicit_task_exit 
#endif

/* These two macros make sure we don't time TAU related events */

#ifdef TAU_MPC
#define TAU_OMPT_COMMON_ENTRY \
    fprintf(stderr, "OMPT event: %s\n", __func__); fflush(stderr); \
    /* Never process anything internal to TAU */ \
    if (Tau_global_get_insideTAU() > 0) { \
        return; \
    } \
    Tau_global_incr_insideTAU(); \
    check_local_tid(); \
    int tid = Tau_get_thread();
#else
#define TAU_OMPT_COMMON_ENTRY \
    /* Never process anything internal to TAU */ \
    if (Tau_global_get_insideTAU() > 0) { \
        return; \
    } \
    Tau_global_incr_insideTAU(); \
    int tid = Tau_get_thread();
#endif

#define TAU_OMPT_COMMON_EXIT \
    Tau_global_decr_insideTAU(); \
    fprintf(stderr, "Finished event: %s\n", __func__); fflush(stderr);

/*
 * Mandatory Events
 * 
 * The following events are supported by all OMPT implementations.
 */

/* Entering a parallel region */
extern "C" void my_parallel_region_begin (
  ompt_task_id_t parent_task_id,    /* id of parent task            */
  ompt_frame_t *parent_task_frame,  /* frame data of parent task    */
  ompt_parallel_id_t parallel_id,   /* id of parallel region        */
  uint32_t requested_team_size,     /* Region team size             */
  void *parallel_function)          /* pointer to outlined function */
{
  TAU_OMPT_COMMON_ENTRY;
  Tau_collector_flags[tid].regionid = parallel_id;
#ifdef TAU_IBM_OMPT
  Tau_collector_flags[tid].taskid = parallel_id; // necessary for IBM, appears broken
#endif
  Tau_get_current_region_context(tid, (unsigned long)parallel_function, false);
  TAU_VERBOSE("New Region: parent id = %lu, exit_runtime_frame = %p, reenter_runtime_frame = %p, parallel_id = %lu, parallel_function = %p %s %p\n", parent_task_id, parent_task_frame->exit_runtime_frame, parent_task_frame->reenter_runtime_frame, parallel_id, parallel_function, region_names[parallel_id], region_names[parallel_id]);
  Tau_omp_start_timer("OpenMP_PARALLEL_REGION", tid, 1, 1, false);
  Tau_collector_flags[tid].parallel++;
  TAU_OMPT_COMMON_EXIT;
}

/* Exiting a parallel region */
#ifdef TAU_MPC
extern "C" void my_parallel_region_end (
  ompt_parallel_id_t parallel_id,   /* id of parallel region        */
  ompt_task_id_t parent_task_id)    /* id of parent task            */
#else
extern "C" void my_parallel_region_end (
  ompt_task_id_t parent_task_id,    /* id of parent task            */
  ompt_frame_t *parent_task_frame,  /* frame data of parent task    */
  ompt_parallel_id_t parallel_id,   /* id of parallel region        */
  void *parallel_function)          /* pointer to outlined function */
#endif
{
  TAU_OMPT_COMMON_ENTRY;
  Tau_collector_flags[tid].regionid = parallel_id;
  if (Tau_collector_flags[tid].parallel>0) {
    Tau_omp_stop_timer("OpenMP_PARALLEL_REGION", tid, 1);
    Tau_collector_flags[tid].parallel--;
  }
  TAU_OPENMP_SET_LOCK;
  char * tmpStr = region_names[parallel_id];
  free(tmpStr);
  region_names.erase(parallel_id);
  TAU_OPENMP_UNSET_LOCK;
  TAU_OMPT_COMMON_EXIT;
}

/* Task creation */
extern "C" void my_task_begin (
  ompt_task_id_t parent_task_id,    /* id of parent task            */
  ompt_frame_t *parent_task_frame,  /* frame data for parent task   */
  ompt_task_id_t  new_task_id,      /* id of created task           */
  void *task_function)              /* pointer to outlined function */
{
  TAU_OMPT_COMMON_ENTRY;
  Tau_collector_flags[tid].taskid = new_task_id;
  TAU_VERBOSE("New Task: parent id = %lu, exit_runtime_frame = %p, reenter_runtime_frame = %p, new_task_id = %lu, task_function = %p\n", parent_task_id, parent_task_frame->exit_runtime_frame, parent_task_frame->reenter_runtime_frame, new_task_id, task_function); fflush(stderr);
  Tau_get_current_region_context(tid, (unsigned long)task_function, true);
  Tau_omp_start_timer("OpenMP_TASK", tid, 1, 0, true);
  TAU_OMPT_COMMON_EXIT;
}

/* Task exit */
extern "C" void my_task_end (
  ompt_task_id_t parent_task_id,    /* id of parent task            */
  ompt_frame_t *parent_task_frame,  /* frame data for parent task   */
  ompt_task_id_t  new_task_id,      /* id of created task           */
  void *task_function)              /* pointer to outlined function */
{
  TAU_OMPT_COMMON_ENTRY;
#ifdef TAU_MPC
  Tau_omp_stop_timer("OpenMP_TASK", tid, 1);
#else
  TAU_OPENMP_SET_LOCK;
  char * tmpStr = task_names[Tau_collector_flags[tid].taskid];
  free(tmpStr);
  task_names.erase(Tau_collector_flags[tid].taskid);
  TAU_OPENMP_UNSET_LOCK;
#endif
  TAU_OMPT_COMMON_EXIT;
}

/* Thread creation */
extern "C" void my_thread_begin(void) {
#ifdef TAU_MPC
  /* Never process anything internal to TAU */
  if (Tau_global_get_insideTAU() > 0) {
        return;
  }
  Tau_global_incr_insideTAU();
  int tid = MPCThreadLayer::RegisterThread();
#else
  TAU_OMPT_COMMON_ENTRY;
  //TAU_VERBOSE("OMPT Created thread: %d\n", tid); fflush(stdout);
#endif
  Tau_create_top_level_timer_if_necessary();
  TAU_OMPT_COMMON_EXIT;
}

/* Thread exit */
extern "C" void my_thread_end(void) {
  if (!Tau_RtsLayer_TheEnableInstrumentation()) return;
  TAU_OMPT_COMMON_ENTRY;
  //TAU_VERBOSE("OMPT Exiting thread: %d\n", tid); fflush(stdout);
  //Tau_stop_top_level_timer_if_necessary();
  TAU_OMPT_COMMON_EXIT;
}

/* Some control event happened */
extern "C" void my_control(uint64_t command, uint64_t modifier) {
  TAU_OMPT_COMMON_ENTRY;
  TAU_VERBOSE("OpenMP Control: %d, %llx, %llx\n", tid, command, modifier); fflush(stdout);
  // nothing to do here?
  TAU_OMPT_COMMON_EXIT;
}

extern "C" int Tau_profile_exit_all_tasks(void);

/* Shutting down the OpenMP runtime */
extern "C" void my_shutdown() {
  if (!Tau_RtsLayer_TheEnableInstrumentation()) return;
  TAU_OMPT_COMMON_ENTRY;
  TAU_VERBOSE("OpenMP Shutdown on thread %d.\n", tid); fflush(stdout);
  Tau_profile_exit_all_tasks();
  TAU_PROFILE_EXIT("exiting");
  // nothing to do here?
  TAU_OMPT_COMMON_EXIT;
}

/**********************************************************************/
/* End Mandatory Events */
/**********************************************************************/

/**********************************************************************/
/* Macros for common wait, acquire, release functionality. */
/**********************************************************************/

#define TAU_OMPT_WAIT_ACQUIRE_RELEASE(WAIT_FUNC,ACQUIRED_FUNC,RELEASE_FUNC,WAIT_NAME,REGION_NAME) \
extern "C" void WAIT_FUNC (ompt_wait_id_t *waitid) { \
  TAU_OMPT_COMMON_ENTRY; \
  Tau_omp_start_timer(WAIT_NAME,tid,1,0,false); \
  Tau_collector_flags[tid].waiting = 1; \
  TAU_OMPT_COMMON_EXIT; \
} \
 \
extern "C" void ACQUIRED_FUNC (ompt_wait_id_t *waitid) { \
  TAU_OMPT_COMMON_ENTRY; \
  if (Tau_collector_flags[tid].waiting>0) { \
    Tau_omp_stop_timer(WAIT_NAME,tid,1); \
  } \
  Tau_collector_flags[tid].waiting = 0; \
  Tau_omp_start_timer(REGION_NAME,tid,1,0,false); \
  Tau_collector_flags[tid].acquired = 1; \
  TAU_OMPT_COMMON_EXIT; \
} \
 \
extern "C" void RELEASE_FUNC (ompt_wait_id_t *waitid) { \
  TAU_OMPT_COMMON_ENTRY; \
  if (Tau_collector_flags[tid].acquired>0) { \
    Tau_omp_stop_timer(REGION_NAME,tid,1); \
  } \
  Tau_collector_flags[tid].acquired = 0; \
  TAU_OMPT_COMMON_EXIT; \
} \

TAU_OMPT_WAIT_ACQUIRE_RELEASE(my_wait_atomic,my_acquired_atomic,my_release_atomic,"OpenMP_ATOMIC_REGION_WAIT","OpenMP_ATOMIC_REGION")
TAU_OMPT_WAIT_ACQUIRE_RELEASE(my_wait_ordered,my_acquired_ordered,my_release_ordered,"OpenMP_ORDERED_REGION_WAIT","OpenMP_ORDERED_REGION")
TAU_OMPT_WAIT_ACQUIRE_RELEASE(my_wait_critical,my_acquired_critical,my_release_critical,"OpenMP_CRITICAL_REGION_WAIT","OpenMP_CRITICAL_REGION")
TAU_OMPT_WAIT_ACQUIRE_RELEASE(my_wait_lock,my_acquired_lock,my_release_lock,"OpenMP_LOCK_WAIT","OpenMP_LOCK")

#undef TAU_OMPT_WAIT_ACQUIRE_RELEASE

/**********************************************************************/
/* Macros for common begin / end functionality. */
/**********************************************************************/

#define TAU_OMPT_SIMPLE_BEGIN_AND_END(BEGIN_FUNCTION,END_FUNCTION,NAME) \
extern "C" void BEGIN_FUNCTION (ompt_parallel_id_t parallel_id, ompt_task_id_t task_id) { \
  TAU_OMPT_COMMON_ENTRY; \
  Tau_collector_flags[tid].regionid = parallel_id; \
  Tau_collector_flags[tid].taskid = task_id; \
  /*TAU_VERBOSE("New Entry: parallel_id = %lu, task_id = %lu %s\n", parallel_id, task_id, NAME); fflush(stderr); */\
  Tau_omp_start_timer(NAME, tid, 1, 0, false); \
  TAU_OMPT_COMMON_EXIT; \
} \
\
extern "C" void END_FUNCTION (ompt_parallel_id_t parallel_id, ompt_task_id_t task_id) { \
  TAU_OMPT_COMMON_ENTRY; \
  Tau_collector_flags[tid].regionid = parallel_id; \
  Tau_collector_flags[tid].taskid = task_id; \
  Tau_omp_stop_timer(NAME, tid, 0); \
  TAU_OMPT_COMMON_EXIT; \
}

#define TAU_OMPT_LOOP_BEGIN_AND_END(BEGIN_FUNCTION,END_FUNCTION,NAME) \
extern "C" void BEGIN_FUNCTION (ompt_parallel_id_t parallel_id, ompt_task_id_t task_id) { \
  TAU_OMPT_COMMON_ENTRY; \
  Tau_collector_flags[tid].regionid = parallel_id; \
  Tau_collector_flags[tid].taskid = task_id; \
  /*TAU_VERBOSE("New Entry: parallel_id = %lu, task_id = %lu %s\n", parallel_id, task_id, NAME); fflush(stderr); */\
  Tau_omp_start_timer(NAME, tid, 1, 0, false); \
  Tau_collector_flags[tid].looping=1; \
  TAU_OMPT_COMMON_EXIT; \
} \
\
extern "C" void END_FUNCTION (ompt_parallel_id_t parallel_id, ompt_task_id_t task_id) { \
  TAU_OMPT_COMMON_ENTRY; \
  Tau_collector_flags[tid].regionid = parallel_id; \
  Tau_collector_flags[tid].taskid = task_id; \
  if (Tau_collector_flags[tid].looping==1) { \
  Tau_omp_stop_timer(NAME, tid, 0); } \
  Tau_collector_flags[tid].looping=0; \
  TAU_OMPT_COMMON_EXIT; \
}

TAU_OMPT_SIMPLE_BEGIN_AND_END(my_barrier_begin,my_barrier_end,"OpenMP_BARRIER")
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_implicit_task_begin,my_implicit_task_end,"OpenMP_IMPLICIT_TASK")
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_wait_barrier_begin,my_wait_barrier_end,"OpenMP_WAIT_BARRIER")
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_master_begin,my_master_end,"OpenMP_MASTER_REGION")
TAU_OMPT_LOOP_BEGIN_AND_END(my_loop_begin,my_loop_end,"OpenMP_LOOP")
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_section_begin,my_section_end,"OpenMP_SECTION") 
//TAU_OMPT_SIMPLE_BEGIN_AND_END(my_single_in_block_begin,my_single_in_block_end,"OpenMP_SINGLE_IN_BLOCK") 
//TAU_OMPT_SIMPLE_BEGIN_AND_END(my_single_others_begin,my_single_others_end,"OpenMP_SINGLE_OTHERS") 
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_taskwait_begin,my_taskwait_end,"OpenMP_TASKWAIT") 
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_wait_taskwait_begin,my_wait_taskwait_end,"OpenMP_WAIT_TASKWAIT") 
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_taskgroup_begin,my_taskgroup_end,"OpenMP_TASKGROUP") 
TAU_OMPT_SIMPLE_BEGIN_AND_END(my_wait_taskgroup_begin,my_wait_taskgroup_end,"OpenMP_WAIT_TASKGROUP") 

#undef TAU_OMPT_SIMPLE_BEGIN_AND_END

/**********************************************************************/
/* Specialized begin / end functionality. */
/**********************************************************************/

/* Thread end idle */
extern "C" void my_idle_end(void) {
  if (!Tau_RtsLayer_TheEnableInstrumentation()) return;
  TAU_OMPT_COMMON_ENTRY;
  Tau_omp_stop_timer("IDLE", tid, 0);
  // if this thread is not the master of a team, then assume this 
  // thread is entering a new parallel region
  if (Tau_collector_flags[tid].parallel==0) {
    Tau_omp_start_timer("OpenMP_PARALLEL_REGION", tid, 1, 1, false);
    Tau_collector_flags[tid].busy = 1;
  }
  Tau_collector_flags[tid].idle = 0;
  TAU_OMPT_COMMON_EXIT;
}

/* Thread begin idle */
extern "C" void my_idle_begin(void) {
  TAU_OMPT_COMMON_ENTRY;
  // if this thread is not the master of a team, then assume this 
  // thread is exiting a parallel region
  if (Tau_collector_flags[tid].parallel==0) {
    if (Tau_collector_flags[tid].idle == 1 && 
        Tau_collector_flags[tid].busy == 0) {
        TAU_OMPT_COMMON_EXIT;
        return;
    }
    if (Tau_collector_flags[tid].busy == 1) {
        Tau_omp_stop_timer("OpenMP_PARALLEL_REGION", tid, 1);
        Tau_collector_flags[tid].busy = 0;
    }
  }
  Tau_collector_flags[tid].idle = 1;
  Tau_omp_start_timer("IDLE", tid, 0, 0, false);
  TAU_OMPT_COMMON_EXIT;
}

#undef TAU_OMPT_COMMON_ENTRY
#undef TAU_OMPT_COMMON_EXIT

// This macro is for checking that the function registration worked.
#define CHECK(EVENT,FUNCTION,NAME) \
  TAU_VERBOSE("Registering OMPT callback %s...",NAME); \
  fflush(stderr); \
  if (ompt_set_callback(EVENT, (ompt_callback_t)(FUNCTION)) == 0) { \
    TAU_VERBOSE("\n\tFailed to register OMPT callback %s!\n",NAME); \
    fflush(stderr); \
  } else { \
    TAU_VERBOSE("success.\n"); \
  } \

/* These will be used when the OMPT interface is updated */

#ifdef TAU_MPC
//ompt_enumerate_state_t ompt_enumerate_state;
//ompt_set_callback_t ompt_set_callback;
//ompt_get_state_t ompt_get_state;
extern "C" ompt_state_t ompt_get_state(ompt_wait_id_t *ompt_wait_id);
extern "C" int ompt_enumerate_state(int current_state, int *next_state, const char **next_state_name);
extern "C" int ompt_set_callback(ompt_event_t event_type, ompt_callback_t callback);
#endif

#ifdef TAU_MPC
int __ompt_initialize() {
  check_local_tid();
#else
int ompt_initialize() {
#endif
  Tau_init_initializeTAU();
  if (initialized || initializing) return 0;
  if (!TauEnv_get_openmp_runtime_enabled()) return 0;
  TAU_VERBOSE("Registering OMPT events...\n"); fflush(stderr);
  initializing = true;
  TAU_OPENMP_INIT_LOCK;

  /* required events */
  CHECK(ompt_event_parallel_begin, my_parallel_region_begin, "parallel_begin");
  CHECK(ompt_event_parallel_end, my_parallel_region_end, "parallel_end");
#ifndef TAU_IBM_OMPT
  // IBM will call task_begin, but not task_end. :(
  CHECK(ompt_event_task_begin, my_task_begin, "task_begin");
  CHECK(ompt_event_task_end, my_task_end, "task_end");
#endif
  CHECK(ompt_event_thread_begin, my_thread_begin, "thread_begin");
  CHECK(ompt_event_thread_end, my_thread_end, "thread_end");
  CHECK(ompt_event_control, my_control, "event_control");
#ifndef TAU_IBM_OMPT
  CHECK(ompt_event_runtime_shutdown, my_shutdown, "runtime_shutdown");
#endif /* TAU_IBM_OMPT */

  if (TauEnv_get_openmp_runtime_events_enabled()) {
  /* optional events, "blameshifting" */
#ifndef TAU_IBM_OMPT 
  // actually, don't do the idle event at all for now
  //CHECK(ompt_event_idle_begin, my_idle_begin, "idle_begin");
  //CHECK(ompt_event_idle_end, my_idle_end, "idle_end");
  
  // IBM will call wait_barrier_begin, but not wait_barrier_end. :(
  CHECK(ompt_event_wait_barrier_begin, my_wait_barrier_begin, "wait_barrier_begin");
  CHECK(ompt_event_wait_barrier_end, my_wait_barrier_end, "wait_barrier_end");
#endif
  CHECK(ompt_event_wait_taskwait_begin, my_wait_taskwait_begin, "wait_taskwait_begin");
  CHECK(ompt_event_wait_taskwait_end, my_wait_taskwait_end, "wait_taskwait_end");
  CHECK(ompt_event_wait_taskgroup_begin, my_wait_taskgroup_begin, "wait_taskgroup_begin");
  CHECK(ompt_event_wait_taskgroup_end, my_wait_taskgroup_end, "wait_taskgroup_end");
  CHECK(ompt_event_release_lock, my_release_lock, "release_lock");
//ompt_event(ompt_event_release_nest_lock_last, ompt_wait_callback_t, 18, ompt_event_release_nest_lock_implem
  CHECK(ompt_event_release_critical, my_release_critical, "release_critical");
  CHECK(ompt_event_release_atomic, my_release_atomic, "release_atomic");
  CHECK(ompt_event_release_ordered, my_release_ordered, "release_ordered");

  /* optional events, synchronous events */
#if !defined(TAU_IBM_OMPT) && !defined(TAU_MPC)
  // IBM will call task_begin, but not task_end. :(
  CHECK(ompt_event_implicit_task_begin, my_implicit_task_begin, "implicit_task_begin");
  CHECK(ompt_event_implicit_task_end, my_implicit_task_end, "implicit_task_end");
#endif
  CHECK(ompt_event_barrier_begin, my_barrier_begin, "barrier_begin");
  CHECK(ompt_event_barrier_end, my_barrier_end, "barrier_end");
  CHECK(ompt_event_master_begin, my_master_begin, "master_begin");
  CHECK(ompt_event_master_end, my_master_end, "master_end");
//ompt_event(ompt_event_task_switch, ompt_task_switch_callback_t, 24, ompt_event_task_switch_implemented) /* 
  CHECK(ompt_event_loop_begin, my_loop_begin, "loop_begin");
  CHECK(ompt_event_loop_end, my_loop_end, "loop_end");
  CHECK(ompt_event_section_begin, my_section_begin, "section_begin");
  CHECK(ompt_event_section_end, my_section_end, "section_end");
/* When using Intel, there are times when the non-single thread continues on its
 * merry way. For now, don't track the time spent in the "other" threads. 
 * We have no way of knowing when the other threads finish waiting, because for
 * Intel they don't wait - they just continue. */
  //CHECK(ompt_event_single_in_block_begin, my_single_in_block_begin, "single_in_block_begin");
  //CHECK(ompt_event_single_in_block_end, my_single_in_block_end, "single_in_block_end");
  //CHECK(ompt_event_single_others_begin, my_single_others_begin, "single_others_begin");
  //CHECK(ompt_event_single_others_end, my_single_others_end, "single_others_end");
  CHECK(ompt_event_taskwait_begin, my_taskwait_begin, "taskwait_begin");
  CHECK(ompt_event_taskwait_end, my_taskwait_end, "taskwait_end");
  CHECK(ompt_event_taskgroup_begin, my_taskgroup_begin, "taskgroup_begin");
  CHECK(ompt_event_taskgroup_end, my_taskgroup_end, "taskgroup_end");

//ompt_event(ompt_event_release_nest_lock_prev, ompt_parallel_callback_t, 41, ompt_event_release_nest_lock_pr

  CHECK(ompt_event_wait_lock, my_wait_lock, "wait_lock");
//ompt_event(ompt_event_wait_nest_lock, ompt_wait_callback_t, 43, ompt_event_wait_nest_lock_implemented) /* n
  CHECK(ompt_event_wait_critical, my_wait_critical, "wait_critical");
  CHECK(ompt_event_wait_atomic, my_wait_atomic, "wait_atomic");
  CHECK(ompt_event_wait_ordered, my_wait_ordered, "wait_ordered");

  CHECK(ompt_event_acquired_lock, my_acquired_lock, "acquired_lock");
//ompt_event(ompt_event_acquired_nest_lock_first, ompt_wait_callback_t, 48, ompt_event_acquired_nest_lock_fir
//ompt_event(ompt_event_acquired_nest_lock_next, ompt_parallel_callback_t, 49, ompt_event_acquired_nest_lock_
  CHECK(ompt_event_acquired_critical, my_acquired_critical, "acquired_critical");
  CHECK(ompt_event_acquired_atomic, my_acquired_atomic, "acquired_atomic");
  CHECK(ompt_event_acquired_ordered, my_acquired_ordered, "acquired_ordered");

//ompt_event(ompt_event_init_lock, ompt_wait_callback_t, 53, ompt_event_init_lock_implemented) /* lock init *
//ompt_event(ompt_event_init_nest_lock, ompt_wait_callback_t, 54, ompt_event_init_nest_lock_implemented) /* n
//ompt_event(ompt_event_destroy_lock, ompt_wait_callback_t, 55, ompt_event_destroy_lock_implemented) /* lock 
//ompt_event(ompt_event_destroy_nest_lock, ompt_wait_callback_t, 56, ompt_event_destroy_nest_lock_implemented

//ompt_event(ompt_event_flush, ompt_thread_callback_t, 57, ompt_event_flush_implemented) /* after executing f
  }
  TAU_VERBOSE("OMPT events registered! \n"); fflush(stderr);

#if defined(TAU_USE_OMPT) || defined(TAU_IBM_OMPT)
// make the states
  if (TauEnv_get_openmp_runtime_states_enabled() == 1) {
    // now, for the collector API support, create the OpenMP states.
    // preallocate State timers. If we create them now, we won't run into
    // malloc issues later when they are required during signal handling.
    int current_state = ompt_state_work_serial;
    int next_state;
    const char *next_state_name;
    std::string *next_state_name_string;
	std::string *serial = new std::string("ompt_state_work_serial");
    OMPT_STATE_NAMES[ompt_state_work_serial] = serial;
    Tau_create_thread_state_if_necessary("ompt_state_work_serial");
    while (ompt_enumerate_state(current_state, &next_state, &next_state_name) == 1) {
      TAU_VERBOSE("Got state %d: '%s'\n", next_state, next_state_name);
      if (next_state >= 128) {
        TAU_VERBOSE("WARNING! MORE OMPT STATES THAN EXPECTED! PROGRAM COULD CRASH!!!\n");
      }
	  next_state_name_string = new std::string(next_state_name);
      OMPT_STATE_NAMES[next_state] = next_state_name_string;
      Tau_create_thread_state_if_necessary(next_state_name);
      current_state = next_state;
    }
    // next_state now holds our max 
  }
  TAU_VERBOSE("OMPT states registered! \n"); fflush(stderr);
#endif

  initializing = false;
  initialized = true;

  return 1;
}

#ifdef TAU_MPC
// the newest version of the library will have a version as well
extern "C" int ompt_initialize(ompt_function_lookup_t lookup, const char *runtime_version, int ompt_version) {
  fprintf(stderr, "Init: %s ver %i\n",runtime_version,ompt_version);
  //ompt_set_callback = (ompt_set_callback_t) lookup("ompt_set_callback");
  //ompt_enumerate_state = (ompt_enumerate_state_t) lookup("ompt_enumerate_state");
  //ompt_get_state = (ompt_get_state_t) lookup("ompt_get_state");
  __ompt_initialize();
}
#endif

#if defined(TAU_USE_OMPT) || defined(TAU_IBM_OMPT)
std::string * Tau_get_thread_ompt_state(int tid) {
    // if not available, return something useful
    if (!initialized) return NULL;
    // query the thread state
    ompt_wait_id_t wait;
    ompt_state_t state = ompt_get_state(&wait);
    //TAU_VERBOSE("Thread %d, state : %d\n", tid, state);
    // return the thread state as a string
    return OMPT_STATE_NAMES[state];
}
#endif

#else // TAU_USE_OMPT
///* THESE ARE OTHER WEAK IMPLEMENTATIONS, IN CASE OMPT SUPPORT IS NONEXISTENT */
///* initialization */
//extern "C" __attribute__ (( weak ))
  //int ompt_set_callback(ompt_event_t evid, ompt_callback_t cb) { return -1; };
#endif // TAU_USE_OMPT

/* THESE ARE OTHER WEAK IMPLEMENTATIONS, IN CASE COLLECTOR API SUPPORT IS NONEXISTENT */
#if !defined (TAU_OPEN64ORC)
#if defined __GNUC__
extern __attribute__ ((weak))
  int __omp_collector_api(void *message) { TAU_VERBOSE ("Error linking GOMP wrapper. Try using tau_exec with the -gomp option.\n"); return -1; };
#endif
#endif

extern "C" __attribute__ ((weak))
void * Tau_get_gomp_proxy_address(void);

