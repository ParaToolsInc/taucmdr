/****************************************************************************
 **			TAU Portable Profiling Package			   **
 **			http://www.cs.uoregon.edu/research/tau	           **
 *****************************************************************************
 **    Copyright 2009                                                       **
 **    Department of Computer and Information Science, University of Oregon **
 **    Advanced Computing Laboratory, Los Alamos National Laboratory        **
 ****************************************************************************/
/****************************************************************************
 **	File            : TauSampling.cpp                                  **
 **	Description     : TAU Profiling Package				   **
 **	Contact		: tau-bugs@cs.uoregon.edu                          **
 **	Documentation	: See http://www.cs.uoregon.edu/research/tau       **
 **                                                                         **
 **      Description     : This file contains all the sampling related code **
 **                                                                         **
 ****************************************************************************/

/****************************************************************************
 *
 *                      University of Illinois/NCSA
 *                          Open Source License
 *
 *          Copyright(C) 2004-2006, The Board of Trustees of the
 *              University of Illinois. All rights reserved.
 *
 *                             Developed by:
 *
 *                        The PerfSuite Project
 *            National Center for Supercomputing Applications
 *              University of Illinois at Urbana-Champaign
 *
 *                   http://perfsuite.ncsa.uiuc.edu/
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the "Software"),
 * to deal with the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * + Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimers.
 * + Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimers in
 *   the documentation and/or other materials provided with the distribution.
 * + Neither the names of The PerfSuite Project, NCSA/University of Illinois
 *   at Urbana-Champaign, nor the names of its contributors may be used to
 *   endorse or promote products derived from this Software without specific
 *   prior written permission.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS WITH THE SOFTWARE.
 ****************************************************************************/

#ifdef __APPLE__
#define _XOPEN_SOURCE 600 /* Single UNIX Specification, Version 3 */
#endif /* __APPLE__ */

#ifndef TAU_WINDOWS

#include <TAU.h>
#include <Profile/TauMetrics.h>
#include <Profile/TauSampling.h>
#include <Profile/TauBfd.h>
#include <tau_internal.h>

#include <sys/time.h>
#include <stdio.h>
#include <string.h>
#include <sstream>
#include <sys/types.h>
#include <signal.h>
#include <stdlib.h>
#include <strings.h>

/* Android didn't provide <ucontext.h> so we make our own */
#ifdef TAU_ANDROID
#include "TauJAPI.h"
#include "android_ucontext.h"
#else
#include <ucontext.h>
#endif

#include <string>
#include <vector>

#ifdef TAU_OPENMP
#include <omp.h>
#endif

#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#ifdef SIGEV_THREAD_ID
#ifndef sigev_notify_thread_id
#define sigev_notify_thread_id _sigev_un._tid
#endif /* ifndef sigev_notify_thread_id */
#endif /* ifdef SIGEV_THREAD_ID */

#define TAU_THOUSAND 1000
#define TAU_MILLION  1000000
#define TAU_BILLION  1000000000

#if defined(TAU_USE_PGS)
#include <pthread.h>
#endif

using namespace std;
using namespace tau;

extern FunctionInfo * Tau_create_thread_state_if_necessary(const char* thread_state);
extern FunctionInfo * Tau_create_thread_state_if_necessary_string(const string & thread_state);
extern "C" int Tau_get_thread_omp_state(int tid);
extern std::string * Tau_get_thread_ompt_state(int tid);

#if defined(TAU_OPENMP) && !defined(TAU_USE_OMPT)
static string _gTauOmpStatesArray[17] = { "OMP_UNKNOWN", "OMP_OVERHEAD", "OMP_WORKING", "OMP_IMPLICIT_BARRIER",
    "OMP_EXPLICIT_BARRIER", "OMP_IDLE", "OMP_SERIAL", "OMP_REDUCTION", "OMP_LOCK_WAIT", "OMP_CRITICAL_WAIT",
    "OMP_ORDERED_WAIT", "OMP_ATOMIC_WAIT", "OMP_TASK_CREATE", "OMP_TASK_SCHEDULE", "OMP_TASK_SUSPEND", "OMP_TASK_STEAL",
    "OMP_TASK_FINISH" };

static const string & gTauOmpStates(int index)
{
  if (index >= 1 && index <= 16) {
    return _gTauOmpStatesArray[index];
  }
  return _gTauOmpStatesArray[0];
}

#endif

/*
 see:
 http://ftp.gnu.org/old-gnu/Manuals/glibc-2.2.3/html_node/libc_463.html#SEC473
 for details.  When using SIGALRM and ITIMER_REAL on MareNostrum (Linux on
 PPC970MP) the network barfs.  When using ITIMER_PROF and SIGPROF, everything
 was fine...
 //int which = ITIMER_REAL;
 //int TAU_ALARM_TYPE = SIGALRM;
 */

/* always use SIGPROF, for now... */

//#if defined(PTHREADS) || defined(TAU_OPENMP)
int TAU_ITIMER_TYPE = ITIMER_PROF;
int TAU_ALARM_TYPE = SIGPROF;
//#else
//int TAU_ITIMER_TYPE = ITIMER_REAL;
//int TAU_ALARM_TYPE = SIGALRM;
//#endif

/*************************************
 * Shared Unwinder function prototypes.
 * These are internal to TAU and does
 *   not need to be extern "C"
 *************************************/
#ifdef TAU_UNWIND
extern void Tau_sampling_outputTraceCallstack(int tid, void *pc,
    void *context);
// *CWL* NOTE: This note applies to all implementations of the TAU context unwind -
//             The reason we unwind up to TAU_SAMP_NUM_ADDRESSES times is
//               because we cannot know, apriori, the exact number of function
//               calls made by TAU (eg. dependance on compilers) between the user
//               code representing that context to the point in TAU where we begin to
//               unwind the event context. All we know is we can safely drop
//               exactly 1 call layer, which explains the "skip" variable 
//               (see TauSampling_libunwind). This layer is invariably
//               "Tau_sampling_event_start"
//
//             The same is not true for sampling, where the signal handler itself
//             provides the originating context.
extern void Tau_sampling_unwindTauContext(int tid, void **address);
extern void Tau_sampling_unwind(int tid, Profiler *profiler,
    void *pc, void *context, unsigned long stack[]);

extern "C" bool unwind_cutoff(void **addresses, void *address) {
  // if the unwind depth is not "auto", then return
  if (TauEnv_get_ebs_unwind_depth() > 0)
  return false;
  bool found = false;
  for (int i=0; i<TAU_SAMP_NUM_ADDRESSES; i++) {
    if ((unsigned long)(addresses[i]) == (unsigned long)address) {
      //      printf("match found %p\n", address);
      found = true;
      break;
    }
  }
  return found;
}

#endif /* TAU_UNWIND */

/*********************************************************************
 * Tau Sampling Record Definition
 ********************************************************************/
typedef struct
{
  unsigned long pc;
  x_uint64 timestamp;
  double counters[TAU_MAX_COUNTERS];
  double counterDeltaStart[TAU_MAX_COUNTERS];
  double counterDeltaStop[TAU_MAX_COUNTERS];
  unsigned long deltaStart;
  unsigned long deltaStop;
} TauSamplingRecord;

struct CallSiteCandidate
{
  CallSiteCandidate(unsigned long * pc, unsigned int count, FunctionInfo * ctx) :
      pcStack(pc), sampleCount(count), tauContext(ctx)
  {
  }

  unsigned long * pcStack;
  unsigned int sampleCount;
  FunctionInfo * tauContext;
  double counters[TAU_MAX_COUNTERS];
};

struct CallSiteInfo
{
  CallSiteInfo(unsigned long _pc) :
      pc(_pc)
  {
  }

  unsigned long pc;
  int moduleIdx;
  char *name;
};

// *CWL* - Keeping this structure in case we need extra fields
struct CallStackInfo
{
  vector<CallSiteInfo*> callSites;
};

/*********************************************************************
 * Global Variables
 ********************************************************************/

// Map for sample callsite/intermediate names to FunctionInfo objects.
//   We need this for two reasons:
//   1. because multiple sample addresses can map to the same source
//      line.
//   2. because multiple candidate samples can belong to the same
//      TAU context and we need to determine if an intermediate
//      FunctionInfo object has already been created for that context.
static map<string, FunctionInfo *> *name2FuncInfoMap[TAU_MAX_THREADS];

struct CallSiteCacheNode
{
  bool resolved;
  TauBfdInfo info;
};

//typedef TAU_HASH_MAP<unsigned long, CallSiteCacheNode*> CallSiteCacheMap;
struct CallSiteCacheMap: public TAU_HASH_MAP<unsigned long, CallSiteCacheNode*>
{
  CallSiteCacheMap() {}
  virtual ~CallSiteCacheMap() {
    //Wait! We might not be done! Unbelieveable as it may seem, this map
    //could (and does sometimes) get destroyed BEFORE we have resolved the addresses. Bummer.
    Tau_sampling_finalize_if_necessary();
  }
};

static CallSiteCacheMap & TheCallSiteCache()
{
  static CallSiteCacheMap map;
  return map;
}

static tau_bfd_handle_t & TheBfdUnitHandle()
{
  static tau_bfd_handle_t bfdUnitHandle = TAU_BFD_NULL_HANDLE;
  if (bfdUnitHandle == TAU_BFD_NULL_HANDLE) {
    RtsLayer::LockEnv();
    if (bfdUnitHandle == TAU_BFD_NULL_HANDLE) {
      bfdUnitHandle = Tau_bfd_registerUnit();
    }
    RtsLayer::UnLockEnv();
  }
  return bfdUnitHandle;
}

