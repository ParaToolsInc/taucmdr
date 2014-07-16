/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 1997  						   	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/***************************************************************************
**	File 		: FunctionInfo.cpp				  **
**	Description 	: TAU Profiling Package				  **
*	Contact		: tau-team@cs.uoregon.edu 		 	  **
**	Documentation	: See http://www.cs.uoregon.edu/research/tau      **
***************************************************************************/

//////////////////////////////////////////////////////////////////////
// Include Files 
//////////////////////////////////////////////////////////////////////

#include <Profile/Profiler.h>
#include <sstream>
#include <algorithm>

#ifdef TAU_DOT_H_LESS_HEADERS
#include <iostream>
#else /* TAU_DOT_H_LESS_HEADERS */
#include <iostream.h>
#endif /* TAU_DOT_H_LESS_HEADERS */

#include <stdio.h> 
#include <fcntl.h>
#include <time.h>
#include <stdlib.h>

#if (!defined(TAU_WINDOWS))
 #include <unistd.h>
#else
  #include <vector>
#endif //TAU_WINDOWS

#ifdef TAU_VAMPIRTRACE 
#include <Profile/TauVampirTrace.h>
#else /* TAU_VAMPIRTRACE */
#ifdef TAU_EPILOG
#include "elg_trc.h"
#endif /* TAU_EPILOG */
#endif /* TAU_VAMPIRTRACE */

#ifdef TAU_SCOREP
#include <Profile/TauSCOREP.h>
#endif

#include <Profile/TauTrace.h>
#include <Profile/TauInit.h>
#include <Profile/TauUtil.h>

using namespace std;

