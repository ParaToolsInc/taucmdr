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
#include <vector>
#include <map>
#include <stdint.h>
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


//TODO: FIXME: (re)Move this declaration
extern "C" int Tau_Global_numCounters;

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
      pathHistogram(NULL), numCalls(0), numSubrs(0), alreadyOnStack(false)
    {
      memset(exclTime, 0, sizeof(exclTime));
      memset(inclTime, 0, sizeof(inclTime));
    }

    size_t numCalls;
    size_t numSubrs;
    bool alreadyOnStack;
    double exclTime[TAU_MAX_COUNTERS];
    double inclTime[TAU_MAX_COUNTERS];

    TauPathHashTable<TauPathAccumulator> pathHistogram;
  };

  FunctionInfo(std::string const & _name, std::string const & _type,
      TauGroup_t _profileGroup=TAU_DEFAULT, char const * _primaryGroup="TAU_DEFAULT",
      bool init=true, int tid=RtsLayer::myThread());

  ~FunctionInfo() {
    TheSafeToDumpData() = 0;
  }

  //! TODO: Document
  uint64_t GetId();

  // Cached, generated on first access
  std::string const & GetFullName();

  // Cached, generated on first access
  std::string const & GetGroupString();

  //! TODO: Document
  void addPcSample(unsigned long *pc, int tid, double interval[TAU_MAX_COUNTERS]);


  std::string const & GetName() const {
    return name;
  }
  void SetName(std::string const & str) {
    name = str;
  }

  std::string const & GetShortName() const {
    return shortName;
  }
  void SetShortName(std::string const & str) {
    shortName = str;
  }

  std::string const & GetType() const {
    return type;
  }
  void SetType(std::string const & str) {
    type = str;
  }

  std::string const & GetPrimaryGroup() const {
    return primaryGroup;
  }
  void SetPrimaryGroup(std::string const & newGroup) {
    // TODO: Reset all group info when primary group changes?
    primaryGroup = newGroup;
    allGroups = newGroup;
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

  bool IsCallSiteResolved() const {
    return callSiteResolved;
  }

  unsigned long GetCallSiteKeyId() const {
    return callSiteKeyId;
  }

  FunctionInfo * GetFirstSpecializedFunction() const {
    return firstSpecializedFunction;
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



  void AddExclTime(double t[], int tid) {
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



  void AddInclTime(double t[], int tid) {
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

private:

  std::string ConstructEventName(std::string const & evtName) const {
    std::ostringstream buff;
    buff << name;
    if (type.length()) {
      buff << " " << type;
    }
    buff << " - " << evtName;
    return buff.str();
  }

  uint64_t id;
  std::string name;
  std::string shortName;
  std::string fullName;
  std::string type;
  TauGroup_t profileGroup;    //TODO: FIX groups
  std::string primaryGroup;   //TODO: FIX groups
  std::string allGroups;      //TODO: FIX groups
  TauUserEvent memoryEvent;
  TauUserEvent headroomEvent;

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



void tauCreateFI(void **ptr, const char *name, const char *type, TauGroup_t ProfileGroup, const char *ProfileGroupName);
void tauCreateFI(void **ptr, const char *name, const std::string& type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName);
void tauCreateFI(void **ptr, const std::string& name, const char *type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName);
void tauCreateFI(void **ptr, const std::string& name, const std::string& type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName);
void tauCreateFI_signalSafe(void **ptr, const std::string& name, const char *type, TauGroup_t ProfileGroup,
    const char *ProfileGroupName);

//=============================================================================
} // END namespace tau


#endif /* _FUNCTIONINFO_H_ */
