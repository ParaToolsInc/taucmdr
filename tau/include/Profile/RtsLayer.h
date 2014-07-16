/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 1997-2008  						   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/****************************************************************************
**	File 		: RtsLayer.h					   **
**	Description 	: TAU Profiling Package Runtime System Layer	   **
**	Author		: Sameer Shende					   **
**	Contact		: tau-bugs@cs.uoregon.edu                	   **
**	Documentation	: See http://www.cs.uoregon.edu/research/tau       **
****************************************************************************/

#ifndef _RTSLAYER_H_
#define _RTSLAYER_H_

#include <map>
#include <string>
#include <functional>
#include <utility>

//////////////////////////////////////////////////////////////////////
//
// class RtsLayer
//
// This class is used for porting the TAU Profiling package to other
// platforms and software frameworks. It contains functions to get
// the node id, thread id etc. When Threads are implemented, myThread()
// method should return the thread id in {0..N-1} where N is the total
// number of threads. All interaction with the outside world should be
// restrained to this class. 
//////////////////////////////////////////////////////////////////////

typedef std::map<std::string, TauGroup_t, std::less<std::string> > ProfileMap_t;


double TauWindowsUsecD(void);

class RtsLayer {
  // Layer for Profiler to interact with the Runtime System
public:
 	
  RtsLayer () { }  // defaults
  ~RtsLayer () { } 

  static int _createThread(void);
  static int createThread(void);
  static void destroyThread(int id);
  static void recycleThread(int id);

#ifdef JAVA
  static bool& TheUsingJNI(void);
#endif

  static TauGroup_t & TheProfileMask(void);
  static bool& TheEnableInstrumentation(void);
  static bool& TheShutdown(void);
  static int& TheNode(void);
  static int& TheContext(void);
  static long GenerateUniqueId(void);
  static ProfileMap_t& TheProfileMap(void);
  static TauGroup_t getProfileGroup(char const *  ProfileGroup) ;
  static TauGroup_t enableProfileGroup(TauGroup_t  ProfileGroup) ;
  static TauGroup_t disableProfileGroup(TauGroup_t  ProfileGroup) ;
  static TauGroup_t generateProfileGroup(void) ;
  static TauGroup_t enableProfileGroupName(char const * ProfileGroup) ;
  static TauGroup_t disableProfileGroupName(char const * ProfileGroup) ;
  static TauGroup_t enableAllGroups(void) ;
  static TauGroup_t disableAllGroups(void) ;
  static TauGroup_t resetProfileGroup(void) ;
  static int setAndParseProfileGroups (char *prog, char *str) ;
  static bool isEnabled(TauGroup_t  ProfileGroup) ; 
  static void ProfileInit(int& argc, char**& argv);
  static std::string PrimaryGroup(const char *ProfileGroupName);
  static bool isCtorDtor(const char *name);

  static std::string GetRTTI(const char *name); 
  inline static const char * CheckNotNull(const char * str) {
    if (str) return str;
    else return "  ";
  }

	static void Initialize(void);

  static int 	SetEventCounter(void);
  static double GetEventCounter(void);

  static void   getUSecD(int tid, double *values);

  static void getCurrentValues(int tid, double *values);

  static int setMyNode(int NodeId, int tid=RtsLayer::myThread());

  static int setMyContext(int ContextId);

  static const char* getSingleCounterName(); 
  static const char* getCounterName(int i); 

  // Return the number of the 'current' node.
  static int myNode(void);

  // Return the number of the 'current' context.
  static int myContext(void);

  // Return the number of the 'current' thread. 0..TAU_MAX_THREADS-1
  static int myThread(void);

  static int unsafeThreadId(void);
 
 	// Return the local thread id (ignoring tasks) This is a 
	// low-overhead call but DO NOT use this call when
	// accessing Profiler stack or the FunctionInfo DB.
  static int localThreadId(void);
  static int unsafeLocalThreadId(void);

  static int getPid();
  static int getTid();

#ifdef KTAU_NG
  static int getLinuxKernelTid();
#endif /* KTAU_NG */

  static int RegisterThread();
	
  static void RegisterFork(int nodeid, enum TauFork_t opcode);

  // This ensure that the FunctionDB (global) is locked while updating
  static int LockDB(void);
  static int UnLockDB(void);
  static int getNumDBLocks(void);

  static int LockEnv(void);
  static int UnLockEnv(void);
  static int getNumEnvLocks(void);

  static int getTotalThreads();


private:

  static void threadLockDB(void);
  static void threadUnLockDB(void);

  static void threadLockEnv(void);
  static void threadUnLockEnv(void);

  static int lockDBCount[TAU_MAX_THREADS];
  static int lockEnvCount[TAU_MAX_THREADS];

  static bool initLocks();
  static bool initEnvLocks();
  //  static int *numThreads();

};

extern "C" int Tau_RtsLayer_createThread();
extern "C" int Tau_RtsLayer_TheEnableInstrumentation();

#endif /* _RTSLAYER_H_  */
/***************************************************************************
 * $RCSfile: RtsLayer.h,v $   $Author: amorris $
 * $Revision: 1.34 $   $Date: 2010/04/08 23:07:41 $
 * POOMA_VERSION_ID: $Id: RtsLayer.h,v 1.34 2010/04/08 23:07:41 amorris Exp $ 
 ***************************************************************************/