namespace tau {
//=============================================================================






//////////////////////////////////////////////////////////////////////
// Member Function Definitions For class FunctionInfo
//////////////////////////////////////////////////////////////////////


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


FunctionInfo::FunctionInfo(string const & _name, string const & _type,
    TauGroup_t _profileGroup, char const * _primaryGroup, bool init, int tid) :
        name(_name),
        type(_type),
        profileGroup(_profileGroup),
        primaryGroup(_primaryGroup),
        allGroups(strip_tau_group(_primaryGroup)),
        memoryEvent(ConstructEventName("Heap Memory Used (KB)")),
        headroomEvent(ConstructEventName("Memory Headroom Available (MB)")),
        isCallSite(false),
        callSiteResolved(false),
        callSiteKeyId(0),
        firstSpecializedFunction(NULL)
{
  // TODO: Fix this initialization nonsense

  /* Make sure TAU is initialized */
  static bool flag = true;
  if (flag) {
    flag = false;
    Tau_init_initializeTAU();
  }

  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  // Use LockDB to avoid a possible race condition.
  RtsLayer::LockDB();
  id = RtsLayer::GenerateUniqueId();

  // TODO: Fix this TAU_WINDOWS=SAMPLING stuff
#ifndef TAU_WINDOWS
  // Necessary for signal-reentrancy to ensure the mmap memory manager
  //   is ready at this point.
  Tau_MemMgr_initIfNecessary();
#endif  



  // Since FunctionInfo constructor is called once for each function (static)
  // we know that it couldn't be already on the call stack.

  //Add function name to the name list.
  TauProfiler_theFunctionList(NULL, NULL, true, GetName().c_str());

  // While accessing the global function database, lock it to ensure
  // an atomic operation in the push_back and size() operations. 
  // Important in the presence of concurrent threads.
  TheFunctionDB().push_back(this);


#if defined(TAU_VAMPIRTRACE)
  string tau_vt_name = name + " " + type;
  id = TAU_VT_DEF_REGION(tau_vt_name.c_str(), VT_NO_ID, VT_NO_LNO, VT_NO_LNO, primaryGroup, VT_FUNCTION);
#elif defined(TAU_EPILOG)
  string tau_elg_name = name + " " + type;
  id = esd_def_region(tau_elg_name.c_str(), ELG_NO_ID, ELG_NO_LNO, ELG_NO_LNO, primaryGroup, ELG_FUNCTION);
#elif defined(TAU_SCOREP)
  string tau_silc_name = name + " " + type;
  if (primaryGroup.find("TAU_PHASE") == string:npos) {
    id = SCOREP_Tau_DefineRegion(tau_silc_name.c_str(),
        SCOREP_TAU_INVALID_SOURCE_FILE,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_ADAPTER_COMPILER,
        SCOREP_TAU_REGION_PHASE);
  } else {
    id = SCOREP_Tau_DefineRegion(tau_silc_name.c_str(),
        SCOREP_TAU_INVALID_SOURCE_FILE,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_INVALID_LINE_NO,
        SCOREP_TAU_ADAPTER_COMPILER,
        SCOREP_TAU_REGION_FUNCTION);
  }
#endif

  TauTraceSetFlushEvents(1);
  RtsLayer::UnLockDB();
}



//////////////////////////////////////////////////////////////////////
uint64_t FunctionInfo::GetId()
{
  // FIXME: To avoid data races, we use a lock if the id has not been created
  if (id == 0) {
    while (id == 0) {
      RtsLayer::LockDB();
      RtsLayer::UnLockDB();
    }
  }
  return id;
}
	    

//////////////////////////////////////////////////////////////////////
void tauCreateFI(void **ptr, const char *name, const char *type, TauGroup_t ProfileGroup, const char *ProfileGroupName)
{
  if (*ptr == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

//Use The ENV lock here.
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::LockEnv();
#else
    RtsLayer::LockEnv();
#endif
    if (*ptr == 0) {
      *ptr = new FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::UnLockEnv();
#else
    RtsLayer::UnLockEnv();
#endif
  }
}

void tauCreateFI(void **ptr, const char *name, const string& type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName)
{
  if (*ptr == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::LockEnv();
#else
    RtsLayer::LockEnv();
#endif
    if (*ptr == 0) {
      *ptr = new FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::UnLockEnv();
#else
    RtsLayer::UnLockEnv();
#endif

  }
}

void tauCreateFI_signalSafe(void **ptr, const string& name, const char *type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName)
{
  if (*ptr == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::LockEnv();
#else
    RtsLayer::LockEnv();
#endif
    if (*ptr == 0) {
    /* KAH - Whoops!! We can't call "new" here, because malloc is not
     * safe in signal handling. therefore, use the special memory
     * allocation routines */
#ifndef TAU_WINDOWS
    *ptr = Tau_MemMgr_malloc(RtsLayer::unsafeThreadId(), sizeof(FunctionInfo));
    /*  now, use the pacement new function to create a object in
     *  pre-allocated memory. NOTE - this memory needs to be explicitly
     *  deallocated by explicitly calling the destructor. 
     *  I think the best place for that is in the destructor for
     *  the hash table. */
    new(*ptr) FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
#else
    new FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
#endif
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::UnLockEnv();
#else
    RtsLayer::UnLockEnv();
#endif
  }
}

void tauCreateFI(void **ptr, const string& name, const char *type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName)
{
  if (*ptr == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::LockEnv();
#else
    RtsLayer::LockEnv();
#endif
    if (*ptr == 0) {
      *ptr = new FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::UnLockEnv();
#else
    RtsLayer::UnLockEnv();
#endif
  }
}

void tauCreateFI(void **ptr, const string& name, const string& type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName)
{
  if (*ptr == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::LockEnv();
#else
    RtsLayer::LockEnv();
#endif
    if (*ptr == 0) {
      *ptr = new FunctionInfo(name, type, ProfileGroup, ProfileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1)
    RtsLayer::UnLockEnv();
#else
    RtsLayer::UnLockEnv();
#endif
  }
}

static bool BothAreWhitespace(char a, char b)
{
  return (a == b) && isspace(a);
}

string const & FunctionInfo::GetFullName()
{
  if (fullName.length() == 0) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

    ostringstream ostr;
    ostr << name;
    if (type.length() > 0 && type != " ") {
      ostr << " " << type;
    }
    ostr << ":GROUP:" << allGroups;

    // Duplicate buffer into fullName
    fullName = ostr.str();
    // Replace runs of whitespace chars with a single whitespace char.
    // Kept chars are moved to the front of fullName and an iterator pointing
    // to the new end of the string is returned.
    // Finally, trim fullName to remove extra chars at end of string.
    fullName.erase(unique(fullName.begin(), fullName.end(), BothAreWhitespace), fullName.end());
  }
  // Return reference to fullName and discard buffer
  return fullName;
}

std::string const & FunctionInfo::GetGroupString()
{
  if (groupString.length() == 0) {
    ostringstream buff;

    for(int i=0; i<groups.size()-1; ++i) {
      string const & group = groups[i];
      buff << group << "|"
    }
    buff << groups[groups.size()-1];
    groupString = buff.str();
  }
  return groupString;
}


/* EBS Sampling Profiles */

void FunctionInfo::addPcSample(unsigned long *pcStack, int tid, double interval[TAU_MAX_COUNTERS])
{
#ifndef TAU_WINDOWS
  // Add to the mmap-ed histogram. We start with a temporary conversion. This
  //   becomes unnecessary once we stop using the vector.
  TauPathAccumulator * accumulator = pathHistogram[tid]->get(pcStack);
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

    bool success = pathHistogram[tid]->insert(pcStack, *accumulator);
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
