/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/paracomp/tau    **
*****************************************************************************
**    Copyright 2003  						   	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
**    Research Center Juelich, Germany                                     **
****************************************************************************/
/***************************************************************************
**	File 		: app.c 					  **
**	Description 	: TAU trace format reader application (uses C API)**
**	Author		: Sameer Shende					  **
**	Contact		: sameer@cs.uoregon.edu 	                  **
***************************************************************************/
#include <TAU_tf.h>
#include <stdio.h>

/* implementation of callback routines */
int EnterState(void *userData, double time, 
		unsigned int nodeid, unsigned int tid, unsigned int stateid)
{
  printf("Entered state %d time %g nid %d tid %d\n", 
		  stateid, time, nodeid, tid);
  return 0;
}

int LeaveState(void *userData, double time, unsigned int nid, unsigned int tid, unsigned int stateid)
{
  printf("Leaving state %d time %g nid %d tid %d\n", stateid, time, nid, tid);
  return 0;
}


int ClockPeriod( void*  userData, double clkPeriod )
{
  printf("Clock period %g\n", clkPeriod);
  return 0;
}

int DefThread(void *userData, unsigned int nodeid, unsigned int threadToken,
const char *threadName )
{
  printf("DefThread nid %d tid %d, thread name %s\n", 
		  nodeid, threadToken, threadName);
  return 0;
}

int EndTrace( void *userData, unsigned int nodeid, unsigned int threadid)
{
  printf("EndTrace nid %d tid %d\n", nodeid, threadid);
  return 0;
}

int DefStateGroup( void *userData, unsigned int stateGroupToken, 
		const char *stateGroupName )
{
  printf("StateGroup groupid %d, group name %s\n", stateGroupToken, 
		  stateGroupName);
  return 0;
}

int DefState( void *userData, unsigned int stateToken, const char *stateName, 
		unsigned int stateGroupToken )
{
  printf("DefState stateid %d stateName %s stategroup id %d\n",
		  stateToken, stateName, stateGroupToken);
  return 0;
}

int DefUserEvent( void *userData, unsigned int userEventToken,
		const char *userEventName, int monotonicallyIncreasing )
{

  printf("DefUserEvent event id %d user event name %s, monotonically increasing = %d\n", userEventToken,
		  userEventName, monotonicallyIncreasing);
  return 0;
}

int EventTrigger( void *userData, double time, 
		unsigned int nodeToken,
		unsigned int threadToken,
	       	unsigned int userEventToken,
		long long userEventValue)
{
  printf("EventTrigger: time %g, nid %d tid %d event id %d triggered value %lld \n", time, nodeToken, threadToken, userEventToken, userEventValue);
  return 0;
}

int SendMessage ( void*  userData,
                                double time,
                                unsigned int sourceNodeToken, 
                                unsigned int sourceThreadToken, 
				unsigned int destinationNodeToken,
				unsigned int destinationThreadToken,
				unsigned int messageSize,
				unsigned int messageTag,
				unsigned int messageComm
				)
    {
    printf("Message Send: time %g, nid %d, tid %d dest nid %d dest tid %d messageSize %d messageComm %d messageTag %lld \n", time, sourceNodeToken,
    sourceThreadToken, destinationNodeToken,
    destinationThreadToken, messageSize, messageComm, messageTag);
    return 0;
    }

int RecvMessage ( void*  userData,
                                double time,
                                unsigned int sourceNodeToken, 
                                unsigned int sourceThreadToken, 
				unsigned int destinationNodeToken,
				unsigned int destinationThreadToken,
				unsigned int messageSize,
				unsigned int messageTag,
				unsigned int messageComm
				)
  {
    printf("Message Recv: time %g, nid %d, tid %d dest nid %d dest tid %d messageSize %d messageComm %d messageTag %lld \n", time, sourceNodeToken,
    sourceThreadToken, destinationNodeToken,
    destinationThreadToken, messageSize, messageComm, messageTag);
    return 0;
    }

/* Reader module */
int main(int argc, char **argv)
{
  Ttf_FileHandleT fh;

  int recs_read, pos;
  Ttf_CallbacksT cb;

  /* main program: Usage app <trc> <edf> */
  if (argc != 3)
  {
    printf("Usage: %s <TAU trace> <edf file>\n", argv[0]);
    exit(1);
  }
     
  /* open trace file */
  fh = Ttf_OpenFileForInput( argv[1], argv[2]);
  if (!fh)
  {
    printf("ERROR:Ttf_OpenFileForInput fails");
    exit(1);
  }

  /* Fill the callback struct */
  cb.UserData = 0;
  cb.DefClkPeriod = ClockPeriod;
  cb.DefThread = DefThread;
  cb.DefStateGroup = DefStateGroup;
  cb.DefState = DefState;
  cb.EndTrace = EndTrace;
  cb.EnterState = EnterState;
  cb.LeaveState = LeaveState;
  cb.DefUserEvent = DefUserEvent;
  cb.EventTrigger = EventTrigger;
  cb.SendMessage = SendMessage;
  cb.RecvMessage = RecvMessage;
  pos = Ttf_RelSeek(fh,2);
  printf("Position returned %d\n", pos);

  recs_read = Ttf_ReadNumEvents(fh, cb, 4);
  printf("Read %d records\n", recs_read);

  recs_read = Ttf_ReadNumEvents(fh, cb, 100);
  printf("Read %d records\n", recs_read);

  Ttf_CloseFile(fh);
  return 0;
}


/***************************************************************************
 * $RCSfile: tau_reader.c,v $   $Author: scottb $
 * $Revision: 1.5 $   $Date: 2006/09/22 18:15:20 $
 * TAU_VERSION_ID: $Id: tau_reader.c,v 1.5 2006/09/22 18:15:20 scottb Exp $ 
 ***************************************************************************/
