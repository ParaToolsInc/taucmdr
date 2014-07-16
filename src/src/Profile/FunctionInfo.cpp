/******************************************************************************
 *
 *                        The TAU Performance System
 *                          http://tau.uoregon.edu/
 *
 * Copyright 1997-2014
 * Department of Computer and Information Science, University of Oregon
 * Advanced Computing Laboratory, Los Alamos National Laboratory
 *
 *****************************************************************************/
/**
 * @file
 * @brief   Declares class FunctionInfo
 * @date    Created 1998-04-24 00:23:34 +0000
 *
 * @authors
 * Adam Morris <amorris@cs.uoregon.edu>
 * Kevin Huck <khuck@cs.uoregon.edu>
 * Sameer Shende <sameer@cs.uoregon.edu>
 * Scott Biersdorff <scottb@cs.uoregon.edu>
 * Wyatt Joel Spear <wspear@cs.uoregon.edu>
 * John C. Linford <jlinford@paratools.com>
 *
 * @copyright
 * Copyright (c) 1997-2014
 * Department of Computer and Information Science, University of Oregon
 * Advanced Computing Laboratory, Los Alamos National Laboratory
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * (1) Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 * (2) Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 * (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
 *     be used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */


#include <sstream>
#include <vector>

#ifdef TAU_DOT_H_LESS_HEADERS
#include <iostream>
using namespace std;
#else /* TAU_DOT_H_LESS_HEADERS */
#include <iostream.h>
#endif /* TAU_DOT_H_LESS_HEADERS */

#include <stdio.h> 
#include <fcntl.h>
#include <time.h>
#include <stdlib.h>

#if (!defined(TAU_WINDOWS))
#include <unistd.h>
#endif //TAU_WINDOWS

#if defined(TAU_VAMPIRTRACE)
#include <Profile/TauVampirTrace.h>
#elif defined(TAU_EPILOG)
#include <elg_trc.h>
#elif defined(TAU_SCOREP)
#include <Profile/TauSCOREP.h>
#endif

#include <Profiler.h>
#include <Profile/TauTrace.h>
#include <Profile/TauInit.h>
#include <Profile/TauUtil.h>



