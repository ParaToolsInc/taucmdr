/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.cs.uoregon.edu/research/tau	           **
*****************************************************************************
**    Copyright 2010                                                       **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/****************************************************************************
**	File            : TauUnify.cpp                                     **
**	Contact		: tau-bugs@cs.uoregon.edu                          **
**	Documentation	: See http://tau.uoregon.edu                       **
**                                                                         **
**      Description     : Event unification                                **
**                                                                         **
****************************************************************************/


#ifdef TAU_MPI
#include <mpi.h>
#endif /* TAU_MPI */

#ifdef TAU_UNIFY

#include <TauUtil.h>
#include <TauMetrics.h>
#include <Profiler.h>
#include <TauUnify.h>

#include <algorithm>
using namespace std;

/** local unification object, one is created for each child rank that we talk to */
typedef struct {
  int rank;       // MPI rank of child
  char *buffer;   // buffer given to us by rank
  int numEvents;  // number of events
  char **strings; // pointers into buffer for strings
  int *mapping;   // mapping table for this child
  int idx;        // index used for merge operation
  int *sortMap;   // sort map for this rank
  int globalNumItems;  // global number of items
} unify_object_t;

/** unification merge object */
typedef struct {

  /** This is a vector of pointers to currently existing strings 
   *  inside the contiguous buffers from child ranks */
  vector<char*> strings;

  /* the number of entries, we can't use strings.size() because the merged 
     strings only exist on the parent */
  int numStrings;

  /* mapping table */
  int *mapping;

} unify_merge_object_t;



/** Comparator class used to create a sort map for unification */
class EventComparator : public binary_function<int, int, bool> {

private:
  EventLister *eventLister;

public:

  /** Constructor takes an EventLister, stores it for use with comparison */
  EventComparator(EventLister *eventLister) {
    this->eventLister = eventLister;
  }

  /** Compare two integers based on the strings that they index */
  bool operator() (int l1, int l2) const {
    return strcmp(eventLister->getEvent(l1),eventLister->getEvent(l2)) < 0;
  }
};


/** Return a table represeting a sorted list of the events */
int *Tau_unify_generateSortMap(EventLister *eventLister) {
#ifdef TAU_MPI
  int rank, numRanks;
  PMPI_Comm_rank(MPI_COMM_WORLD, &rank);
  PMPI_Comm_size(MPI_COMM_WORLD, &numRanks);
#endif /* TAU_MPI */

  int numEvents = eventLister->getNumEvents();
  int *sortMap = (int*) TAU_UTIL_MALLOC(numEvents*sizeof(int));

  for (int i=0; i<numEvents; i++) {
    sortMap[i] = i;
  }

  sort(sortMap, sortMap + numEvents, EventComparator(eventLister));

  return sortMap;
}


/** Return a Tau_util_outputDevice containing a buffer of the event definitions */
Tau_util_outputDevice *Tau_unify_generateLocalDefinitionBuffer(int *sortMap, EventLister *eventLister) {
  int numEvents = eventLister->getNumEvents();

  // create a buffer-based output device
  Tau_util_outputDevice *out = Tau_util_createBufferOutputDevice();

  // write the number of events into the output device
  Tau_util_output(out,"%d%c", numEvents, '\0');

  // write each event into the output device
  for(int i=0;i<numEvents;i++) {
    Tau_util_output(out,"%s%c", eventLister->getEvent(sortMap[i]), '\0');
  }

  return out;
}

/** Process a buffer from a given rank, return a unify_object_t */
unify_object_t *Tau_unify_processBuffer(char *buffer, int rank) {
  
  // create the unification object
  unify_object_t *unifyObject = (unify_object_t*) TAU_UTIL_MALLOC(sizeof(unify_object_t));
  unifyObject->buffer = buffer;
  unifyObject->rank = rank;

  // read the number of events from the buffer
  int numEvents;
  sscanf(buffer,"%d", &numEvents);
  unifyObject->numEvents = numEvents;

  // assign the "string" pointers to their locations within the buffer
  unifyObject->strings = (char **) TAU_UTIL_MALLOC(sizeof(char*) * numEvents);
  buffer = strchr(buffer, '\0')+1;
  for (int i=0; i<numEvents; i++) {
    unifyObject->strings[i] = buffer;
    buffer = strchr(buffer, '\0')+1;
  }

  // create an initial mapping table for this rank
  unifyObject->mapping = (int*) TAU_UTIL_MALLOC(sizeof(int) * numEvents);
  for (int i=0; i<numEvents; i++) {
    unifyObject->mapping[i] = i;
  }
  return unifyObject;
}

