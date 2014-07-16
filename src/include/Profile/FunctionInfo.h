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

#ifndef _FUNCTIONINFO_H_
#define _FUNCTIONINFO_H_

#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <stdint.h>
#include <Profiler.h>
#include <Profile/UserEvent.h>
#include <Profile/TauGlobal.h>
#include <Profile/TauInit.h>

// For EBS Sampling Profiles with custom allocator support
#ifndef TAU_WINDOWS
#include <sys/types.h>
#include <unistd.h>

#include <Profile/TauPathHash.h>
#include <Profile/TauSampling.h>
#endif //TAU_WINDOWS


namespace tau {
//=============================================================================


/******************************************************************************
 * @class FunctionInfo
 *
 * @brief This class instantiated once per code region as a static variable.
 * It will be constructed the first time the function is called, and that
 * constructor registers this object (and therefore the function) with the
 * timer system.
 */
class FunctionInfo
{
public:

  struct Data
  {
    Data() :
      numCalls(0), numSubrs(0), alreadyOnStack(false),
      pathHistogram(RtsLayer::getTid())
    {
      memset(exclTime, 0, sizeof(exclTime));
      memset(inclTime, 0, sizeof(inclTime));

      // FIXME: Get rid of this nasty hack
      memset(dumpExclusiveValues, 0, sizeof(exclTime));
      memset(dumpInclusiveValues, 0, sizeof(inclTime));
    }

    size_t numCalls;
    size_t numSubrs;
    bool alreadyOnStack;
    double exclTime[TAU_MAX_COUNTERS];
    double inclTime[TAU_MAX_COUNTERS];

    // FIXME: Get rid of this nasty hack
    double dumpExclusiveValues[TAU_MAX_COUNTERS];
    double dumpInclusiveValues[TAU_MAX_COUNTERS];

    TauPathHashTable<TauPathAccumulator> pathHistogram;
  };

  FunctionInfo(std::string const & _name, std::string const & _type,
      TauGroup_t _profileGroup=TAU_DEFAULT, char const * _primaryGroup="TAU_DEFAULT",
      bool init=true, int tid=RtsLayer::myThread());

  ~FunctionInfo() {
    TheSafeToDumpData() = 0;
  }


  // FIXME: Ugly nasty hack
  double * getDumpExclusiveValues(int tid) {
    return ThreadData(tid).dumpExclusiveValues;
  }
  // FIXME: Ugly nasty hack
  double * getDumpInclusiveValues(int tid) {
    return ThreadData(tid).dumpInclusiveValues;
  }
  // FIXME: Ugly nasty hack
  void getInclusiveValues(int tid, double *values) {
    Data & d = ThreadData(tid);
    for(int i=0; i<Tau_Global_numCounters; i++) {
      values[i] = d.inclTime[i];
    }
  }
  // FIXME: Ugly nasty hack
  void getExclusiveValues(int tid, double *values) {
    Data & d = ThreadData(tid);
    for(int i=0; i<Tau_Global_numCounters; i++) {
      values[i] = d.exclTime[i];
    }
  }


  //! TODO: Document
  uint64_t GetId() {
    // To avoid data races, we use a lock if the id has not been created
    while (!id) {
      RtsLayer::LockDB();
      RtsLayer::UnLockDB();
    }
    return id;
  }

  // Cached, generated on first access
  char const * GetFullName();

  // Cached, generated on first access
  char const * GetGroupString();

  //! TODO: Document
  // FIXME: Name
  void addPcSample(unsigned long *pc, int tid, double interval[TAU_MAX_COUNTERS]);


  char const * GetName() const {
    return name;
  }
  void SetName(char const * const str) {
    name = str;
  }

  char const * GetShortName() const {
    return shortName;
  }
  void SetShortName(char const * const str) {
    shortName = str;
  }

  char const * GetType() const {
    return type;
  }
  void SetType(char const * const str) {
    type = str;
  }

  char const * GetPrimaryGroup() const {
    return groupName;
  }
  void SetPrimaryGroup(char const * const newGroup) {
    // TODO: Reset all group info when primary group changes?
    groupName = newGroup;
    allGroups = newGroup;
  }

  char const * GetAllGroups() const {
    return allGroups;
  }

  TauUserEvent * GetMemoryEvent() const {
    return memoryEvent;
  }

  TauUserEvent * GetHeadroomEvent() const {
    return headroomEvent;
  }

  TauGroup_t GetProfileGroup() const {
    return profileGroup;
  }
  void SetProfileGroup(TauGroup_t gr) {
    profileGroup = gr;
  }

  bool IsCallSite() const {
    return isCallSite;
  }
  void SetIsCallSite(bool value) {
    isCallSite = value;
  }

  bool IsCallSiteResolved() const {
    return callSiteResolved;
  }
  void SetCallSiteResolved(bool value) {
    callSiteResolved = value;
  }

  unsigned long GetCallSiteKeyId() const {
    return callSiteKeyId;
  }
  void SetCallSiteKeyId(unsigned long id) {
    callSiteKeyId = id;
  }

  FunctionInfo * GetFirstSpecializedFunction() const {
    return firstSpecializedFunction;
  }
  void SetFirstSpecializedFunction(FunctionInfo * const fi) {
    firstSpecializedFunction = fi;
  }



  void IncrNumCalls(int tid) {
    ThreadData(tid).numCalls++;
  }
  size_t GetNumCalls(int tid) const {
    return ThreadData(tid).numCalls;
  }
  void SetNumCalls(int tid, long calls) {
    ThreadData(tid).numCalls = calls;
  }

  void IncrNumSubrs(int tid) {
    ThreadData(tid).numSubrs++;
  }
  long GetNumSubrs(int tid) const {
    return ThreadData(tid).numSubrs;
  }
  void SetNumSubrs(int tid, long subrs) {
    ThreadData(tid).numSubrs = subrs;
  }

