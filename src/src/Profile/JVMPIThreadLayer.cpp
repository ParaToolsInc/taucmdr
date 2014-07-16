/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 1997-2009 					      	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/***************************************************************************
**	File 		: JVMPIThreadLayer.cpp				  **
**	Description 	: TAU Profiling Package RTS Layer definitions     **
**			  for supporting Java Threads 			  **
**	Contact		: tau-team@cs.uoregon.edu 		 	  **
**	Documentation	: See http://www.cs.uoregon.edu/research/tau      **
***************************************************************************/


//////////////////////////////////////////////////////////////////////
// Include Files 
//////////////////////////////////////////////////////////////////////

//#define DEBUG_PROF

#ifdef TAU_DOT_H_LESS_HEADERS
#include <iostream>
using namespace std;
#else /* TAU_DOT_H_LESS_HEADERS */
#include <iostream.h>
#endif /* TAU_DOT_H_LESS_HEADERS */
#include <Profile/Profiler.h>
#include <Profile/TauJava.h>
#include <stdlib.h>



/////////////////////////////////////////////////////////////////////////
// Member Function Definitions For class JVMPIThreadLayer
// This allows us to get thread ids from 0..N-1 
/////////////////////////////////////////////////////////////////////////


/////////////////////////////////////////////////////////////////////////
// Define the static private members of JVMPIThreadLayer  
/////////////////////////////////////////////////////////////////////////

JavaVM 	* JVMPIThreadLayer::tauVM;
int 	  JVMPIThreadLayer::tauThreadCount = 0; 
JVMPI_RawMonitor JVMPIThreadLayer::tauNumThreadsLock ;
JVMPI_RawMonitor JVMPIThreadLayer::tauDBMutex ;
JVMPI_RawMonitor JVMPIThreadLayer::tauEnvMutex ;
JVMPI_Interface  * JVMPIThreadLayer::tau_jvmpi_interface = NULL;


////////////////////////////////////////////////////////////////////////
// RegisterThread() should be called before any profiling routines are
// invoked. This routine sets the thread id that is used by the code in
// FunctionInfo and Profiler classes. 
////////////////////////////////////////////////////////////////////////
int * JVMPIThreadLayer::RegisterThread(JNIEnv *env_id)
{
  static int initflag = JVMPIThreadLayer::InitializeThreadData();
  // if its in here the first time, setup mutexes etc.

  //THIS IS CURRENTLY LEAKING!
  int *threadId = new int;

  // Lock the mutex guarding the thread count before incrementing it.
  tau_jvmpi_interface->RawMonitorEnter(tauNumThreadsLock); 

  if (tauThreadCount == TAU_MAX_THREADS)
  {
    fprintf(stderr, "TAU>ERROR number of threads exceeds TAU_MAX_THREADS\n");
    fprintf(stderr, "Change TAU_MAX_THREADS parameter in <tau>/include/Profile/Profiler.h\n");
    fprintf(stderr, "And make install. Current value is %d\n", tauThreadCount);
    fprintf(stderr, "******************************************************************\n");
    tau_jvmpi_interface->ProfilerExit(1);
  }

  // Increment the number of threads present
  (*threadId) = RtsLayer::createThread();
  //(*threadId) = tauThreadCount ++;

  DEBUGPROFMSG("Thread id "<< *threadId << " Created! "<<endl);
  // Unlock it now 
  tau_jvmpi_interface->RawMonitorExit(tauNumThreadsLock); 
  // A thread should call this routine exactly once. 

  // Make this a thread specific data structure wrt the thread environment
  tau_jvmpi_interface->SetThreadLocalStorage(env_id, threadId); 
  

  return threadId;
}


////////////////////////////////////////////////////////////////////////
// GetThreadId wrapper to be used when we don't have the environment 
// pointer (JNIEnv *) that we get from JVMPI. Typically called by entry/exit
// of a non-Java layer. 
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::GetThreadId(void) 
{
  // First get the environment id of the thread using the JVM
  JNIEnv *env_id;

  int res = tauVM->GetEnv( (void **) &env_id, JNI_VERSION_1_2 );
  if (res < 0) {
    //printf("JVMPIThreadLayer::GetThreadId() gets -ve GetEnv result \n");
    DEBUGPROFMSG("JVMPIThreadLayer::GetThreadId() gets -ve GetEnv result \n");
    return -1;
  }
  if (env_id == (JNIEnv *) NULL)
  {
    printf("JVMPIThreadLayer::GetThreadId(): env_id is null! res = %d\n", res);
    return -1;
  }

  // We now have a valid env_id, call the other overloaded version of the 
  // the GetThreadId member
  return GetThreadId(env_id);

}