/* This structure holds the per-thread data for managing sampling results */

struct tau_sampling_flags
{
  /* Sample processing enabled/disabled */
  int samplingEnabled;
  /* Sample processing suspended/resumed */
  int suspendSampling;
  long long numSamples;
  long long samplesDroppedTau;
  long long samplesDroppedSuspended;
  // save the previous timestamp so that we can increment the accumulator
  // each time we get a sample
  x_uint64 previousTimestamp[TAU_MAX_COUNTERS];
  /* The trace for this node, mulithreaded execution currently not supported? */
  FILE *ebsTrace;
};

/* depending on the compiler support, use the fastest solution */

#ifdef TAU_USE_TLS
// thread local storage
__thread struct tau_sampling_flags tau_sampling_tls_flags;
static inline struct tau_sampling_flags *tau_sampling_flags(void)
{ return &tau_sampling_tls_flags;}
#elif defined(TAU_USE_DTLS)
// thread local storage
__declspec(thread) struct tau_sampling_flags tau_sampling_tls_flags;
static inline struct tau_sampling_flags *tau_sampling_flags(void)
{ return &tau_sampling_tls_flags;}
#elif defined(TAU_USE_PGS)
// pthread specific
pthread_key_t tau_sampling_tls_key;
static inline struct tau_sampling_flags *tau_sampling_flags(void)
{ return (struct tau_sampling_flags*)(pthread_getspecific(tau_sampling_tls_key));}
#else
// worst case - array of flags, one for each thread.
struct tau_sampling_flags tau_sampling_tls_flags[TAU_MAX_THREADS];
static inline struct tau_sampling_flags *tau_sampling_flags(void)
{
  return &tau_sampling_tls_flags[Tau_get_local_tid()];
}
#endif

/* The trace for this node, mulithreaded execution currently not supported */
//FILE *ebsTrace[TAU_MAX_THREADS] = { NULL };
/* we need a process-wide flag for disabling sampling at program exit. */
int collectingSamples = 0;

// When we register our signal handler, we have to save any existing handler,
// so that we can call it when we are done.
static struct sigaction application_sa;

/*********************************************************************
 * Get the architecture specific PC
 ********************************************************************/

#if __WORDSIZE == 32
#define UCONTEXT_REG(uc, reg) ((uc)->uc_mcontext.uc_regs->gregs[reg])
#else
#define UCONTEXT_REG(uc, reg) ((uc)->uc_mcontext.gp_regs[reg])
#endif

#define PPC_REG_PC 32

#if (defined(sun) || defined(__APPLE__) || defined(_AIX)) || \
    (!defined(TAU_BGP) && !defined(TAU_BGQ) && !defined(__x86_64__) && \
    !defined(i386) && !defined(__ia64__) && !defined(__powerpc64__) && \
	!defined(__powerpc__) && !defined(__arm__))
static void issueUnavailableWarning(const char *text)
{
  static bool warningIssued = false;
  if (!warningIssued) {
    fprintf(stderr, "%s", text);
    warningIssued = true;
  }
}
#endif

unsigned long get_pc(void *p)
{
  unsigned long pc;

  /* SUN SUPPORT */

#ifdef sun
  issueUnavailableWarning("Warning, TAU Sampling does not work on Solaris\n");
  return 0;

  /* APPLE SUPPORT */

#elif __APPLE__
  issueUnavailableWarning("Warning, TAU Sampling works on Apple, but symbol lookup using BFD might not.\n");
  ucontext_t *uct = (ucontext_t *)p;
  //printf("%p\n", uct->uc_mcontext->__ss.__rip);
  //Careful here, we need to support ppc macs as well.
#if defined(_STRUCT_X86_THREAD_STATE64) && !defined(__i386__)
  pc = uct->uc_mcontext->__ss.__rip;
#elif defined (__i386__)
  pc = uct->uc_mcontext->__ss.__eip;
#else
  pc = uct->uc_mcontext->__ss.__srr0;
#endif /* defined(_STRUCT_X86_THREAD_STATE64) && !defined(__i386__) */
  return pc;

  /* AIX SUPPORT */

#elif _AIX
  issueUnavailableWarning("Warning, TAU Sampling does not work on AIX\n");
  return 0;

  /* EVERYTHING ELSE SUPPORT */

#else
  struct ucontext *uc = (struct ucontext *)p;
  struct sigcontext *sc;
  sc = (struct sigcontext *)&uc->uc_mcontext;
#ifdef TAU_BGP
  //  pc = (unsigned long)sc->uc_regs->gregs[PPC_REG_PC];
  pc = (unsigned long)UCONTEXT_REG(uc, PPC_REG_PC);
# elif defined(TAU_BGQ)
  //  201203 - Thanks to the Open|Speedshop team!
  pc = (unsigned long)((struct pt_regs *)(((&(uc->uc_mcontext))->regs))->nip);
# elif __x86_64__
  pc = (unsigned long)sc->rip;
# elif i386
  pc = (unsigned long)sc->eip;
# elif __ia64__
  pc = (unsigned long)sc->sc_ip;
# elif __powerpc64__
  // it could possibly be "link" - but that is supposed to be the return address.
  pc = (unsigned long)sc->regs->nip;
# elif __powerpc__
  // it could possibly be "link" - but that is supposed to be the return address.
  pc = (unsigned long)sc->regs->nip;
# elif __arm__
  pc = (unsigned long)sc->arm_pc;
#elif defined(TAU_FUJITSU)
  pc = ((struct sigcontext *)p)->sigc_regs.tpc;
# else
  issueUnavailableWarning("Warning, TAU Sampling does not work on unknown platform.\n");
  return 0;
# endif /* TAU_BGP, BGQ, __x86_64__, i386, __ia64__, __powerpc64__, __powerpc__, __arm__ */
  return pc;
#endif /* sun, APPLE, AIX */
}

extern "C" FILE* Tau_sampling_get_ebsTrace()
{
  return tau_sampling_flags()->ebsTrace;
}

extern "C" void Tau_sampling_suspend(int tid)
{
  tau_sampling_flags()->suspendSampling = 1;
}

extern "C" void Tau_sampling_resume(int tid)
{
  tau_sampling_flags()->suspendSampling = 0;
}

// TODO: Why is this here?  For HPC Toolkit?
extern "C" void Tau_sampling_dlopen()
{
  fprintf(stderr, "TAU: got a dlopen\n");
}

/*******************************************
 * EBS Tracing Input/Output Routines
 *******************************************/

void Tau_sampling_outputTraceHeader(int tid)
{
  fprintf(tau_sampling_flags()->ebsTrace, "# Format version: 0.2\n");
  fprintf(tau_sampling_flags()->ebsTrace,
      "# $ | <timestamp> | <delta-begin> | <delta-end> | <metric 1> ... <metric N> | <tau callpath> | <location> [ PC callstack ]\n");
  fprintf(tau_sampling_flags()->ebsTrace,
      "# %% | <delta-begin metric 1> ... <delta-begin metric N> | <delta-end metric 1> ... <delta-end metric N> | <tau callpath>\n");
  fprintf(tau_sampling_flags()->ebsTrace, "# Metrics:");
  for (int i = 0; i < Tau_Global_numCounters; i++) {
    const char *name = TauMetrics_getMetricName(i);
    fprintf(tau_sampling_flags()->ebsTrace, " %s", name);
  }
  fprintf(tau_sampling_flags()->ebsTrace, "\n");
}

void Tau_sampling_outputTraceCallpath(int tid)
{
  Profiler *profiler = TauInternal_CurrentProfiler(tid);
  // *CWL* 2012/3/18 - EBS traces cannot handle callsites for now. Do not track.
  if ((profiler->CallPathFunction != NULL) && (TauEnv_get_callpath())) {
    fprintf(tau_sampling_flags()->ebsTrace, "%lld", profiler->CallPathFunction->GetId());
  } else if (profiler->ThisFunction != NULL) {
    fprintf(tau_sampling_flags()->ebsTrace, "%lld", profiler->ThisFunction->GetId());
  }
}

void Tau_sampling_flushTraceRecord(int tid, TauSamplingRecord *record, void *pc, ucontext_t *context)
{
  fprintf(tau_sampling_flags()->ebsTrace, "$ | %lld | ", record->timestamp);

#ifdef TAU_EXP_DISABLE_DELTAS
  fprintf(tau_sampling_flags()->ebsTrace, "0 | 0 | ");
#else
  fprintf(tau_sampling_flags()->ebsTrace, "%lu | %lu | ", record->deltaStart, record->deltaStop);
#endif

  for (int i = 0; i < Tau_Global_numCounters; i++) {
    fprintf(tau_sampling_flags()->ebsTrace, "%.16G ", record->counters[i]);
  }

  fprintf(tau_sampling_flags()->ebsTrace, "| ");

  /* *CWL* - consider a check for TauEnv_get_callpath() here */
  Tau_sampling_outputTraceCallpath(tid);

  fprintf(tau_sampling_flags()->ebsTrace, " | %p", (void*)(record->pc));

#ifdef TAU_UNWIND
  if (TauEnv_get_ebs_unwind() == 1) {
    Tau_sampling_outputTraceCallstack(tid, pc, context);
  }
#endif /* TAU_UNWIND */

  // do nothing?
  //fprintf(tau_sampling_flags()->ebsTrace, "");
}