/** Generates a definition buffer from a unify_merge_object_t */
Tau_util_outputDevice *Tau_unify_generateMergedDefinitionBuffer(unify_merge_object_t &mergedObject, 
								EventLister *eventLister) {
  Tau_util_outputDevice *out = Tau_util_createBufferOutputDevice();

  Tau_util_output(out,"%d%c", mergedObject.strings.size(), '\0');
  for(unsigned int i=0;i<mergedObject.strings.size();i++) {
    Tau_util_output(out,"%s%c", mergedObject.strings[i], '\0');
  }

  return out;
}

/** Merge a set of unification objects.  Because each set of event identifiers is sorted,
    this is a simple merge operation. */
unify_merge_object_t *Tau_unify_mergeObjects(vector<unify_object_t*> &objects) {
  unify_merge_object_t *mergedObject = new unify_merge_object_t();

  for (unsigned int i=0; i<objects.size(); i++) {
    // reset index pointers to start
    objects[i]->idx = 0;
  }

  bool finished = false;

  int count = 0;

  while (!finished) {
    // merge objects

    char *nextString = NULL;
    for (unsigned int i=0; i<objects.size(); i++) {
      if (objects[i]->idx < objects[i]->numEvents) {
        if (nextString == NULL) {
          nextString = objects[i]->strings[objects[i]->idx];
        } else {
          char *compareString = objects[i]->strings[objects[i]->idx];
          if (strcmp(nextString, compareString) > 0) {
            nextString = compareString;
          }
        }
      }
    }
 
    // the next string is given in nextString at this point
    if (nextString != NULL) {
      mergedObject->strings.push_back(nextString);
    }

    finished = true;

    // write the mappings and check if we are finished
    for (unsigned int i=0; i<objects.size(); i++) {
      if (objects[i]->idx < objects[i]->numEvents) {
	char * compareString = objects[i]->strings[objects[i]->idx];
	if (strcmp(nextString, compareString) == 0) {
	  objects[i]->mapping[objects[i]->idx] = count;
	  objects[i]->idx++;
	}
	if (objects[i]->idx < objects[i]->numEvents) {
	  finished = false;
	}
      }
    }
    
    if (nextString != NULL) {
      count++;
    }
  }

  mergedObject->numStrings = count;

  return mergedObject;
}