////////////////////////////////////////////////////////////////////////
// GetThreadId returns an id in the range 0..N-1 by looking at the 
// thread specific data.
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::GetThreadId(JNIEnv *env_id) 
{
  int *tid ;
   
  tid = (int *) tau_jvmpi_interface->GetThreadLocalStorage(env_id);
  // The thread id is stored in a thread specific storage

  if (tid == (int *) NULL)
  { // This thread needs to be registered
    tid = RegisterThread(env_id);
    if ((*tid) == 0) 
    { // Main JVM thread has tid 0, others have tid > 0 
      TauJavaLayer::CreateTopLevelRoutine(
	"THREAD=JVM-MainThread; THREAD GROUP=system", " ", "THREAD", (*tid));
    }
    else
    { // Internal thread that was just registered.
      TauJavaLayer::CreateTopLevelRoutine(
        "THREAD=JVM-InternalThread; THREAD GROUP=system"," ", "THREAD", (*tid));
    }

  }
  return (*tid); 

}

  



////////////////////////////////////////////////////////////////////////
// InitializeThreadData is called before any thread operations are performed. 
// It sets the default values for static private data members of the 
// JVMPIThreadLayer class.
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::InitializeThreadData(void)
{
  // Initialize the mutex
  tauNumThreadsLock = tau_jvmpi_interface->RawMonitorCreate("num threads lock");
  
  //cout <<" Initialized the thread Mutex data " <<endl;
  return 1;
}

////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::InitializeDBMutexData(void)
{
  // For locking functionDB 
  tauDBMutex =  tau_jvmpi_interface->RawMonitorCreate("FuncDB lock");
  
  //cout <<" Initialized the functionDB Mutex data " <<endl;
  return 1;
}

////////////////////////////////////////////////////////////////////////
// LockDB locks the mutex protecting TheFunctionDB() global database of 
// functions. This is required to ensure that push_back() operation 
// performed on this is atomic (and in the case of tracing this is 
// followed by a GetFunctionID() ). This is used in 
// FunctionInfo::FunctionInfoInit().
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::LockDB(void)
{
  static int initflag=InitializeDBMutexData();
  // Lock the functionDB mutex
  tau_jvmpi_interface->RawMonitorEnter(tauDBMutex);
  return 1;
}

////////////////////////////////////////////////////////////////////////
// UnLockDB() unlocks the mutex tauDBMutex used by the above lock operation
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::UnLockDB(void)
{
  // Unlock the functionDB mutex
  tau_jvmpi_interface->RawMonitorExit(tauDBMutex);
  return 1;
}  

////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::InitializeEnvMutexData(void)
{
  if (tau_jvmpi_interface == NULL) {
    fprintf (stderr,"Error, TAU's jvmpi interface was not initialized properly (java -XrunTAU ...)\n");
    fprintf (stderr,"When TAU is configured with -jdk=<dir>, it can only profile Java Programs!\n");
    exit(-1);
  }
  // For locking functionDB 
  tauEnvMutex =  tau_jvmpi_interface->RawMonitorCreate("Env lock");
  
  //cout <<" Initialized the Env Mutex data " <<endl;
  return 1;
}

////////////////////////////////////////////////////////////////////////
// LockEnv locks the mutex protecting TheFunctionDB() global database of 
// functions. This is required to ensure that push_back() operation 
// performed on this is atomic (and in the case of tracing this is 
// followed by a GetFunctionID() ). This is used in 
// FunctionInfo::FunctionInfoInit().
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::LockEnv(void)
{
  static int initflag=InitializeEnvMutexData();
  // Lock the Env mutex
  tau_jvmpi_interface->RawMonitorEnter(tauEnvMutex);
  return 1;
}

////////////////////////////////////////////////////////////////////////
// UnLockDB() unlocks the mutex tauDBMutex used by the above lock operation
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::UnLockEnv(void)
{
  // Unlock the Env mutex
  tau_jvmpi_interface->RawMonitorExit(tauEnvMutex);
  return 1;
}  
////////////////////////////////////////////////////////////////////////
// TotalThreads returns the number of active threads 
////////////////////////////////////////////////////////////////////////
int JVMPIThreadLayer::TotalThreads(void)
{
  int count;
  // For synchronization, we lock the thread count mutex. If we had a 
  // set and increment operation, we wouldn't need this. Optimization for
  // the future.

  tau_jvmpi_interface->RawMonitorEnter(tauNumThreadsLock);
  count = tauThreadCount;
  tau_jvmpi_interface->RawMonitorExit(tauNumThreadsLock);

  return count;
}

// Use JVMPI to get per thread cpu time (microseconds)
jlong JVMPIThreadLayer::getCurrentThreadCpuTime(void) {
  return tau_jvmpi_interface->GetCurrentThreadCpuTime() / 1000;
}
  
// EOF JVMPIThreadLayer.cpp 


/***************************************************************************
 * $RCSfile: JVMPIThreadLayer.cpp,v $   $Author: khuck $
 * $Revision: 1.8 $   $Date: 2009/03/13 00:46:56 $
 * TAU_VERSION_ID: $Id: JVMPIThreadLayer.cpp,v 1.8 2009/03/13 00:46:56 khuck Exp $
 ***************************************************************************/