void Tau_sampling_outputTraceStop(int tid, Profiler *profiler, double *stopTime)
{
  fprintf(tau_sampling_flags()->ebsTrace, "%% | ");

  for (int i = 0; i < Tau_Global_numCounters; i++) {
    double startTime = profiler->StartTime[i]; // gtod must be counter 0
    x_uint64 start = (x_uint64)startTime;
    fprintf(tau_sampling_flags()->ebsTrace, "%lld ", start);
  }
  fprintf(tau_sampling_flags()->ebsTrace, "| ");

  for (int i = 0; i < Tau_Global_numCounters; i++) {
    x_uint64 stop = (x_uint64)stopTime[i];
    fprintf(tau_sampling_flags()->ebsTrace, "%lld ", stop);
  }
  fprintf(tau_sampling_flags()->ebsTrace, "| ");

  Tau_sampling_outputTraceCallpath(tid);
  fprintf(tau_sampling_flags()->ebsTrace, "\n");
}

/*********************************************************************
 * Write Maps file for EBS Traces
 ********************************************************************/
int Tau_sampling_write_maps(int tid, int restart)
{
  const char *profiledir = TauEnv_get_profiledir();

  int node = RtsLayer::myNode();
  node = 0;
  char filename[4096];
  sprintf(filename, "%s/ebstrace.map.%d.%d.%d.%d", profiledir, RtsLayer::getPid(), node, RtsLayer::myContext(), tid);

  FILE *output = fopen(filename, "a");

  FILE *mapsfile = fopen("/proc/self/maps", "r");
  if (mapsfile == NULL) {
    return -1;
  }

  char line[4096];
  while (!feof(mapsfile)) {
    fgets(line, 4096, mapsfile);
    unsigned long start, end, offset;
    char module[4096];
    char perms[5];
    module[0] = 0;

    sscanf(line, "%lx-%lx %s %lx %*s %*u %[^\n]", &start, &end, perms, &offset, module);

    if (*module && ((strcmp(perms, "r-xp") == 0) || (strcmp(perms, "rwxp") == 0))) {
      fprintf(output, "%s %p %p %lu\n", module, (void*)start, (void*)end, offset);
    }
  }
  fclose(output);

  return 0;
}

void Tau_sampling_outputTraceDefinitions(int tid)
{
  const char *profiledir = TauEnv_get_profiledir();
  char filename[4096];
  int node = RtsLayer::myNode();
  node = 0;
  sprintf(filename, "%s/ebstrace.def.%d.%d.%d.%d", profiledir, RtsLayer::getPid(), node, RtsLayer::myContext(), tid);

  FILE *def = fopen(filename, "w");

  fprintf(def, "# Format:\n");
  fprintf(def, "# <id> | <name>\n");

  for (vector<FunctionInfo *>::iterator it = TheFunctionDB().begin(); it != TheFunctionDB().end(); it++) {
    FunctionInfo *fi = *it;
    if (strlen(fi->GetType()) > 0) {
      fprintf(def, "%lld | %s %s\n", fi->GetId(), fi->GetName(), fi->GetType());
    } else {
      fprintf(def, "%lld | %s\n", fi->GetId(), fi->GetName());
    }
  }
  fclose(def);

  /* write out the executable name at the end */
  char buffer[4096];
  memset(buffer, 0, 4096);
  int rc = readlink("/proc/self/exe", buffer, 4096);
  if (rc == -1) {
    fprintf(stderr, "TAU Sampling: Error, unable to read /proc/self/exe\n");
  } else {
    buffer[rc] = 0;
    fprintf(tau_sampling_flags()->ebsTrace, "# exe: %s\n", buffer);
  }

  /* write out the node number */
  fprintf(tau_sampling_flags()->ebsTrace, "# node: %d\n", RtsLayer::myNode());
  fprintf(tau_sampling_flags()->ebsTrace, "# thread: %d\n", tid);

  fclose(tau_sampling_flags()->ebsTrace);

#if (defined (TAU_BGP) || (TAU_BGQ))
  /* do nothing */
#else
  Tau_sampling_write_maps(tid, 0);
#endif /* TAU_BGP || TAU_BGQ */

}

void Tau_sampling_handle_sampleTrace(void *pc, ucontext_t *context, int tid)
{

#ifdef TAU_USE_HPCTOOLKIT
  // *CWL* - special case for HPCToolkit because it relies on
  //         the runtime, or unwinding does not happen.
  if (hpctoolkit_process_started == 0) {
    printf("nope, quitting\n");
    return;
  }
#endif /* TAU_USE_HPCTOOLKIT */

  TauSamplingRecord theRecord;
  Profiler *profiler = TauInternal_CurrentProfiler(tid);

  struct timeval tp;
  gettimeofday(&tp, 0);
  x_uint64 timestamp = ((x_uint64)tp.tv_sec * (x_uint64)1e6 + (x_uint64)tp.tv_usec);

  theRecord.timestamp = timestamp;
  theRecord.pc = (unsigned long)pc;
  theRecord.deltaStart = 0;
  theRecord.deltaStop = 0;

  double startTime = profiler->StartTime[0]; // gtod must be counter 0
  theRecord.deltaStart = (x_uint64)startTime;
  theRecord.deltaStop = 0;

  double values[TAU_MAX_COUNTERS];
  TauMetrics_getMetrics(tid, values);
  for (int i = 0; i < Tau_Global_numCounters; i++) {
    theRecord.counters[i] = values[i];
    startTime = profiler->StartTime[i];
    theRecord.counterDeltaStart[i] = (x_uint64)startTime;
    theRecord.counterDeltaStop[i] = 0;
  }

  Tau_sampling_flushTraceRecord(tid, &theRecord, pc, context);

  /* set this to get the stop event */
  profiler->needToRecordStop = 1;

  /* if we are doing EBS sampling, set whether we want inclusive samples */
  /* that is, main->foo->mpi_XXX is a sample for main, foo and mpi_xxx */
  if (TauEnv_get_ebs_inclusive() > 0) {
    profiler = (Profiler *)Tau_query_parent_event(profiler);
    while (profiler != NULL) {
      profiler->needToRecordStop = 1;
      profiler = (Profiler *)Tau_query_parent_event(profiler);
    }
  }
}

/*********************************************************************
 * EBS Profiling Functions
 ********************************************************************/

void Tau_sampling_internal_initName2FuncInfoMapIfNecessary()
{
  static bool name2FuncInfoMapInitialized = false;
  if (!name2FuncInfoMapInitialized) {
    RtsLayer::LockEnv();
    for (int i = 0; i < TAU_MAX_THREADS; i++) {
      //name2FuncInfoMap[i] = NULL;
      name2FuncInfoMap[i] = new map<string, FunctionInfo *>();
    }
    name2FuncInfoMapInitialized = true;
    RtsLayer::UnLockEnv();
  }
}

char *Tau_sampling_getShortSampleName(const char *sampleName)
{
  return NULL;
}

extern "C" CallSiteInfo * Tau_sampling_resolveCallSite(unsigned long addr, char const * tag, char const * childName,
    char ** newShortName, bool addAddress)
{
  int printMessage = 0;
  if (strcmp(tag, "UNWIND") == 0) {
    // if we are dealing with callsites, adjust for the fact that the
    //   return address is the next instruction.
    addr -= 1;
  }
  CallSiteInfo * callsite = new CallSiteInfo(addr);

  CallSiteCacheMap & callSiteCache = TheCallSiteCache();
  // does the node exist in the cache? if not, look it up
  CallSiteCacheNode * node = callSiteCache[addr];
  if (!node) {
    RtsLayer::LockDB();
    node = callSiteCache[addr];
    if (!node) {
      node = new CallSiteCacheNode;
      node->resolved = Tau_bfd_resolveBfdInfo(TheBfdUnitHandle(), addr, node->info);
      callSiteCache[addr] = node;
    }
    RtsLayer::UnLockDB();
    printMessage = 1;
  }

  char buff[4096];

  char *newName = NULL;

  // if the node was found by BFD, populate the callsite node
  if (node->resolved) {
    TauBfdInfo & resolvedInfo = node->info;
    if (childName) {
      sprintf(buff, "[%s] %s [@] %s [{%s} {%d}]", tag, childName, resolvedInfo.funcname, resolvedInfo.filename,
          resolvedInfo.lineno);
    } else {
      sprintf(buff, "[%s] %s [{%s} {%d}]", tag, resolvedInfo.funcname, resolvedInfo.filename, resolvedInfo.lineno);
    }
    // TODO: Leak?
    char lineno[32];
    sprintf(lineno, "%d", resolvedInfo.lineno);
//      *newShortName = (char*)malloc(strlen(resolvedInfo.funcname) + strlen(lineno) + 2);
//      sprintf(*newShortName, "%s.%d", resolvedInfo.funcname, resolvedInfo.lineno);
    newName = (char*)malloc(strlen(resolvedInfo.funcname) + strlen(lineno) + 2);
    sprintf(newName, "%s.%d", resolvedInfo.funcname, resolvedInfo.lineno);
    newShortName = &newName;
    //TAU_VERBOSE("resolved function name (newName in TauSampling.cpp) = %s\n", newName);
  } else {
    char const * mapName = "UNKNOWN";
    TauBfdAddrMap const * addressMap = Tau_bfd_getAddressMap(TheBfdUnitHandle(), addr);
    if (addressMap) {
      mapName = addressMap->name;
    }
    if (addAddress) {
      char * tempAddrBuffer = (char*)malloc(32); // not expecting more than 26 digits in addr
      if (childName) {
        sprintf(buff, "[%s] [%s] [@] UNRESOLVED %s ADDR %p", tag, childName, mapName, (void *)addr);
      } else {
        sprintf(buff, "[%s] UNRESOLVED %s ADDR %p", tag, mapName, (void *)addr);
      }
      sprintf(tempAddrBuffer, "ADDR %p", (void *)addr);
      // TODO: Leak?
      *newShortName = tempAddrBuffer;
    } else {
      if (childName) {
        sprintf(buff, "[%s] [%s] [@] UNRESOLVED %s", tag, childName, mapName);
      } else {
        if (TauEnv_get_bfd_lookup()) {
          sprintf(buff, "[%s] UNRESOLVED %s", tag, mapName);
        } else {
          sprintf(buff, "[%s] UNRESOLVED %s ADDR %p", tag, mapName, (void*)addr);
        }
      }
      // TODO: Leak?
      *newShortName = strdup("UNRESOLVED");
    }
  }

  // TODO: Leak?
  callsite->name = strdup(buff);
  // only print this for new addresses
  if (printMessage == 1) TAU_VERBOSE("Name %s, Address %p resolved to %s\n", *newShortName, (void*)addr, buff);
  return callsite;
}

