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
 * @brief   Declares class TauUserEvent
 * @date    Created 1998-04-24 00:18:04 +0000
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


#ifndef _USEREVENT_H_
#define _USEREVENT_H_

#include <string>
#include <limits>
#include <vector>
#include <map>
#include <Profile/TauInit.h>
#include <Profile/TauEnv.h>


namespace tau {
//=============================================================================

// Forward declaration
class Profiler;

//////////////////////////////////////////////////////////////////////
//
//////////////////////////////////////////////////////////////////////
typedef double tau_measurement_t;


//////////////////////////////////////////////////////////////////////
//
//////////////////////////////////////////////////////////////////////
class TauUserEvent
{
public:

  struct Data
  {
    Data() :
      minVal(std::numeric_limits<tau_measurement_t>::max()),
      maxVal(-std::numeric_limits<tau_measurement_t>::max()),
      sumVal(0), sumSqrVal(0), lastVal(0), userVal(0), nEvents(0)
    { }

    tau_measurement_t minVal;
    tau_measurement_t maxVal;
    tau_measurement_t sumVal;
    tau_measurement_t sumSqrVal;
    tau_measurement_t lastVal;
    tau_measurement_t userVal;
    size_t nEvents;
  };

  static void ReportStatistics(bool ForEachThread=false);

public:

  TauUserEvent() :
      eventId(0), name("No Name"),
      minEnabled(true), maxEnabled(true), meanEnabled(true),
      stdDevEnabled(true), monoIncreasing(false), writeAsMetric(false)
  {
    AddEventToDB();
  }

  TauUserEvent(TauUserEvent const & e) :
      eventId(0), name(e.name),
      minEnabled(e.minEnabled), maxEnabled(e.maxEnabled),
      meanEnabled(e.meanEnabled), stdDevEnabled(e.stdDevEnabled),
      monoIncreasing(e.monoIncreasing), writeAsMetric(false) 
  {
    AddEventToDB();
  }

  TauUserEvent(std::string const & name, bool increasing=false) :
      eventId(0), name(name), minEnabled(true), maxEnabled(true),
      meanEnabled(true), stdDevEnabled(true), monoIncreasing(increasing), writeAsMetric(false) 
  {
    AddEventToDB();
  }

  ~TauUserEvent(void) {
    Tau_destructor_trigger();
  }

  TauUserEvent & operator=(const TauUserEvent & e) {
    // Why isn't eventId copied?
    name = e.name;
    minEnabled = e.minEnabled;
    maxEnabled = e.maxEnabled;
    meanEnabled = e.meanEnabled;
    stdDevEnabled = e.stdDevEnabled;
    return *this;
  }

  x_uint64 GetId(void) const {
    return eventId;
  }

  std::string const & GetName(void) const {
    return name;
  }
  void SetName(std::string const & value) {
    name = value;
  }

  bool IsMinEnabled(void) const {
    return minEnabled;
  }
  void SetMinEnabled(bool value) {
    minEnabled = value;
  }

  bool IsMaxEnabled(void) const {
    return maxEnabled;
  }
  void SetMaxEnabled(bool value) {
    maxEnabled = value;
  }

  bool IsMeanEnabled(void) const {
    return meanEnabled;
  }
  void SetMeanEnabled(bool value) {
    meanEnabled = value;
  }

  bool IsStdDevEnabled(void) const {
    return stdDevEnabled;
  }
  void SetStdDevEnabled(bool value) {
    stdDevEnabled = value;
  }

  bool IsMonotonicallyIncreasing(void) const {
    return monoIncreasing;
  }
  void SetMonotonicallyIncreasing(bool value) {
    monoIncreasing = value;
  }

  void SetWriteAsMetric(bool value) {
    writeAsMetric = value;
  }
  
  bool GetWriteAsMetric() {
    return writeAsMetric;
  }
  
  tau_measurement_t GetMin(void) {
    Data const & d = ThreadData();
    return d.nEvents ? d.minVal : 0;
  }
  tau_measurement_t GetMin(int tid) {
    Data const & d = ThreadData(tid);
    return d.nEvents ? d.minVal : 0;
  }

  tau_measurement_t GetMax(void) {
    Data const & d = ThreadData();
    return d.nEvents ? d.maxVal : 0;
  }
  tau_measurement_t GetMax(int tid) {
    Data const & d = ThreadData(tid);
    return d.nEvents ? d.maxVal : 0;
  }

  tau_measurement_t GetSum(void) {
    return ThreadData().sumVal;
  }
  tau_measurement_t GetSum(int tid) {
    return ThreadData(tid).sumVal;
  }

  tau_measurement_t GetSumSqr(void) {
    return ThreadData().sumSqrVal;
  }
  tau_measurement_t GetSumSqr(int tid) {
    return ThreadData(tid).sumSqrVal;
  }

