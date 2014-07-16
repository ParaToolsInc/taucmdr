/****************************************************************************
 **			TAU Portable Profiling Package			   **
 **			http://www.cs.uoregon.edu/research/tau	           **
 *****************************************************************************
 **    Copyright 1997-2009	          			   	   **
 **    Department of Computer and Information Science, University of Oregon **
 **    Advanced Computing Laboratory, Los Alamos National Laboratory        **
 ****************************************************************************/
/***************************************************************************
 **	File 		: UserEvent.cpp					  **
 **	Description 	: TAU Profiling Package				  **
 **	Contact		: tau-bugs@cs.uoregon.edu 		 	  **
 **	Documentation	: See http://www.cs.uoregon.edu/research/tau      **
 ***************************************************************************/

//////////////////////////////////////////////////////////////////////
// Include Files 
//////////////////////////////////////////////////////////////////////
#ifdef TAU_CRAYXMT
#pragma mta instantiate used
#endif /* TAU_CRAYXMT */

#ifndef TAU_DISABLE_MARKERS
#define TAU_USE_EVENT_THRESHOLDS 1 
#endif /* TAU_DISABLE_MARKERS */

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>

#ifdef TAU_DOT_H_LESS_HEADERS
#include <iostream>
#include <sstream>
using namespace std;
#else /* TAU_DOT_H_LESS_HEADERS */
#include <iostream.h>
#include <sstream.h>
#endif /* TAU_DOT_H_LESS_HEADERS */

#ifdef TAU_VAMPIRTRACE
#include <otf.h>
#include "Profile/TauVampirTrace.h"
#endif /* TAU_VAMPIRTRACE */

#ifdef TAU_EPILOG
#include "elg_trc.h"
#endif /* TAU_EPILOG */

#ifdef TAU_SCOREP
#include <scorep/SCOREP_Tau.h>
#endif

#include <Profile/Profiler.h>
#include <Profile/TauTrace.h>
#include <Profile/TauInit.h>
#include <Profile/UserEvent.h>
#include <tau_internal.h>

using namespace tau;

#ifdef PGI
template void vector<TauUserEvent *>::insert_aux(vector<TauUserEvent *>::iterator, TauUserEvent *const &);
template TauUserEvent** copy_backward(TauUserEvent**,TauUserEvent**,TauUserEvent**);
template TauUserEvent** uninitialized_copy(TauUserEvent**,TauUserEvent**,TauUserEvent**);
#endif // PGI