string *Tau_sampling_getPathName(unsigned int index, CallStackInfo *callStack)
{
  string *ret;
  vector<CallSiteInfo*> & sites = callStack->callSites;
  int startIdx;

  if (sites.size() <= 0) {
    fprintf(stderr, "ERROR: EBS attempted to access 0 length callstack\n");
    exit(-1);
  }
  if (index >= sites.size()) {
    fprintf(stderr, "ERROR: EBS attempted to access index %d of vector of length %ld\n", index, sites.size());
    exit(-1);
  }

  startIdx = (int)(sites.size()) - 1;
  stringstream buffer;
  buffer << (sites[startIdx])->name;
  // do some stupid conversions thanks to unsigned and signed behavior
  if (startIdx > 0) {
    int limit = (int)index;
    for (int i = startIdx - 1; i >= limit; i--) {
      buffer << " => ";
      buffer << (sites[i])->name;
    }
  }
  // copy the string so it doesn't go out of scope
  ret = new string(buffer.str());
  return ret;
}

CallStackInfo * Tau_sampling_resolveCallSites(const unsigned long * addresses)
{
  CallStackInfo * callStack = NULL;

  if (addresses) {
    int length = addresses[0];
    if (length > 0) {
      callStack = new CallStackInfo;
      bool addAddress = (TauEnv_get_ebs_keep_unresolved_addr() == 1);

      char * prevShortName = NULL;
      char * newShortName = NULL;
      callStack->callSites.push_back(
          Tau_sampling_resolveCallSite(addresses[1], "SAMPLE", NULL, &newShortName, addAddress));
      // move the pointers
      if (newShortName) {
        prevShortName = newShortName;
        newShortName = NULL;
      }
      for (int i = 2; i < length; ++i) {
        unsigned long address = addresses[i];
        callStack->callSites.push_back(
            Tau_sampling_resolveCallSite(address, "UNWIND", prevShortName, &newShortName, addAddress));
        // free the previous short name now.
        if (prevShortName) {
          free(prevShortName);
          prevShortName = NULL;
          if (newShortName) {
            prevShortName = newShortName;
          }
        }
        // move the pointers
        if (newShortName) {
          prevShortName = newShortName;
          newShortName = NULL;
        }
      }
      if (newShortName) {
        free(newShortName);
      }
      if (prevShortName) {
        free(prevShortName);
      }
    }
  }
  return callStack;
}

void Tau_sampling_eventStopProfile(int tid, Profiler *profiler, double *stopTime)
{
  // No activity required for Sampling Profiling at event stop for now.
}

char *Tau_sampling_internal_stripCallPath(const char *callpath)
{
  char *pointer = NULL;
  char *temp = (char *)callpath;
  do {
    pointer = temp;
    temp = strstr(pointer, "=>");
    if (temp != NULL) {
      temp += 2; // strip off the "=>"
      if (temp == NULL) {
        // takes care of case where string terminates with "=>"
        pointer = NULL;
      }
    }
  } while (temp != NULL);

  return strdup(pointer);
}

