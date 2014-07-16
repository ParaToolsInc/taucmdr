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
**	File 		: TAU_tf.h					  **
**	Description 	: TAU trace format reader library C, C++ API	  **
**	Author		: Sameer Shende, Holger Brunst			  **
**	Contact		: sameer@cs.uoregon.edu 	                  **
***************************************************************************/
#ifndef _TAU_TF_H_
#define _TAU_TF_H_

#include "TAU_tf_writer.h"

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/* callbacks */

typedef int (*Ttf_DefClkPeriodT)( void*  userData,
                                  double clkPeriod );

typedef int (*Ttf_DefThreadT)( void *userData,
                               unsigned int nodeToken,
                               unsigned int threadToken,
                               const char *threadName );

typedef int (*Ttf_EndTraceT)( void *userData,
                              unsigned int nodeToken,
			      unsigned int threadToken);

typedef int (*Ttf_DefStateGroupT)( void *userData,
                                   unsigned int stateGroupToken,
                                   const char *stateGroupName );

typedef int (*Ttf_DefStateT)( void *userData,
                              unsigned int stateToken,
                              const char *stateName,
                              unsigned int stateGroupToken );

typedef int (*Ttf_EnterStateT)( void*  userData,
                                double time,
                                unsigned int nodeToken,
                                unsigned int threadToken,
                                unsigned int stateToken );

typedef int (*Ttf_LeaveStateT)( void*  userData,
                                double time,
                                unsigned int nodeToken, 
                                unsigned int threadToken,
                                unsigned int stateToken );

typedef int (*Ttf_SendMessageT)( void*  userData,
                                double time,
                                unsigned int sourceNodeToken, 
                                unsigned int sourceThreadToken, 
				unsigned int destinationNodeToken,
				unsigned int destinationThreadToken,
				unsigned int messageSize,
				unsigned int messageTag,
				unsigned int messageComm
				);

typedef int (*Ttf_RecvMessageT)( void*  userData,
                                double time,
                                unsigned int sourceNodeToken, 
                                unsigned int sourceThreadToken, 
				unsigned int destinationNodeToken,
				unsigned int destinationThreadToken,
				unsigned int messageSize,
				unsigned int messageTag,
				unsigned int messageComm
				);

typedef int (*Ttf_DefUserEventT)( void *userData,
				unsigned int userEventToken,
				const char *userEventName,
				int monotonicallyIncreasing
				);

typedef int (*Ttf_EventTriggerT)( void *userData, 
				 double time, 
				 unsigned int nodeToken,
				 unsigned int threadToken,
				 unsigned int userEventToken,
				 /* double userEventValue*/
				 long long userEventValue
				);

/* callback table */
typedef struct Ttf_Callbacks
{
   void*  UserData; 
   Ttf_DefClkPeriodT  DefClkPeriod;
   Ttf_DefThreadT     DefThread;
   Ttf_DefStateGroupT DefStateGroup;
   Ttf_DefStateT      DefState;
   Ttf_EndTraceT      EndTrace;

   Ttf_EnterStateT    EnterState;
   Ttf_LeaveStateT    LeaveState;
   Ttf_SendMessageT   SendMessage;
   Ttf_RecvMessageT   RecvMessage;
   Ttf_DefUserEventT   DefUserEvent;
   Ttf_EventTriggerT   EventTrigger;
} Ttf_CallbacksT;
   



/* open a trace file for reading */
Ttf_FileHandleT Ttf_OpenFileForInput( const char *name , 
                                 const char *edf);



void Ttf_SetSubtractFirstTimestamp( Ttf_FileHandleT handle, int value );
void Ttf_SetNonBlocking( Ttf_FileHandleT handle, int value );

/* Seek to an absolute event position. 
 * A negative position indicates to start from the tail of the event stream. 
 * Returns the position if successful or 0 if an error occured */
int Ttf_AbsSeek( Ttf_FileHandleT handle, int eventPosition ); 


/* seek to a event position relative to the current position (just for completeness!) 
 * Returns the position if successful or 0 if an error occured */
int Ttf_RelSeek( Ttf_FileHandleT handle, int plusMinusNumEvents ); 


/* read n events and call appropriate handlers.
 * Returns the number of records read (can be 0).
 * Returns a -1 value when an error takes place. Check errno */
int Ttf_ReadNumEvents( Ttf_FileHandleT fileHandle,
                                   Ttf_CallbacksT callbacks,
                                   int numberOfEvents );


/* close a trace file */
Ttf_FileHandleT Ttf_CloseFile( Ttf_FileHandleT fileHandle );

#ifdef __cplusplus
}
#endif /* __cplusplus */


#endif /* _TAU_TF_H_ */



/***************************************************************************
 * $RCSfile: TAU_tf.h,v $   $Author: wspear $
 * $Revision: 1.7 $   $Date: 2005/11/21 22:45:36 $
 * TAU_VERSION_ID: $Id: TAU_tf.h,v 1.7 2005/11/21 22:45:36 wspear Exp $ 
 ***************************************************************************/