namespace tau {
//=============================================================================


static char *strip_tau_group(const char *ProfileGroupName) {
  char *source = strdup(ProfileGroupName);
  const char *find = "TAU_GROUP_";
  char *ptr;

  ptr = strstr(source,find);
  while (ptr != NULL) {
    char *endptr = ptr+strlen(find);
    while (*endptr != '\0') {
      *ptr++ = *endptr++;
    }
    *ptr = '\0';
    ptr = strstr(source,find);
  }
  return source;
}

//////////////////////////////////////////////////////////////////////
// FunctionInfoInit is called by all four forms of FunctionInfo ctor
//////////////////////////////////////////////////////////////////////
FunctionInfo::FunctionInfo(std::string const & _name, std::string const & _type,
    TauGroup_t _profileGroup, char const * _profileGroupName,
    bool init, int tid) :
        //id(0),
        name(strdup(_name.c_str())),
        shortName(NULL),
        fullName(NULL),
        type(strdup(_type.c_str())),
        //memoryEvent(NULL),
        //headroomEvent(NULL),
        //groupName(NULL),
        allGroups(strip_tau_group(_profileGroupName)),
        profileGroup(_profileGroup),
        isCallSite(false),
        callSiteResolved(false),
        callSiteKeyId(0),
        firstSpecializedFunction(NULL)
{
  /* Make sure TAU is initialized */
  // FIXME: Remove this flag
  static bool flag = true;
  if (flag) {
    flag = false;
    Tau_init_initializeTAU();
  }

  groupName = strdup(RtsLayer::PrimaryGroup(allGroups).c_str());

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  // Use LockDB to avoid a possible race condition.
  RtsLayer::LockDB();

#ifndef TAU_WINDOWS
  // Necessary for signal-reentrancy to ensure the mmap memory manager
  //   is ready at this point.
  Tau_MemMgr_initIfNecessary();
#endif  

  // Since FunctionInfo constructor is called once for each function (static)
  // we know that it couldn't be already on the call stack.

  //Add function name to the name list.
  TauProfiler_theFunctionList(NULL, NULL, true, (const char *)GetName());

  // While accessing the global function database, lock it to ensure
  // an atomic operation in the push_back and size() operations. 
  // Important in the presence of concurrent threads.
  id = RtsLayer::GenerateUniqueId();
  TheFunctionDB().push_back(this);

#if defined(TAU_VAMPIRTRACE)
  string tau_vt_name(string(Name)+" "+string(Type));
  id = TAU_VT_DEF_REGION(tau_vt_name.c_str(), VT_NO_ID, VT_NO_LNO, VT_NO_LNO, GroupName, VT_FUNCTION);
#elif defined(TAU_EPILOG)
  string tau_elg_name(string(Name)+" "+string(Type));
  id = esd_def_region(tau_elg_name.c_str(), ELG_NO_ID, ELG_NO_LNO,
      ELG_NO_LNO, GroupName, ELG_FUNCTION);
#elif defined(TAU_SCOREP)
  string tau_silc_name(string(Name)+" "+string(Type));
  if (strstr(ProfileGroupName, "TAU_PHASE") != NULL) {
    id = SCOREP_Tau_DefineRegion( tau_silc_name.c_str(),
        SCOREP_TAU_INVALID_SOURCE_FILE,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_ADAPTER_COMPILER,
        SCOREP_TAU_REGION_PHASE
    );
  } else {
    id = SCOREP_Tau_DefineRegion( tau_silc_name.c_str(),
        SCOREP_TAU_INVALID_SOURCE_FILE,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_ADAPTER_COMPILER,
        SCOREP_TAU_REGION_FUNCTION
    );
  }
#endif

#ifdef TAU_PROFILEMEMORY
  {
    char * buff = new char[strlen(name)+strlen(type)+100];
    sprintf(buff, "%s %s - Heap Memory Used (KB)", name, type);
    memoryEvent = new TauUserEvent(buff);
    delete buff;
  }
#else
  memoryEvent = NULL;
#endif

#ifdef TAU_PROFILEHEADROOM
  {
    char * buff = new char[strlen(name)+strlen(type)+100];
    sprintf(buff, "%s %s - Memory Headroom Available (MB)", name, type);
    headroomEvent = new TauUserEvent(buff);
  }
#else
  headroomEvent = NULL;
#endif

  TauTraceSetFlushEvents(1);
  RtsLayer::UnLockDB();
}



char const * FunctionInfo::GetFullName()
{
  if (!fullName) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

    ostringstream ostr;
    if (strlen(GetType()) > 0 && strcmp(GetType(), " ") != 0) {
      ostr << GetName() << " " << GetType() << ":GROUP:" << GetAllGroups();
    } else {
      ostr << GetName() << ":GROUP:" << GetAllGroups();
    }

    fullName = Tau_util_removeRuns(ostr.str().c_str());
  }
  return fullName;
}

/* EBS Sampling Profiles */


void FunctionInfo::addPcSample(unsigned long *pcStack, int tid, double interval[TAU_MAX_COUNTERS])
{
#ifndef TAU_WINDOWS
  // Add to the mmap-ed histogram. We start with a temporary conversion. This
  //   becomes unnecessary once we stop using the vector.
  TauPathAccumulator * accumulator = ThreadData(tid).pathHistogram.get(pcStack);
  if (accumulator == NULL) {
    /* KAH - Whoops!! We can't call "new" here, because malloc is not
     * safe in signal handling. therefore, use the special memory
     * allocation routines */
    // accumulator = new TauPathAccumulator(1,interval);

    /* Use placement new to create a object in pre-allocated memory.
     * NOTE - this memory needs to be explicitly deallocated by calling the
     * destructor. I think the best place for that is in the destructor for
     * the hash table. */
    accumulator = (TauPathAccumulator*)Tau_MemMgr_malloc(tid, sizeof(TauPathAccumulator));
    new (accumulator) TauPathAccumulator(1, interval);

    bool success = ThreadData(tid).pathHistogram.insert(pcStack, *accumulator);
    if (!success) {
      fprintf(stderr, "addPcSample: Failed to insert sample.\n");
    }
  } else {
    accumulator->count++;
    for (int i = 0; i < Tau_Global_numCounters; i++) {
      accumulator->accumulator[i] += interval[i];
    }
  }
#endif // TAU_WINDOWS
}




//=============================================================================
} // END namespace tau