void Tau_sampling_finalizeProfile(int tid)
{
  TAU_VERBOSE("TAU: Finalizing sampling profiles on thread %d\n", tid);

  // Resolve all unresolved PC values.
  //
  // For resolution, each PC resolves to a unique CallSite tuple:
  //     filename X funcname X lineno
  // Each CallSite tuple maps to its own FunctionInfo object
  //

  // NOTE: This code ought to be at the start of a dlopen trap as well
  //       to take care of epoch changes.

  // Iterate through all known FunctionInfo to acquire candidate callsites
  // for resolution.
  TAU_VERBOSE("TAU: Preparing callsite candidates\n");
  vector<CallSiteCandidate*> candidates;

  RtsLayer::LockDB();
  // *CWL* NOTE: Cannot create intermediate FunctionInfo objects while
  //       we iterate TheFunctionDB()! Hence the candidates!
  for (vector<FunctionInfo*>::iterator fI_iter = TheFunctionDB().begin(); fI_iter != TheFunctionDB().end(); fI_iter++) {
    FunctionInfo * parentTauContext = *fI_iter;
    if (parentTauContext->GetPathHistogram(tid).size() == 0) {
      // No samples encountered in this TAU context. Continue to next TAU context.
      continue;
    }

    parentTauContext->GetPathHistogram(tid).resetIter();
    pair<unsigned long *, TauPathAccumulator> * item = parentTauContext->GetPathHistogram(tid).nextIter();
    while (item) {
      // This is a placeholder for more generic pcStack extraction routines.
      CallSiteCandidate * candidate = new CallSiteCandidate(item->first, item->second.count, parentTauContext);
//      DEBUGMSG("Tau Context %s has %d samples", candidate->tauContext->GetName(), candidate->sampleCount);
      for (int i = 0; i < Tau_Global_numCounters; i++) {
        candidate->counters[i] = item->second.accumulator[i];
      }
      candidates.push_back(candidate);
      delete item;
      item = parentTauContext->GetPathHistogram(tid).nextIter();
    }
  }
  RtsLayer::UnLockDB();

  // Initialization of maps for this thread if necessary.
  Tau_sampling_internal_initName2FuncInfoMapIfNecessary();
  if (name2FuncInfoMap[tid] == NULL) {
    name2FuncInfoMap[tid] = new map<string, FunctionInfo *>();
  }

  // For each encountered sample PC in the non-empty TAU context,
  //
  //    resolve to the unique sample name as follows:
  //       <TAU Callpath Name> => <CallStack Path>
  //
  //    where <CallStack Path> is <CallSite> (=> <CallSite>)* and
  //       <CallSite> is:
  //       SAMPLE|UNWIND <funcname> [{filename} {lineno:colno}-{lineno:colno}]
  //
  //    note that <CallStack Path> is the generalization of a sample
  //       whether or not stack unwinding is invoked.
  //
  TAU_VERBOSE("TAU: Translating symbols to source code locations on thread %d\n", tid);
  vector<CallSiteCandidate *>::iterator cs_it;
  for (cs_it = candidates.begin(); cs_it != candidates.end(); cs_it++) {
    CallSiteCandidate * candidate = *cs_it;

    // STEP 0: Set up the metric values based on the candidate
    //         to eventually be assigned to various FunctionInfo
    //         entities.
    //double metricValue;

    // Determine the EBS_SOURCE metric index and update the appropriate
    //   sample approximations.
    int ebsSourceMetricIndex = TauMetrics_getMetricIndexFromName(TauEnv_get_ebs_source());
    if (ebsSourceMetricIndex == -1) {
      // *CWL* - Force it to be 0 and hope for the best.
      ebsSourceMetricIndex = 0;
    }
    unsigned int binFreq = candidate->sampleCount;
    //metricValue = binFreq*TauEnv_get_ebs_period();
    //metricValue = candidate->counters[0];

    // STEP 1: Resolve all addresses in a PC Stack.
    CallStackInfo * callStack = Tau_sampling_resolveCallSites(candidate->pcStack);

    // Name-to-function map iterator. To be shared for intermediate and callsite
    //   scenarios.
    map<string, FunctionInfo *>::iterator fi_it;

    // STEP 2: Find out if the Intermediate node for this candidate
    //         has been created. Intermediate nodes need to be handled
    //         in a persistent mode across candidates.
    FunctionInfo *intermediateGlobalLeaf = NULL;
    FunctionInfo *intermediatePathLeaf = NULL;
    stringstream intermediateGlobalLeafString;
    stringstream intermediatePathLeafString;

    // STEP 2a: Locate or create Leaf Entry - the CONTEXT node
    intermediateGlobalLeafString << "[CONTEXT] ";
    bool needToUpdateContext = false;
    if (strncmp(candidate->tauContext->GetName(), "OMP_", 4) == 0) {
      needToUpdateContext = true;
    }
    char * tmpStr = Tau_sampling_internal_stripCallPath(candidate->tauContext->GetName());
    intermediateGlobalLeafString << tmpStr;
    free(tmpStr);
    const string& iglstring = intermediateGlobalLeafString.str();
    fi_it = name2FuncInfoMap[tid]->find(iglstring);
    if (fi_it == name2FuncInfoMap[tid]->end()) {
      // Create the FunctionInfo object for the leaf Intermediate object.
      RtsLayer::LockDB();
      intermediateGlobalLeaf = new FunctionInfo(iglstring, candidate->tauContext->GetType(),
          candidate->tauContext->GetProfileGroup(), "TAU_SAMPLE_CONTEXT", true);
      RtsLayer::UnLockDB();
      name2FuncInfoMap[tid]->insert(std::pair<string, FunctionInfo*>(iglstring, intermediateGlobalLeaf));
    } else {
      intermediateGlobalLeaf = (FunctionInfo *)fi_it->second;
    }

    // Step 2b: Locate or create Full Path Entry. Requires name
    //   information about the Leaf Entry available.
    //   This is the TIMER => SAMPLES entry.
    intermediatePathLeafString << candidate->tauContext->GetName() << " ";
    intermediatePathLeafString << candidate->tauContext->GetType() << " => ";
    intermediatePathLeafString << iglstring;
    const string& iplstring = intermediatePathLeafString.str();
    fi_it = name2FuncInfoMap[tid]->find(iplstring);
    if (fi_it == name2FuncInfoMap[tid]->end()) {
      // Create the FunctionInfo object for the leaf Intermediate object.
      RtsLayer::LockDB();
      intermediatePathLeaf = new FunctionInfo(iplstring, candidate->tauContext->GetType(),
          candidate->tauContext->GetProfileGroup(), "TAU_SAMPLE_CONTEXT|TAU_CALLPATH", true);
      RtsLayer::UnLockDB();
      name2FuncInfoMap[tid]->insert(std::pair<string, FunctionInfo*>(iplstring, intermediatePathLeaf));
    } else {
      intermediatePathLeaf = (FunctionInfo *)fi_it->second;
    }
    // Accumulate the histogram into the Intermediate FunctionInfo objects.
    intermediatePathLeaf->SetNumCalls(tid, intermediatePathLeaf->GetNumCalls(tid) + binFreq);
    intermediateGlobalLeaf->SetNumCalls(tid, intermediateGlobalLeaf->GetNumCalls(tid) + binFreq);
    if (needToUpdateContext) {
      candidate->tauContext->SetNumCalls(tid, intermediateGlobalLeaf->GetNumCalls(tid) + binFreq);
    }
    for (int m = 0; m < Tau_Global_numCounters; m++) {
      intermediatePathLeaf->AddInclTime(candidate->counters[m], tid, m);
      intermediateGlobalLeaf->AddInclTime(candidate->counters[m], tid, m);
      if (needToUpdateContext) {
        candidate->tauContext->AddInclTime(candidate->counters[m], tid, m);
        candidate->tauContext->AddExclTime(candidate->counters[m], tid, m);
      }
    }

    // STEP 3: For each sample, construct all FunctionInfo objects
    //    associated with the unwound addresses and the PC.
    //
    // Intermediate FunctionInfo objects must be found or created
    //    at this time.
    //
    // For Each Address
    //   1. Check and Create Leaf Entry
    //   2. Check and Create Path Entry (Requires Intermediate)
    vector<CallSiteInfo *> & sites = callStack->callSites;
    // *CWL* - we need the index, which is why the iterator is not used.
    for (unsigned int i = 0; i < sites.size(); i++) {
      string * samplePathLeafString = Tau_sampling_getPathName(i, callStack);
      const string& sampleGlobalLeafString = sites[i]->name;
      FunctionInfo * samplePathLeaf = NULL;
      FunctionInfo * sampleGlobalLeaf = NULL;

      fi_it = name2FuncInfoMap[tid]->find(sampleGlobalLeafString);
      if (fi_it == name2FuncInfoMap[tid]->end()) {
        char const * sampleGroup = "TAU_UNWIND";
        if (sampleGlobalLeafString.find("UNWIND") == string::npos) {
          sampleGroup = "TAU_SAMPLE";
        }
        RtsLayer::LockDB();
        sampleGlobalLeaf = new FunctionInfo(sampleGlobalLeafString, candidate->tauContext->GetType(),
            candidate->tauContext->GetProfileGroup(), sampleGroup, true);
        RtsLayer::UnLockDB();
        name2FuncInfoMap[tid]->insert(std::pair<string, FunctionInfo*>(sampleGlobalLeafString, sampleGlobalLeaf));
      } else {
        sampleGlobalLeaf = (FunctionInfo*)fi_it->second;
      }

      stringstream callSiteKeyName;
      callSiteKeyName << iplstring << " ";
      callSiteKeyName << candidate->tauContext->GetType() << " => ";
      callSiteKeyName << samplePathLeafString;
      const string cskname(callSiteKeyName.str());
      delete samplePathLeafString;
      // try to find the key
      fi_it = name2FuncInfoMap[tid]->find(cskname);
      if (fi_it == name2FuncInfoMap[tid]->end()) {
        char const * sampleGroup = "TAU_UNWIND|TAU_CALLPATH";
        if (cskname.find("UNWIND") == string::npos) {
          sampleGroup = "TAU_SAMPLE|TAU_CALLPATH";
        }
        RtsLayer::LockDB();
        samplePathLeaf = new FunctionInfo(cskname, "", candidate->tauContext->GetProfileGroup(), sampleGroup, true);
        RtsLayer::UnLockDB();
        //name2FuncInfoMap[tid]->insert(std::pair<string, FunctionInfo*>(callSiteKeyName->c_str(), samplePathLeaf));
        name2FuncInfoMap[tid]->insert(std::pair<string, FunctionInfo*>(cskname, samplePathLeaf));
      } else {
        samplePathLeaf = (FunctionInfo*)fi_it->second;
      }

      // Update the count and time for the end of the path for sampled event.
      samplePathLeaf->SetNumCalls(tid, samplePathLeaf->GetNumCalls(tid) + binFreq);
      sampleGlobalLeaf->SetNumCalls(tid, sampleGlobalLeaf->GetNumCalls(tid) + binFreq);

      for (int m = 0; m < Tau_Global_numCounters; m++) {
        samplePathLeaf->AddInclTime(candidate->counters[m], tid, m);
        // Exclusive times are only incremented for actual sample data
        //   and not unwound data
        if (i == 0) {
          samplePathLeaf->AddExclTime(candidate->counters[m], tid, m);
        }
        // Accumulate the count and time into the global leaf representative sampled event.
        sampleGlobalLeaf->AddInclTime(candidate->counters[m], tid, m);
        if (i == 0) {
          sampleGlobalLeaf->AddExclTime(candidate->counters[m], tid, m);
        }
      }
    }
    while (!callStack->callSites.empty()) {
      CallSiteInfo * tmp = callStack->callSites.back();
      callStack->callSites.pop_back();
      free(tmp->name);
      delete tmp;
    }
    delete callStack;
  }

  // Write out Metadata.
  //
  // *CWL* - overload node numbers (not scalable in ParaProf display) in
  //         preparation for a more scalable way of displaying per-node
  //         metadata information.
  //
  char tmpstr[512];
  char tmpname[512];
  sprintf(tmpname, "TAU_EBS_SAMPLES_TAKEN_%d", tid);
  sprintf(tmpstr, "%lld", tau_sampling_flags()->numSamples);
  TAU_METADATA(tmpname, tmpstr);

  sprintf(tmpname, "TAU_EBS_SAMPLES_DROPPED_TAU_%d", tid);
  sprintf(tmpstr, "%lld", tau_sampling_flags()->samplesDroppedTau);
  TAU_METADATA(tmpname, tmpstr);

  sprintf(tmpname, "TAU_EBS_SAMPLES_DROPPED_SUSPENDED_%d", tid);
  sprintf(tmpstr, "%lld", tau_sampling_flags()->samplesDroppedSuspended);
  TAU_METADATA(tmpname, tmpstr);

  while (!candidates.empty()) {
    CallSiteCandidate * tmp = candidates.back();
    candidates.pop_back();
    delete tmp;
  }
}