  bool GetAlreadyOnStack(int tid) const {
    return ThreadData(tid).alreadyOnStack;
  }
  void SetAlreadyOnStack(bool value, int tid) {
    ThreadData(tid).alreadyOnStack = value;
  }



  void AddExclTime(double const t[], int tid) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.exclTime[i] += t[i];
    }
  }
  void AddExclTime(double value, int tid, int counter) {
    ThreadData(tid).exclTime[counter] += value;
  }

  double const * GetExclTime(int tid) const {
    return ThreadData(tid).exclTime;
  }
  double GetExclTime(int tid, int counter) const {
    return ThreadData(tid).exclTime[counter];
  }

  void SetExclTime(int tid, double value) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.exclTime[i] = value;
    }
  }
  void SetExclTime(int tid, double excltime[]) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.exclTime[i] = excltime[i];
    }
  }



  void AddInclTime(double const t[], int tid) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.inclTime[i] += t[i];
    }
  }
  void AddInclTime(double value, int tid, int counter) {
    ThreadData(tid).inclTime[counter] += value;
  }

  double const * GetInclTime(int tid) const {
    return ThreadData(tid).inclTime;
  }
  double GetInclTime(int tid, int counter) const {
    return ThreadData(tid).inclTime[counter];
  }

  void SetInclTime(int tid, double value) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.inclTime[i] = value;
    }
  }
  void SetInclTime(int tid, double incltime[]) {
    Data & d = ThreadData(tid);
    for (int i = 0; i < Tau_Global_numCounters; ++i)
      d.inclTime[i] = incltime[i];
  }



  //! Called by a function to decrease its parent functions time
  //! exclude from it the time spent in child function
  void ExcludeTime(double t[], int tid) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; ++i) {
      d.exclTime[i] -= t[i];
    }
  }

  //! if exclusive time is negative (at Stop) we set it to zero during
  //! compensation. This function is used to reset it to zero for single
  //! and multiple counters
  void ResetExclTimeIfNegative(int tid) {
    Data & d = ThreadData(tid);
    for (int i=0; i<Tau_Global_numCounters; i++) {
      if (d.exclTime[i] < 0) {
        d.exclTime[i] = 0;
      }
    }
  }

  TauPathHashTable<TauPathAccumulator> const & GetPathHistogram(int tid) const {
    return ThreadData(tid).pathHistogram;
  }
  TauPathHashTable<TauPathAccumulator> & GetPathHistogram(int tid) {
    return ThreadData(tid).pathHistogram;
  }

private:

  std::string ConstructEventName(std::string const & evtName) const {
    std::ostringstream buff;
    buff << name;
    if (strlen(type) > 0) {
      buff << " " << type;
    }
    buff << " - " << evtName;
    return buff.str();
  }

  uint64_t id;
  char const * name;
  char const * shortName;
  char const * fullName;
  char const * type;
  TauUserEvent * memoryEvent;
  TauUserEvent * headroomEvent;

  // TODO: Fix groups
  char const * groupName;
  char const * allGroups;
  TauGroup_t profileGroup;

  // For CallSite discovery
  bool isCallSite;
  bool callSiteResolved;
  unsigned long callSiteKeyId;
  FunctionInfo * firstSpecializedFunction;

  Data __d[TAU_MAX_THREADS];

  Data & ThreadData() {
    return __d[RtsLayer::myThread()];
  }
  Data const & ThreadData() const {
    return __d[RtsLayer::myThread()];
  }
  Data & ThreadData(int tid) {
    return __d[tid];
  }
  Data const & ThreadData(int tid) const {
    return __d[tid];
  }

};
/* END class FunctionInfo ****************************************************/



/******************************************************************************
 * @brief
 */
static inline void tauCreateFI(void ** ptr,
    std::string const & name, std::string const & type,
    TauGroup_t profileGroup, char const * profileGroupName)
{
  if (!*ptr) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1) {
      RtsLayer::LockEnv();
    }
#else
    RtsLayer::LockEnv();
#endif
    if (!*ptr) {
      *ptr = new FunctionInfo(name, type, profileGroup, profileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1) {
      RtsLayer::UnLockEnv();
    }
#else
    RtsLayer::UnLockEnv();
#endif
  }
}

/******************************************************************************
 * @brief
 */
static inline void tauCreateFI_signalSafe(void ** ptr,
    std::string const & name, std::string const & type,
    TauGroup_t profileGroup, char const * profileGroupName)
{
#ifdef TAU_WINDOWS
  tauCreateFI(ptr, name, type, profileGroup, profileGroupName);
#else
  if (!*ptr) {
    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1) {
      RtsLayer::LockEnv();
    }
#else
    RtsLayer::LockEnv();
#endif
    if (!*ptr) {
      /* KAH - Whoops!! We can't call "new" here, because malloc is not
       * safe in signal handling. therefore, use the special memory
       * allocation routines */
      *ptr = Tau_MemMgr_malloc(RtsLayer::unsafeThreadId(), sizeof(FunctionInfo));
      /*  now, use the placement new function to create a object in
       *  pre-allocated memory. NOTE - this memory needs to be explicitly
       *  deallocated by explicitly calling the destructor.
       *  I think the best place for that is in the destructor for
       *  the hash table. */
      new (*ptr) FunctionInfo(name, type, profileGroup, profileGroupName);
    }
#ifdef TAU_CHARM
    if (RtsLayer::myNode() != -1) {
      RtsLayer::UnLockEnv();
    }
#else
    RtsLayer::UnLockEnv();
#endif
  }
#endif /* TAU_WINDOWS */
}

//=============================================================================
} // END namespace tau


#endif /* _FUNCTIONINFO_H_ */