  tau_measurement_t GetMean(void) {
    Data const & d = ThreadData();
    return d.nEvents ? (d.sumVal / d.nEvents) : 0;
  }
  tau_measurement_t GetMean(int tid) {
    Data const & d = ThreadData(tid);
    return d.nEvents ? (d.sumVal / d.nEvents) : 0;
  }

  size_t GetNumEvents(void) {
    return ThreadData().nEvents;
  }
  size_t GetNumEvents(int tid) {
    return ThreadData(tid).nEvents;
  }

  void ResetData(void) {
    ThreadData() = Data();
  }
  void ResetData(int tid) {
    ThreadData(tid) = Data();
  }

  void TriggerEvent(tau_measurement_t data) {
    TriggerEvent(data, RtsLayer::myThread(), 0, 0);
  }
  void TriggerEvent(tau_measurement_t data, int tid) {
    TriggerEvent(data, tid, 0, 0);
  }
  void TriggerEvent(tau_measurement_t data, int tid, double timestamp, int use_ts);

private:

  Data & ThreadData() {
    return eventData[RtsLayer::myThread()];
  }

  Data & ThreadData(int tid) {
    return eventData[tid];
  }

  void AddEventToDB();

  Data eventData[TAU_MAX_THREADS];

  x_uint64 eventId;
  std::string name;
  bool minEnabled;
  bool maxEnabled;
  bool meanEnabled;
  bool stdDevEnabled;
  bool monoIncreasing;
  bool writeAsMetric;
};


//////////////////////////////////////////////////////////////////////
// Don't inherit TauUserEvent to avoid virtual function overhead
//////////////////////////////////////////////////////////////////////
class TauContextUserEvent
{
public:

  TauContextUserEvent(char const * name, bool monoIncr=false) :
#ifdef TAU_SCOREP
      contextEnabled(false),
#else
      contextEnabled(TauEnv_get_callpath_depth() != 0),
#endif
      userEvent(new TauUserEvent(name, monoIncr)),
      contextEvent(NULL)
  { }
  
  TauContextUserEvent(const TauContextUserEvent &c) :
    contextEnabled(c.contextEnabled),
      userEvent(c.userEvent),
      contextEvent(c.contextEvent)
  { }

  TauContextUserEvent & operator=(const TauContextUserEvent &rhs) {
      userEvent = rhs.userEvent;
      contextEvent = rhs.contextEvent; 
      contextEnabled = rhs.contextEnabled;
      return *this;
  }
  
  ~TauContextUserEvent() {
    delete userEvent;
  }

  void SetContextEnabled(bool value) {
    contextEnabled = value;
  }

  std::string const & GetUserEventName() const {
    return userEvent->GetName();
  }
  
  void SetAllEventName(std::string const & value) {
    userEvent->SetName(value);
    if (contextEvent != NULL)
    {
      std::size_t sep_pos = contextEvent->GetName().find(':');
      if (sep_pos != std::string::npos)
      {
        std::string context_portion = contextEvent->GetName().substr(sep_pos, contextEvent->GetName().length()-sep_pos);
        //form new string
        //contextEvent = userEvent;
        std::string new_context = userEvent->GetName();
        new_context += std::string(" ");
        new_context += context_portion;
        contextEvent->SetName(new_context);
      }
      else {
        contextEvent->SetName(value);
      }
    }

  }

  std::string const & GetName() const {
    return contextEvent->GetName();
  }
  
  void SetName(std::string const & value) {
    contextEvent->SetName(value);
  }

  TauUserEvent *getContextUserEvent() {
    return contextEvent;
  }

  TauUserEvent *getUserEvent() {
    return userEvent;
  }

  void TriggerEvent(tau_measurement_t data) {
    TriggerEvent(data, RtsLayer::myThread(), 0, 0);
  }
  void TriggerEvent(tau_measurement_t data, int tid) {
    TriggerEvent(data, tid, 0, 0);
  }
  void TriggerEvent(tau_measurement_t data, int tid, double timestamp, int use_ts);

private:

  long * FormulateContextComparisonArray(Profiler * current);
  std::string FormulateContextNameString(Profiler * current);

  bool contextEnabled;
  TauUserEvent * userEvent;
  TauUserEvent * contextEvent;
};


//////////////////////////////////////////////////////////////////////
//
//////////////////////////////////////////////////////////////////////
struct AtomicEventDB : public std::vector<TauUserEvent*>
{
  AtomicEventDB() {
    Tau_init_initializeTAU();
  }
  ~AtomicEventDB() {
    Tau_destructor_trigger();
  }
};

AtomicEventDB & TheEventDB(void);


//=============================================================================
} // END namespace tau


#endif /* _USEREVENT_H_ */