namespace tau
{

// Orders callpaths by comparing arrays of profiler addresses stored as longs.
// The first element of the array is the array length.
struct ContextEventMapCompare
{
  bool operator()(long const * l1, long const * l2) const
  {
    int i;
    long const len = l1[0];
    if (len != l2[0]) return len < l2[0];
    for (i=0; i<len; ++i) {
      if (l1[i] != l2[i]) return l1[i] < l2[i];
    }
    return (l1[i] < l2[i]);
  }
};

struct ContextEventMap : public std::map<long *, TauUserEvent *, ContextEventMapCompare>
{
  ~ContextEventMap() {
    Tau_destructor_trigger();
  }
};

AtomicEventDB & TheEventDB(void)
{
  static AtomicEventDB eventDB;
  return eventDB;
}

// Add User Event to the EventDB
void TauUserEvent::AddEventToDB()
{
  // Protect TAU from itself
  TauInternalFunctionGuard protects_this_function;

  RtsLayer::LockDB();
  /* Set user event id */
  eventId = RtsLayer::GenerateUniqueId();
#ifdef TAU_VAMPIRTRACE
#ifdef TAU_VAMPIRTRACE_5_12_API
  uint32_t gid = vt_def_counter_group(VT_CURRENT_THREAD, "TAU Events");
  eventId = vt_def_counter(VT_CURRENT_THREAD, GetName().c_str(), OTF_COUNTER_TYPE_ABS|OTF_COUNTER_SCOPE_NEXT, gid, "#");
#else
  uint32_t gid = vt_def_counter_group("TAU Events");
  eventId = vt_def_counter(GetName().c_str(), OTF_COUNTER_TYPE_ABS|OTF_COUNTER_SCOPE_NEXT, gid, "#");
#endif /* TAU_VAMPIRTRACE_5_12_API */
#endif /* TAU_VAMPIRTRACE */

#ifdef TAU_SCOREP
  SCOREP_Tau_MetricHandle handle = SCOREP_TAU_INIT_METRIC_HANDLE;

  SCOREP_Tau_InitMetric( &handle, GetName().c_str(), "units");
  eventId=handle;
#endif
  TheEventDB().push_back(this);
  DEBUGPROFMSG("Successfully registered event " << GetName() << endl;);
  DEBUGPROFMSG("Size of eventDB is " << TheEventDB().size() <<endl);

  RtsLayer::UnLockDB();
}

///////////////////////////////////////////////////////////
// TriggerEvent records the value of data in the UserEvent
///////////////////////////////////////////////////////////
void TauUserEvent::TriggerEvent(TAU_EVENT_DATATYPE data, int tid, double timestamp, int use_ts)
{
  if (!Tau_global_getLightsOut()) {
#ifdef TAU_VAMPIRTRACE
    // *CWL* - x_uint64 (unsigned long long) violates the vampirtrace interface which expects
    //         unsigned long (previously uint64_t). The change from uint64_t to x_uint64 was
    //         previously made in response to problems with SCORE-P but was done as a global
    //         cut-and-paste which turned out to be unsafe. Since the use of time and cval
    //         are guarded for just vampirtrace, it should be safe to revert the changes
    //         for just vampirtrace.
    //
    //         Keep an eye on this. We should expect trouble as long as we cannot provide
    //         a proper abstraction for what constitutes a 64-bit unsigned integer in TAU.
    //         This should be a TODO item.
    // x_uint64 time;
    // x_uint64 cval;
    uint64_t time;
    uint64_t cval;
    int id = eventId;
    time = vt_pform_wtime();
    // cval = (x_uint64) data;
    cval = (uint64_t) data;
#ifdef TAU_VAMPIRTRACE_5_12_API
    vt_count(VT_CURRENT_THREAD, &time, id, 0);
#else
    vt_count(&time, id, 0);
#endif /* TAU_VAMPIRTRACE_5_12_API */
    time = vt_pform_wtime();
#ifdef TAU_VAMPIRTRACE_5_12_API
    vt_count(VT_CURRENT_THREAD, &time, id, cval);
#else
    vt_count(&time, id, cval);
#endif /* TAU_VAMPIRTRACE_5_12_API */
    time = vt_pform_wtime();
#ifdef TAU_VAMPIRTRACE_5_12_API
    vt_count(VT_CURRENT_THREAD, &time, id, 0);
#else
    vt_count(&time, id, 0);
#endif /* TAU_VAMPIRTRACE_5_12_API */

#else /* TAU_VAMPIRTRACE */
#ifndef TAU_EPILOG
    if (TauEnv_get_tracing()) {
      TauTraceEvent(eventId, (x_uint64)0, tid, (x_uint64)timestamp, use_ts);
      TauTraceEvent(eventId, (x_uint64)data, tid, (x_uint64)timestamp, use_ts);
      TauTraceEvent(eventId, (x_uint64)0, tid, (x_uint64)timestamp, use_ts);
    }
#endif /* TAU_EPILOG */
    /* Timestamp is 0, and use_ts is 0, so tracing layer gets timestamp */
#endif /* TAU_VAMPIRTRACE */

#ifdef TAU_SCOREP
    SCOREP_Tau_TriggerMetricDouble( eventId, data );
#endif /*TAU_SCOREP*/

    TAU_ASSERT(this != NULL, "this == NULL in TauUserEvent::TriggerEvent!  Make sure all databases are appropriately locked.\n");

#ifdef PROFILING_ON
    Data & d = ThreadData(tid);

    // Record this value
    d.lastVal = data;

    // Increment number of events
    ++d.nEvents;

    // Compute relevant statistics for the data
    if (minEnabled && data < d.minVal) {
#ifdef TAU_USE_EVENT_THRESHOLDS
      if (d.nEvents > 1 && data <= (1.0 - TauEnv_get_evt_threshold()) * d.minVal) {
        if (name[0] != '[') { //re-entrant
          char ename[20 + name.length()];
          sprintf(ename, "[GROUP=MIN_MARKER] %s", name.c_str());
          if (name.find("=>") == std::string::npos) {
            //DEBUGPROFMSG("Marker: "<<ename<<"  d.minVal = "<<d.minVal<<" data = "<<data<<" d.nEvents = "<<d.nEvents<<endl;);
#ifdef TAU_SCOREP
            TAU_TRIGGER_EVENT(ename, data);
#else /* TAU_SCOREP */
            TAU_TRIGGER_CONTEXT_EVENT_THREAD(ename, data, tid);
#endif /* TAU_SCOREP */
          }
        }
      }
#endif /* TAU_USE_EVENT_THRESHOLDS */
      d.minVal = data;
    }

    if (maxEnabled && data > d.maxVal) {
#ifdef TAU_USE_EVENT_THRESHOLDS
      if (d.nEvents > 1 && data >= (1.0 + TauEnv_get_evt_threshold()) * d.maxVal) {
        if (name[0] != '[') { //re-entrant
          char ename[20 + name.length()];
          sprintf(ename, "[GROUP=MAX_MARKER] %s", name.c_str());
          if (name.find("=>") == std::string::npos) {
            //DEBUGPROFMSG("Marker: "<<ename<<"  d.maxVal = "<<d.maxVal<<" data = "<<data<<" d.nEvents = "<<d.nEvents<<endl;);
#ifdef TAU_SCOREP
            TAU_TRIGGER_EVENT(ename, data);
#else /* TAU_SCOREP */
            TAU_TRIGGER_CONTEXT_EVENT_THREAD(ename, data, tid);
#endif /* TAU_SCOREP */
          }
        }
      }
#endif /* TAU_USE_EVENT_THRESHOLDS */
      d.maxVal = data;
    }

    if (meanEnabled) {
      d.sumVal += data;
    }
    if (stdDevEnabled) {
      d.sumSqrVal += data * data;
    }
#endif /* PROFILING_ON */
  } // Tau_global_getLightsOut
}


void TauUserEvent::ReportStatistics(bool ForEachThread)
{
  TAU_EVENT_DATATYPE TotalNumEvents, TotalSumValue, Minima, Maxima;
  vector<TauUserEvent*>::iterator it;

  Maxima = Minima = 0;
  cout << "TAU Runtime Statistics" << endl;
  cout << "*************************************************************" << endl;

  for (it = TheEventDB().begin(); it != TheEventDB().end(); it++) {
    DEBUGPROFMSG("TauUserEvent "<<
        (*it)->GetName() << "\n Min " << (*it)->GetMin() << "\n Max " <<
        (*it)->GetMax() << "\n Mean " << (*it)->GetMean() << "\n Sum Sqr " <<
        (*it)->GetSumSqr() << "\n NumEvents " << (*it)->GetNumEvents()<< endl;);

    TotalNumEvents = TotalSumValue = 0;

    for (int tid = 0; tid < TAU_MAX_THREADS; tid++) {
      if ((*it)->GetNumEvents(tid) > 0) {
        // There were some events on this thread
        TotalNumEvents += (*it)->GetNumEvents(tid);
        TotalSumValue += (*it)->GetSum(tid);

        if ((*it)->IsMinEnabled()) {
          // Min is not disabled
          // take the lesser of Minima and the min on that thread
          if (tid > 0) {
            // more than one thread
            Minima = (*it)->GetMin(tid) < Minima ? (*it)->GetMin(tid) : Minima;
          } else {
            // this is the first thread. Initialize Minima to the min on it.
            Minima = (*it)->GetMin(tid);
          }
        }

        if ((*it)->IsMaxEnabled()) {
          // Max is not disabled
          // take the maximum of Maxima and max on that thread
          if (tid > 0) {
            // more than one thread
            Maxima = (*it)->GetMax(tid) > Maxima ? (*it)->GetMax(tid) : Maxima;
          } else {
            // this is the first thread. Initialize Maxima to the max on it.
            Maxima = (*it)->GetMax(tid);
          }
        }

        if (ForEachThread) {
          // true, print statistics for this thread
          cout << "n,c,t " << RtsLayer::myNode() << "," << RtsLayer::myContext() << "," << tid
              << " : Event : " << (*it)->GetName() << endl
              << " Number : " << (*it)->GetNumEvents(tid) << endl
              << " Min    : " << (*it)->GetMin(tid) << endl
              << " Max    : " << (*it)->GetMax(tid) << endl
              << " Mean   : " << (*it)->GetMean(tid) << endl
              << " Sum    : " << (*it)->GetSum(tid) << endl << endl;
        }

      }    // there were no events on this thread
    }    // for all threads

    cout << "*************************************************************" << endl;
    cout << "Cumulative Statistics over all threads for Node: " << RtsLayer::myNode() << " Context: " << RtsLayer::myContext() << endl;
    cout << "*************************************************************" << endl;
    cout << "Event Name     = " << (*it)->GetName() << endl;
    cout << "Total Number   = " << TotalNumEvents << endl;
    cout << "Total Value    = " << TotalSumValue << endl;
    cout << "Minimum Value  = " << Minima << endl;
    cout << "Maximum Value  = " << Maxima << endl;
    cout << "-------------------------------------------------------------" << endl;
    cout << endl;
  }    // For all events
}


////////////////////////////////////////////////////////////////////////////
// Formulate Context Comparison Array, an array of addresses with size depth+2.
// The callpath depth is the 0th index, the user event goes is the last index
//////////////////////////////////////////////////////////////////////
long * TauContextUserEvent::FormulateContextComparisonArray(Profiler * current)
{
  int depth = TauEnv_get_callpath_depth();

  long * ary = new long[depth+2];
  memset(ary, 0, (depth+2)*sizeof(long));

  int i=1;
  // start writing to index 1, we fill in the depth after
  for(; current && depth; ++i) {
    ary[i] = Tau_convert_ptr_to_long(current->ThisFunction);
    current = current->ParentProfiler;
    --depth;
  }
  ary[i] = Tau_convert_ptr_to_long(userEvent);
  ary[0] = i; // set the depth

  return ary;
}

////////////////////////////////////////////////////////////////////////////
// Formulate Context Callpath name string
////////////////////////////////////////////////////////////////////////////
string TauContextUserEvent::FormulateContextNameString(Profiler * current)
{
  if (current) {
    ostringstream buff;
    buff << userEvent->GetName();

    int depth = TauEnv_get_callpath_depth();
    if (depth) {
      Profiler ** path = new Profiler*[depth];

      // Reverse the callpath to avoid string copies
      int i=depth-1;
      for (; current && i >= 0; --i) {
        path[i] = current;
        current = current->ParentProfiler;
      }
      // Now we can construct the name string by appending rather than prepending
      buff  << " : ";
      FunctionInfo * fi;
      for (++i; i < depth-1; ++i) {
        fi = path[i]->ThisFunction;
        buff << fi->GetName();
        if (strlen(fi->GetType()) > 0)
          buff << " " << fi->GetType();
        buff << " => ";
      }
      fi = path[i]->ThisFunction;
      buff << fi->GetName();
      if (strlen(fi->GetType()) > 0)
        buff << " " << fi->GetType();

      delete[] path;
    }

    // Return a new string object.
    // A smart STL implementation will not allocate a new buffer.
    return buff.str();
  } else {
    return "";
  }
}

////////////////////////////////////////////////////////////////////////////
// Trigger the context event
////////////////////////////////////////////////////////////////////////////
void TauContextUserEvent::TriggerEvent(TAU_EVENT_DATATYPE data, int tid, double timestamp, int use_ts)
{
  static ContextEventMap contextMap;
  if (!Tau_global_getLightsOut()) {

    // Protect TAU from itself
    TauInternalFunctionGuard protects_this_function;

    if (contextEnabled) {
      Profiler * current = TauInternal_CurrentProfiler(tid);
      long * comparison = FormulateContextComparisonArray(current);

      RtsLayer::LockDB();
      ContextEventMap::iterator it = contextMap.find(comparison);
      if (it == contextMap.end()) {
        contextEvent = new TauUserEvent(
            FormulateContextNameString(current),
            userEvent->IsMonotonicallyIncreasing());
        contextMap[comparison] = contextEvent;
      } else {
        contextEvent = it->second;
        delete[] comparison;
      }
      RtsLayer::UnLockDB();
      contextEvent->TriggerEvent(data, tid, timestamp, use_ts);
    }
    userEvent->TriggerEvent(data, tid, timestamp, use_ts);
  }
}

} // END namespace tau


////////////////////////////////////////////////////////////////////////////
//
////////////////////////////////////////////////////////////////////////////
extern "C"
x_uint64 TauUserEvent_GetEventId(TauUserEvent const * evt)
{
  return evt->GetId();
}


/***************************************************************************
 * $RCSfile: UserEvent.cpp,v $   $Author: amorris $
 * $Revision: 1.46 $   $Date: 2010/05/07 22:16:23 $
 * POOMA_VERSION_ID: $Id: UserEvent.cpp,v 1.46 2010/05/07 22:16:23 amorris Exp $ 
 ***************************************************************************/