void Tau_sampling_handle_sampleProfile(void *pc, ucontext_t *context, int tid)
{

  Profiler * profiler = TauInternal_CurrentProfiler(tid);
  if (profiler == NULL) {
    Tau_create_top_level_timer_if_necessary_task(tid);
    profiler = TauInternal_CurrentProfiler(tid);
    if (profiler == NULL) {
      if (TauEnv_get_ebs_enabled_tau()) {
        // if we are sampling to measure TAU, the profile might not be done yet
        return;
      } else {
        printf("STILL no top level timer on thread %d!\n", tid);
        fflush(stdout);
        exit(999);
      }
    }
  }

  // ok to be temporary. Hash table on the other end will copy the details.
  unsigned long pcStack[TAU_SAMP_NUM_ADDRESSES + 1] = { 0 };

#ifdef TAU_UNWIND
  if (TauEnv_get_ebs_unwind() == 1) {
    Tau_sampling_unwind(tid, profiler, pc, context, pcStack);
  } else {
    pcStack[0] = 1;
    pcStack[1] = (unsigned long)pc;
  }
#else
  pcStack[0] = 1;
  pcStack[1] = (unsigned long)pc;
#endif /* TAU_UNWIND */

  FunctionInfo * samplingContext;
  if (TauEnv_get_callsite() && (profiler->CallSiteFunction != NULL)) {
    samplingContext = profiler->CallSiteFunction;
  } else if (TauEnv_get_callpath() && (profiler->CallPathFunction != NULL)) {
    samplingContext = profiler->CallPathFunction;
  } else {
    samplingContext = profiler->ThisFunction;
  }

  TAU_ASSERT(samplingContext != NULL, "samplingContext == NULL!");

  /* Get the current metric values */
  double values[TAU_MAX_COUNTERS] = { 0.0 };
  double deltaValues[TAU_MAX_COUNTERS] = { 0.0 };
  TauMetrics_getMetrics(tid, values);
  //printf("tid = %d, values[0] = %f\n", tid, values[0]); fflush(stdout);

  int ebsSourceMetricIndex = TauMetrics_getMetricIndexFromName(TauEnv_get_ebs_source());
  int ebsPeriod = TauEnv_get_ebs_period();
  //printf("tid = %d, period = %d\n", tid, ebsPeriod); fflush(stdout);
  for (int i = 0; i < Tau_Global_numCounters; i++) {
    //printf("tid = %d, sampling previousTimestamp = %llu, period = %d\n", tid, tau_sampling_flags()->previousTimestamp[i], ebsPeriod); fflush(stdout);
    /*
     if (tau_sampling_flags()->previousTimestamp[i] == 0) {
     // "We don't believe you!". Should only happen for non EBS_SOURCE
     // metrics. Hypothesis - the first sample would find the
     // previousTimestamp for events unset.
     tau_sampling_flags()->previousTimestamp[i] == profiler->StartTime[i];
     }
     */
    if ((ebsSourceMetricIndex == i) && (values[i] < ebsPeriod)) {
      // "We don't believe you either!". Should only happen for EBS_SOURCE.
      // Hypothesis: Triggering PAPI overflows resets the values to 0.
      //             (or close to 0).
      deltaValues[i] = ebsPeriod;
      tau_sampling_flags()->previousTimestamp[i] += ebsPeriod;
    } else {
      deltaValues[i] = values[i] - tau_sampling_flags()->previousTimestamp[i];
      /*
       printf("[%s] tid=%d ctr=%d, Delta computed as %f minus %lld = %f\n",
       samplingContext->GetName(),
       tid, i,
       values[i], tau_sampling_flags()->previousTimestamp[i], deltaValues[i]);
       */
      tau_sampling_flags()->previousTimestamp[i] = values[i];
    }
    //printf("tid = %d, sampling previousTimestamp = %llu, period = %d\n", tid, tau_sampling_flags()->previousTimestamp[i], ebsPeriod); fflush(stdout);
  }
  //printf("tid = %d, Delta = %f, period = %d\n", tid, deltaValues[0], ebsPeriod); fflush(stdout);
#ifdef TAU_OPENMP
  if (TauEnv_get_openmp_runtime_states_enabled() == 1) {
    // get the thread state, too!
#if defined(TAU_USE_OMPT) || defined(TAU_IBM_OMPT)
    // OMPT returns a character array
    std::string* state_name = Tau_get_thread_ompt_state(tid);
    if (state_name != NULL) {
      // FYI, this won't actually create the state. Because that wouldn't be signal-safe.
      // Instead, it will look it up and return the ones we created during
      // the OpenMP Collector API initialization.
      FunctionInfo *stateContext = Tau_create_thread_state_if_necessary_string(*state_name);
      stateContext->addPcSample(pcStack, tid, deltaValues);
    }
#else
    // ORA returns an integer, which has to be mapped to a std::string
    int thread_state = Tau_get_thread_omp_state(tid);
    if (thread_state >= 0) {
      // FYI, this won't actually create the state. Because that wouldn't be signal-safe.
      // Instead, it will look it up and return the ones we created during
      // the OpenMP Collector API initialization.
      FunctionInfo *stateContext = Tau_create_thread_state_if_necessary_string(gTauOmpStates(thread_state));
      stateContext->addPcSample(pcStack, tid, deltaValues);
    }
#endif
  } else {
    samplingContext->addPcSample(pcStack, tid, deltaValues);
  }
#else
  // also do the regular context!
  samplingContext->addPcSample(pcStack, tid, deltaValues);
#endif
}

/*********************************************************************
 * Event triggers
 ********************************************************************/

/* Various unwinders might have their own implementation */
void Tau_sampling_event_start(int tid, void **addresses)
{
  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  // This is undefined when no unwind capability has been linked into TAU
#ifdef TAU_UNWIND
  if (TauEnv_get_ebs_unwind() == 1) {
    Tau_sampling_unwindTauContext(tid, addresses);
  }
#endif /* TAU_UNWIND */

  /* Kevin here. This code is a bad idea. I have disabled it for now.
   * Sampling and instrumentation can play together just fine, if a
   * timer starts / stops, it shouldn't affect the timers for sampling.
   * And SHOULDN'T affect the timers for sampling.
   */
#if 0
  if (TauEnv_get_profiling()) {
    // *CWL* - 8/18/2012. The new way of measuring a sample's contribution
    //         (in light of the uneven distribution of samples in threads)
    //         necessitates the use of a measured event's time stamp to
    //         serve as a bounding value for subsequent deductions.
    //
    //         Note that this is still a fudge. In the face of limited
    //         measured events, this can end up accounting metric
    //         contributions to samples that can sometimes seem bizarre.
    //         (e.g., Source=PAPI_TOT_CYC, Metric=PAPI_FP_OPS can result
    //         in strange attribution of values to samples depending on
    //         the interplay of high FLOPS/s events and low FLOPS/s
    //         events).
    //
    //         Without handling the event boundaries, another observed
    //         (bad) effect is in cases where PAPI_FP_OPS is used as
    //         TAU_EBS_SOURCE. A good chunk of the events leading up
    //         to a reasonable period of say 1,000,000 FP_OPS as a
    //         sample are likely to do very little FP_OPS. However,
    //         at the first sample, the deltas computed for the sample's
    //         TIME metric are likely to stretch all the way back to
    //         main() if event boundary limits are not established.
    //
    //         Statistical sampling, being what it is, can never avoid
    //         this fudging. The previous approach of counting had the
    //         advantage of limiting the fudge factor to some factor of
    //         TAU_EBS_PERIOD.

    double values[TAU_MAX_COUNTERS] = {0.0};
    TauMetrics_getMetrics(tid, values);
    for (int i = 0; i < Tau_Global_numCounters; i++) {
      tau_sampling_flags()->previousTimestamp[i] = values[i];
      printf("tid = %d, event previousTimestamp = %llu\n", tid, tau_sampling_flags()->previousTimestamp[i]); fflush(stdout);
    }

  }
#endif
}

int Tau_sampling_event_stop(int tid, double *stopTime)
{
#ifndef TAU_EXP_DISABLE_DELTAS
  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  tau_sampling_flags()->samplingEnabled = 0;

  Profiler *profiler = TauInternal_CurrentProfiler(tid);

  if (TauEnv_get_tracing()) {
    if (!profiler->needToRecordStop) {
      tau_sampling_flags()->samplingEnabled = 1;
      return 0;
    }
    Tau_sampling_outputTraceStop(tid, profiler, stopTime);
  }

  if (TauEnv_get_profiling()) {
    Tau_sampling_eventStopProfile(tid, profiler, stopTime);
  }

  tau_sampling_flags()->samplingEnabled = 1;
#endif
  return 0;
}

/*********************************************************************
 * Sample Handling
 ********************************************************************/
void Tau_sampling_handle_sample(void *pc, ucontext_t *context)
{
  if (collectingSamples) {
    int tid = Tau_get_local_tid();
    //printf("%d SAMPLE: %p\n", tid, pc);
    if (tau_sampling_flags()->samplingEnabled) {
      tau_sampling_flags()->numSamples++;

      // Exclude TAU from sampling
      if ((Tau_global_get_insideTAU() > 0) && (!TauEnv_get_ebs_enabled_tau())) {
        tau_sampling_flags()->samplesDroppedTau++;
        return;
      }

      if (tau_sampling_flags()->suspendSampling) {
        tau_sampling_flags()->samplesDroppedSuspended++;
        return;
      }

      // disable sampling until we handle this sample
      {
        TauInternalFunctionGuard protects_this_region;
        tau_sampling_flags()->suspendSampling = 1;
        if (TauEnv_get_tracing()) {
          Tau_sampling_handle_sampleTrace(pc, context, tid);
        }

        if (TauEnv_get_profiling()) {
          Tau_sampling_handle_sampleProfile(pc, context, tid);
        }
        tau_sampling_flags()->suspendSampling = 0;
      } // insideTAU
    } // samplingEnabled
  } // collectingSamples
}

extern "C" void TauMetrics_internal_alwaysSafeToGetMetrics(int tid, double values[]);

/*********************************************************************
 * Handler for itimer interrupt
 ********************************************************************/
void Tau_sampling_handler(int signum, siginfo_t *si, void *context)
{
  unsigned long pc;
  pc = get_pc(context);

#ifdef DEBUG_PROF
  double values[TAU_MAX_COUNTERS];
  TauMetrics_internal_alwaysSafeToGetMetrics(0, values);
#endif // DEBUG_PROF
  Tau_sampling_handle_sample((void *)pc, (ucontext_t *)context);

  // now, apply the application's action.
  if (application_sa.sa_handler == SIG_IGN || application_sa.sa_handler == SIG_DFL) {
    // if there is no handler, or the action is ignore
    // do nothing, because we are only handling SIGPROF
    // and if we do the "default", that would lead to termination.
    //return;
  } else {
    // Invoke the application's handler.
    if (application_sa.sa_flags & SA_SIGINFO) {
      (*application_sa.sa_sigaction)(signum, si, context);
    } else {
      (*application_sa.sa_handler)(signum);
    }
  }
#ifdef DEBUG_PROF
  double values2[TAU_MAX_COUNTERS];
  TauMetrics_internal_alwaysSafeToGetMetrics(0, values2);
  TAU_VERBOSE("Sampling took %f usec\n", values2[0] - values[0]);
#endif // DEBUG_PROF
}

/*********************************************************************
 * PAPI Overflow handler
 ********************************************************************/