/** Using MPI, unify events for a given EventLister */
Tau_unify_object_t *Tau_unify_unifyEvents(EventLister *eventLister) {
  int rank, numRanks;
  rank = 0;
  numRanks = 1;
#ifdef TAU_MPI
  MPI_Status status;

  PMPI_Comm_rank(MPI_COMM_WORLD, &rank);
  PMPI_Comm_size(MPI_COMM_WORLD, &numRanks);
#endif /* TAU_MPI */

  // for internal timing
  x_uint64 start, end;

  if (rank == 0) {
    TAU_VERBOSE("TAU: Unifying...\n");
    start = TauMetrics_getTimeOfDay();
  }

  // generate our own sort map
  int *sortMap = Tau_unify_generateSortMap(eventLister);

  // array of unification objects
  vector<unify_object_t*> *unifyObjects = new vector<unify_object_t*>();

  // add ourselves
  Tau_util_outputDevice *out = Tau_unify_generateLocalDefinitionBuffer(sortMap, eventLister);
  char *defBuf = Tau_util_getOutputBuffer(out);
  int defBufSize = Tau_util_getOutputBufferLength(out);
  unifyObjects->push_back(Tau_unify_processBuffer(defBuf, -1 /* no rank */));


  // define our merge object
  unify_merge_object_t *mergedObject = NULL;

  // use binomial heap (like MPI_Reduce) to communicate with parent/children
  int mask = 0x1;
  int parent = -1;

  while (mask < numRanks) {
    if ((mask & rank) == 0) {
      int source = (rank | mask);
      if (source < numRanks) {
	
	int recv_buflen = 0;

#ifdef TAU_MPI
	// send ok-to-go
	PMPI_Send(NULL, 0, MPI_INT, source, 0, MPI_COMM_WORLD);
	
	// receive buffer length
	PMPI_Recv(&recv_buflen, 1, MPI_INT, source, 0, MPI_COMM_WORLD, &status);
#endif /* TAU_MPI */

	// Only receive and allocate memory if there's something to receive.
	//   Note that this condition only applies to Atomic events.
	if (recv_buflen > 0) {
	  // allocate buffer
	  char *recv_buf = (char *) TAU_UTIL_MALLOC(recv_buflen);
	  
#ifdef TAU_MPI
	  // receive buffer
	  PMPI_Recv(recv_buf, recv_buflen, MPI_CHAR, source, 0, MPI_COMM_WORLD, &status);
#endif /* TAU_MPI */
	  
	  // add unification object to array
	  unifyObjects->push_back(Tau_unify_processBuffer(recv_buf, source));
	}
      }

    } else {
      // I've received from all my children, now process and send the results up.

      if (unifyObjects->size() > 1) {
	// merge children
	mergedObject = Tau_unify_mergeObjects(*unifyObjects);
	
	// generate buffer to send to parent
	Tau_util_outputDevice *out = Tau_unify_generateMergedDefinitionBuffer(*mergedObject, eventLister);
	defBuf = Tau_util_getOutputBuffer(out);
	defBufSize = Tau_util_getOutputBufferLength(out);
      }

      parent = (rank & (~ mask));

#ifdef TAU_MPI
      // recieve ok to go
      PMPI_Recv(NULL, 0, MPI_INT, parent, 0, MPI_COMM_WORLD, &status);
      
      // send length
      PMPI_Send(&defBufSize, 1, MPI_INT, parent, 0, MPI_COMM_WORLD);
#endif /* TAU_MPI */
      
      // Send data only if the buffer size is greater than 0.
      //   This applies only to Atomic events.
      if (defBufSize > 0) {
#ifdef TAU_MPI
	// send data
	PMPI_Send(defBuf, defBufSize, MPI_CHAR, parent, 0, MPI_COMM_WORLD);
#endif /* TAU_MPI */
      }
      break;
    }
    mask <<= 1;
  }

  int globalNumItems;

  if (rank == 0) {
    // rank 0 will now put together the final event id map
    mergedObject = Tau_unify_mergeObjects(*unifyObjects);

    globalNumItems = mergedObject->strings.size();
  }


  if (mergedObject == NULL) {
    // leaf functions allocate a phony merged object to use below
    int numEvents = eventLister->getNumEvents();
    mergedObject = new unify_merge_object_t();
    mergedObject->numStrings = numEvents;
  }

  // receive reverse mapping table from parent
  if (parent != -1) {
    mergedObject->mapping = (int *) TAU_UTIL_MALLOC(sizeof(int)* mergedObject->numStrings);
    
#ifdef TAU_MPI
    PMPI_Recv(mergedObject->mapping, mergedObject->numStrings, 
	      MPI_INT, parent, 0, MPI_COMM_WORLD, &status);
#endif /* TAU_MPI */

    // apply mapping table to children
    for (unsigned int i=0; i<unifyObjects->size(); i++) {
      for (int j=0; j<(*unifyObjects)[i]->numEvents; j++) {
	(*unifyObjects)[i]->mapping[j] = mergedObject->mapping[(*unifyObjects)[i]->mapping[j]];
      }
    }
  }

  // send tables to children
  for (unsigned int i=1; i<unifyObjects->size(); i++) {
#ifdef TAU_MPI
    PMPI_Send((*unifyObjects)[i]->mapping, (*unifyObjects)[i]->numEvents, 
	      MPI_INT, (*unifyObjects)[i]->rank, 0, MPI_COMM_WORLD);
#endif /* TAU_MPI */
  }

  /* debug: output final table */
  // if (rank == 0) {
  //   unify_object_t *object = (*unifyObjects)[0];
  //   for (int i=0; i<object->numEvents; i++) {
  //     fprintf (stderr, "[rank %d] = Entry %d maps to [%d] is %s\n", rank, i, object->mapping[i], object->strings[i]);
  //   }
  // }

  if (rank == 0) {
    // finalize timing and write into metadata
    end = TauMetrics_getTimeOfDay();
    eventLister->setDuration(((double)(end-start))/1000000.0f);
    TAU_VERBOSE("TAU: Unifying Complete, duration = %.4G seconds\n", 
		((double)(end-start))/1000000.0f);
    char tmpstr[256];
    sprintf(tmpstr, "%.4G seconds", ((double)(end-start))/1000000.0f);
    TAU_METADATA("TAU Unification Time", tmpstr);
  }

  // the local object
  unify_object_t *object = (*unifyObjects)[0];

#ifdef TAU_MPI
  PMPI_Bcast (&globalNumItems, 1, MPI_INT, 0, MPI_COMM_WORLD);
#endif /* TAU_MPI */

  Tau_unify_object_t *tau_unify_object = (Tau_unify_object_t*) TAU_UTIL_MALLOC(sizeof(Tau_unify_object_t));
  tau_unify_object->globalNumItems = globalNumItems;
  tau_unify_object->sortMap = sortMap;
  tau_unify_object->mapping = object->mapping;
  tau_unify_object->localNumItems = object->numEvents;
  tau_unify_object->globalStrings = NULL;

  if (rank == 0) {
    char **globalStrings = (char**)TAU_UTIL_MALLOC(sizeof(char*)*globalNumItems);

    for (unsigned int i=0; i<mergedObject->strings.size(); i++) {
      globalStrings[i] = strdup(mergedObject->strings[i]);
    }
    tau_unify_object->globalStrings = globalStrings;
  }

  /* free up memory */
  delete mergedObject;

  Tau_util_destroyOutputDevice(out);

  free ((*unifyObjects)[0]->strings);
  free ((*unifyObjects)[0]);

  for (unsigned int i=1; i<unifyObjects->size(); i++) {
    free ((*unifyObjects)[i]->buffer);
    free ((*unifyObjects)[i]->strings);
    free ((*unifyObjects)[i]->mapping);
    free ((*unifyObjects)[i]);
  }
  delete unifyObjects;

  // return the unification object that will be used to map local <-> global ids
  return tau_unify_object;
}