void Tau_sampling_papi_overflow_handler(int EventSet, void *address, x_int64 overflow_vector, void *context)
{
  /*
   int tid = RtsLayer::localThreadId();
   fprintf(stderr,"[%d] Overflow at %p! bit=0x%llx \n", tid, address,overflow_vector);
   */

  x_int64 value = (x_int64)address;

  if ((value & 0xffffffffff000000ll) == 0xffffffffff000000ll) {
    return;
  }

  Tau_sampling_handle_sample(address, (ucontext_t *)context);
}

/*********************************************************************
 * Initialize the sampling trace system
 ********************************************************************/
int Tau_sampling_init(int tid)
{
  int ret;

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  int threshold = TauEnv_get_ebs_period();

#if defined(TAU_USE_PGS)
  if (tid == 0)
  pthread_key_create (&tau_sampling_tls_key, NULL);
  struct tau_sampling_flags *tau_sampling_tls_flags = (struct tau_sampling_flags*)malloc(sizeof(struct tau_sampling_flags));
  tau_sampling_tls_flags->samplingEnabled = 0;
  tau_sampling_tls_flags->suspendSampling = 0;
  tau_sampling_tls_flags->numSamples = 0;
  tau_sampling_tls_flags->samplesDroppedTau = 0;
  tau_sampling_tls_flags->samplesDroppedSuspended = 0;
  tau_sampling_tls_flags->ebsTrace = NULL;
  pthread_setspecific(tau_sampling_tls_key, tau_sampling_tls_flags);
#else
  tau_sampling_flags()->samplingEnabled = 0;
  tau_sampling_flags()->suspendSampling = 0;
  tau_sampling_flags()->numSamples = 0;
  tau_sampling_flags()->samplesDroppedTau = 0;
  tau_sampling_flags()->samplesDroppedSuspended = 0;
  tau_sampling_flags()->ebsTrace = NULL;
#endif

  const char *profiledir = TauEnv_get_profiledir();

  int node = RtsLayer::myNode();
  char filename[4096];

  if (TauEnv_get_tracing()) {
    sprintf(filename, "%s/ebstrace.raw.%d.%d.%d.%d", profiledir, RtsLayer::getPid(), node, RtsLayer::myContext(), tid);

    tau_sampling_flags()->ebsTrace = fopen(filename, "w");
    if (tau_sampling_flags()->ebsTrace == NULL) {
      fprintf(stderr, "Tau Sampling Error: Unable to open %s for writing\n", filename);
      exit(-1);
    }

    Tau_sampling_outputTraceHeader(tid);
  }

  // Nothing currently requires initialization work for sampling into
  //   profiles.
  /*
   if (TauEnv_get_profiling()) {
   }
   */

  /*  *CWL* - NOTE: It is fine to establish the timer interrupts here
   (and the PAPI overflow interrupts elsewhere) only because we
   enable sample handling for each thread after init(tid) completes.
   See Tau_sampling_handle_sample().
   */
#ifndef TAU_BGQ
  if (strcmp(TauEnv_get_ebs_source(), "itimer") == 0 || strcmp(TauEnv_get_ebs_source(), "TIME") == 0) {
    // only thread 0 sets up the timer interrupts.
    if (tid == 0) {
#endif // TAU_BGQ
      struct sigaction act;

      // If TIME isn't on the list of TAU_METRICS, then do not sample.
      // Eventually, we could employ a best-effort attempt to add
      //   TAU_EBS_SOURCE to TAU_METRICS if TAU_EBS_SOURCE is not a
      //   a member of TAU_METRICS.
      int checkVal = TauMetrics_getMetricIndexFromName("TIME");
      if (checkVal == -1) {
        // *CWL* - Attempt other default (or pseudo-default) timer options.
        //         This is probably not the best nor most efficient way.
        //         The only saving grace is that these pseudo-default
        //         timers are probably not going to overlap in the same run.
        //
        //         Essentially, we don't
        //         really care what these timers do, if EBS_SOURCE=TIME, we
        //         just want to find ANY time-based metric to latch the
        //         data to.
        const char *temp = NULL;
        checkVal = TauMetrics_getMetricIndexFromName("TAUGPU_TIME");
        if (checkVal != -1) {
          temp = "TAUGPU_TIME";
        }

        checkVal = TauMetrics_getMetricIndexFromName("LINUX_TIMERS");
        if (checkVal != -1) {
          temp = "LINUX_TIMERS";
        }

        checkVal = TauMetrics_getMetricIndexFromName("BGL_TIMERS");
        if (checkVal != -1) {
          temp = "BGL_TIMERS";
        }

        checkVal = TauMetrics_getMetricIndexFromName("BGP_TIMERS");
        if (checkVal != -1) {
          temp = "BGP_TIMERS";
        }

        checkVal = TauMetrics_getMetricIndexFromName("BGQ_TIMERS");
        if (checkVal != -1) {
          temp = "BGQ_TIMERS";
        }

        checkVal = TauMetrics_getMetricIndexFromName("CRAY_TIMERS");
        if (checkVal != -1) {
          temp = "CRAY_TIMERS";
        }

        // If *some* pseudo-default timer is used, then override the EBS_SOURCE string.
        //   The overriden value will eventually be used in the final EBS data resolution
        //   phase to latch the EBS data to the appropriate metric data (which uses the
        //   EBS_SOURCE string to figure out the metric index).
        if (temp) {
          TauEnv_override_ebs_source(temp);
        } else {
          fprintf(stderr, "TAU Sampling Warning: No time-related metric found in TAU_METRICS. "
              "Sampling is disabled for TAU_EBS_SOURCE %s.\n", TauEnv_get_ebs_source());
          return -1;
        }
      }

      memset(&act, 0, sizeof(struct sigaction));
      ret = sigemptyset(&act.sa_mask);
      if (ret != 0) {
        fprintf(stderr, "TAU: Sampling error 1: %s\n", strerror(ret));
        return -1;
      }
      ret = sigaddset(&act.sa_mask, TAU_ALARM_TYPE);
      if (ret != 0) {
        fprintf(stderr, "TAU: Sampling error 2: %s\n", strerror(ret));
        return -1;
      }
      act.sa_sigaction = Tau_sampling_handler;
      act.sa_flags = SA_SIGINFO | SA_RESTART;

      // initialize the application signal action, so we can apply it
      // after we run our signal handler
      struct sigaction query_action;
      ret = sigaction(TAU_ALARM_TYPE, NULL, &query_action);
      if (ret != 0) {
        fprintf(stderr, "TAU: Sampling error 3: %s\n", strerror(ret));
        return -1;
      }
      if (query_action.sa_handler == SIG_DFL || query_action.sa_handler == SIG_IGN) {
        ret = sigaction(TAU_ALARM_TYPE, &act, NULL);
        if (ret != 0) {
          fprintf(stderr, "TAU: Sampling error 4: %s\n", strerror(ret));
          return -1;
        }
        //DEBUGMSG("sigaction called");
        // the old handler was just the default or ignore.
        memset(&application_sa, 0, sizeof(struct sigaction));
        sigemptyset(&application_sa.sa_mask);
        application_sa.sa_handler = query_action.sa_handler;
      } else {
        // FIRST! check if this is us! (i.e. we got initialized twice)
        if (query_action.sa_sigaction == Tau_sampling_handler) {
#ifndef TAU_BGQ // It's ok to have multiple init on BGQ
          TAU_VERBOSE("[%d] WARNING! Tau_sampling_init called twice!\n", tid);
#endif
        } else {
          TAU_VERBOSE("[%d] WARNING! Tau_sampling_init found another handler!\n", tid);
          // install our handler, and save the old handler
          ret = sigaction(TAU_ALARM_TYPE, &act, &application_sa);
          if (ret != 0) {
            fprintf(stderr, "TAU: Sampling error 5: %s\n", strerror(ret));
            return -1;
          }
          //DEBUGMSG("sigaction called");
        }
      }
#ifndef TAU_BGQ
    } // if (tid == 0)
#endif

    /* on Linux systems, we have the option of sampling based on the Wall clock
     * on a per-thread basis.  We don't have this ability everywhere - on those
     * systems, we have to use ITIMER_PROF with setitimer. */
#if defined(SIGEV_THREAD_ID) && !defined(TAU_BGQ) && !defined(TAU_FUJITSU)
    struct sigevent sev;
    memset(&sev, 0, sizeof(sigevent));
    timer_t timerid = 0;
    sev.sigev_signo = TAU_ALARM_TYPE;
    sev.sigev_notify = SIGEV_THREAD_ID;
    sev.sigev_value.sival_ptr = &timerid;
#ifndef TAU_ANDROID
#ifndef TAU_FUJITSU
    sev.sigev_notify_thread_id = syscall(__NR_gettid);
#endif /* TAU_FUJITSU */
#else
    sev.sigev_notify_thread_id = JNIThreadLayer::GetThreadSid();
    TAU_VERBOSE(" *** (S%d) send alarm to %d\n", gettid(), sev.sigev_notify_thread_id);
#endif
    ret = timer_create(CLOCK_REALTIME, &sev, &timerid);
    if (ret != 0) {
      fprintf(stderr, "TAU: (%d, %d) Sampling error 6: %s\n", RtsLayer::myNode(), RtsLayer::myThread(), strerror(ret));
      return -1;
    }
    struct itimerspec it;

    /* this timer is in nanoseconds, but our parameters are in microseconds. */
    /* so don't divide by a billion, divide by a million, then scale to nanoseconds. */
    it.it_interval.tv_nsec = it.it_value.tv_nsec = (threshold % TAU_MILLION) * TAU_THOUSAND;
    it.it_interval.tv_sec = it.it_value.tv_sec = threshold / TAU_MILLION;

    ret = timer_settime(timerid, 0, &it, NULL);
    if (ret != 0) {
      fprintf(stderr, "TAU: Sampling error 7: %s\n", strerror(ret));
      return -1;
    }
    //TAU_VERBOSE("Thread %d (pthread id = %d) called timer_settime...\n", tid, syscall(__NR_gettid));

#else /* use itimer when not on Linux */
    struct itimerval ovalue, pvalue;
    getitimer(TAU_ITIMER_TYPE, &pvalue);

    static struct itimerval itval;
    itval.it_interval.tv_usec = itval.it_value.tv_usec = threshold % TAU_MILLION;
    itval.it_interval.tv_sec = itval.it_value.tv_sec = threshold / TAU_MILLION;
    //DEBUGMSG("threshold=%d, itimer=(%d, %d)", threshold, itval.it_interval.tv_usec, itval.it_interval.tv_sec);

    ret = setitimer(TAU_ITIMER_TYPE, &itval, &ovalue);
    if (ret != 0) {
      fprintf(stderr, "TAU: Sampling error 8: %s\n", strerror(ret));
      return -1;
    }
    //TAU_VERBOSE("Thread %d called setitimer...\n", tid);
    //DEBUGMSG("setitimer called");
#endif //SIGEV_THREAD_ID

#ifndef TAU_BGQ
  } //(TauEnv_get_ebs_source() == "itimer" || "TIME")
#endif

  // set up the base timers
  double values[TAU_MAX_COUNTERS] = { 0 };
  /* Get the current metric values */
  //    TauMetrics_getMetrics(tid, values);
  // *CWL* - sampling_init can happen within the TAU init in the non-MPI case.
  //         So, we invoke a call that insists that TAU Metrics are available
  //         and ready to use. This requires that sampling init happens after
  //         metric init under all possible initialization conditions.
  TauMetrics_internal_alwaysSafeToGetMetrics(tid, values);
  //for (int x = 0; x < TAU_MAX_THREADS; x++) {
  for (int y = 0; y < Tau_Global_numCounters; y++) {
    tau_sampling_flags()->previousTimestamp[y] = values[y];
  }
  //printf("tid = %d, init previousTimestamp = %llu\n", tid, tau_sampling_flags()->previousTimestamp[y]); fflush(stdout);
  //}
  tau_sampling_flags()->samplingEnabled = 1;
  collectingSamples = 1;
  return 0;
}