/** We store a unifier for the functions and atomic events for use externally */
/* *CWL* 2010-10-11: Is this safe? Are threads not used here? */
Tau_unify_object_t *functionUnifier=0, *atomicUnifier=0;
extern "C" Tau_unify_object_t *Tau_unify_getFunctionUnifier() {
  return functionUnifier;
}
extern "C" Tau_unify_object_t *Tau_unify_getAtomicUnifier() {
  return atomicUnifier;
}

/** Merge both function and atomic event definitions */
extern "C" int Tau_unify_unifyDefinitions() {
  FunctionEventLister *functionEventLister = new FunctionEventLister();
  functionUnifier = Tau_unify_unifyEvents(functionEventLister);
  AtomicEventLister *atomicEventLister = new AtomicEventLister();
  atomicUnifier = Tau_unify_unifyEvents(atomicEventLister);
  return 0;
}


#endif /* TAU_UNIFY */

#ifdef TAU_MPC
extern "C" int TauInitMpcThreads(int* rank) {
  static bool firsttime = true; 
  if (firsttime) {
    for (int i = 0; i < TAU_MAX_THREADS; i++) {
      rank[i] = -1;
    }
    firsttime = false;
  }
  return 0;
}

extern "C" int TauGetMpiRank(void) {
  static int firsttime = 1;
  static int *rank = NULL;
  int retval;

  RtsLayer::LockDB(); 
  int tid = RtsLayer::myThread();
  if (firsttime) {
    if (rank == NULL) {
      rank = new int[TAU_MAX_THREADS]; 
      firsttime = TauInitMpcThreads(rank);
    }
  }
  if (rank[tid] == -1) {
    PMPI_Comm_rank(MPI_COMM_WORLD, &rank[tid]);
  }
  retval = rank[tid];
  RtsLayer::UnLockDB();

  return retval;
}
#else /* !TAU_MPC */

extern "C" int TauGetMpiRank(void)
{
#ifdef TAU_MPI
  int rank;
  PMPI_Comm_rank(MPI_COMM_WORLD, &rank);
  return rank;
#else
  return 0;
#endif /* TAU_MPI */
}
#endif /* TAU_MPC */