/*********************************************************************
 * Finalize the sampling trace system
 ********************************************************************/
int Tau_sampling_finalize(int tid)
{
  if (TauEnv_get_tracing() && !tau_sampling_flags()->ebsTrace) return 0;
  TAU_VERBOSE("TAU: <Node=%d.Thread=%d> finalizing sampling for %d...\n", RtsLayer::myNode(), Tau_get_local_tid(), tid);
  fflush(stdout);

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  /* Disable sampling first */
  tau_sampling_flags()->samplingEnabled = 0;
  collectingSamples = 0;

  struct itimerval itval;
  int ret;

  if (tid == 0) {
    // no timers to unset if on thread 0
    itval.it_interval.tv_usec = itval.it_value.tv_usec = itval.it_interval.tv_sec = itval.it_value.tv_sec = 0;

    ret = setitimer(ITIMER_REAL, &itval, 0);
    if (ret != 0) {
      /* ERROR */
    }
  }

  if (TauEnv_get_tracing()) {
    Tau_sampling_outputTraceDefinitions(tid);
  }

  if (TauEnv_get_profiling()) {
    Tau_sampling_finalizeProfile(tid);
  }

  if (tid == 0) {
    // clear the hash map to eliminate memory leaks
    CallSiteCacheMap & mytab = TheCallSiteCache();
    for (CallSiteCacheMap::iterator it = mytab.begin(); it != mytab.end(); ++it) {
      CallSiteCacheNode * node = it->second;
      delete node;
    }
    TheCallSiteCache().clear();
    //TheCallSiteCache().erase(TheCallSiteCache().begin(), TheCallSiteCache().end());
#ifdef TAU_BFD
    //Tau_delete_bfd_units();
#endif
  }

  return 0;
}

/* *CWL* - This is workaround code for MPI where mvapich2 on Hera was
 found to conflict with EBS sampling operations if EBS was initialized
 before MPI_Init().
 */
extern "C" void Tau_sampling_init_if_necessary(void)
{
  static bool samplingThrInitialized[TAU_MAX_THREADS] = { false };

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  // sanity check - does the user want sampling at all?
  if (!TauEnv_get_ebs_enabled()) return;

  int tid = RtsLayer::localThreadId();
  // have we initialized already?
  if (samplingThrInitialized[tid]) return;

  /* Greetings, intrepid thread developer. We had a problem with OpenMP applications
   * which did not call instrumented functions or regions from an OpenMP region. In
   * those cases, TAU does not get a chance to initialize sampling on any thread other
   * than thread 0. By making this region an OpenMP parallel region, we initialize
   * sampling on all (currently known) OpenMP threads. Any threads created after this
   * point may not be recognized by TAU. But this should catch the 99% case.
   * By the way, this doesn't work on PGI. the master thread does all the work,
   * and the other threads don't get initialized. Just hope that with PGI, there
   * are instrumented functions inside the parallel regions, otherwise sampling
   * will only work on thread 0.  */
#if 0 && defined(TAU_OPENMP) && !defined(TAU_PTHREAD) && !defined(__PGI)
  // if the master thread is in TAU, in a non-parallel region
  if (omp_get_num_threads() == 1) {
    /* FIRST! make sure that we don't process samples while in this code */

    /* WE HAVE TO DO THIS! Otherwise, we end up with deadlock. Don't worry,
     * it is OK, because we know(?) there are no other active threads
     * thanks to the #define three lines above this */
    int numEnvLocks = RtsLayer::getNumEnvLocks();
    int numDBLocks = RtsLayer::getNumDBLocks();
    int tmpLocks = numEnvLocks;
    // This looks strange, but we want to make sure we REALLY unlock the locks
    while (tmpLocks > 0) {
      tmpLocks = RtsLayer::UnLockEnv();
    }
    tmpLocks = numDBLocks;
    while (tmpLocks > 0) {
      tmpLocks = RtsLayer::UnLockDB();
    }

    // do this for all threads
    int dummy = 0;
    int all_threads = omp_get_max_threads();
#pragma omp parallel for ordered 
    for (dummy = 0; dummy < all_threads; dummy++) {
      // but do it sequentially.
      //
      // Protect TAU from itself
      TauInternalFunctionGuard protects_this_function;
#pragma omp ordered 
      {
#pragma omp critical (creatingtopleveltimer)
        {
          // Getting the thread ID registers the OpenMP thread.
          int myTid = Tau_get_thread ();
          if (!samplingThrInitialized[myTid]) {
            Tau_sampling_init(myTid);
            samplingThrInitialized[myTid] = true;
            TAU_VERBOSE("Thread %d, %d initialized sampling\n", tid, myTid);
          }
        } // critical
      } // ordered
    } // for
    /* WE HAVE TO DO THIS! The environment was locked before we entered
     * this function, we unlocked it, so re-lock it for safety */
    for (tmpLocks = 0; tmpLocks < numDBLocks; tmpLocks++) {
      RtsLayer::LockDB();
    }
    for (tmpLocks = 0; tmpLocks < numEnvLocks; tmpLocks++) {
      RtsLayer::LockEnv();
    }
  }

#else
// handle all other cases!
  if (!samplingThrInitialized[tid]) {
    samplingThrInitialized[tid] = true;
    Tau_sampling_init(tid);
    TAU_VERBOSE("Thread %d initialized sampling\n", tid);
  }
#endif
}

extern "C" void Tau_sampling_finalize_if_necessary(void)
{
  static bool finalized = false;
  static bool thrFinalized[TAU_MAX_THREADS] = { false };
  int tid = Tau_get_local_tid();

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  // before wrapping things up, stop listening to signals.
  sigset_t x;
  sigemptyset(&x);
  sigaddset(&x, TAU_ALARM_TYPE);
#if defined(PTHREADS) || defined(TAU_OPENMP)
  pthread_sigmask(SIG_BLOCK, &x, NULL);
#else
  sigprocmask(SIG_BLOCK, &x, NULL);
#endif

  if (!finalized) {
    TAU_VERBOSE("TAU: <Node=%d.Thread=%d> finalizing sampling...\n", RtsLayer::myNode(), tid);
    fflush(stdout);
    RtsLayer::LockEnv();
    // check again, someone else might already have finalized by now.
    if (!finalized) {
      for (int i = 0; i < TAU_MAX_THREADS; i++) {
        thrFinalized[i] = false;
        // just in case, disable sampling.
        //samplingEnabled[i] = 0;
      }
      collectingSamples = 0;
      finalized = true;
    }
    RtsLayer::UnLockEnv();
  }

  if (!thrFinalized[tid]) {
    tau_sampling_flags()->samplingEnabled = 0;
    thrFinalized[tid] = true;
    Tau_sampling_finalize(tid);
  }

  // Kevin: should we finalize all threads on this process? I think so.
  if (tid == 0) {
    for (int i = 0; i < RtsLayer::getTotalThreads(); i++) {
      if (!thrFinalized[i]) {
        thrFinalized[i] = true;
        Tau_sampling_finalize(i);
      }
    }
  }
}

#endif //TAU_WINDOWS && TAU_ANDROID
