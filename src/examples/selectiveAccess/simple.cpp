
#include <Profile/Profiler.h>
/****************************************************************************
** File 	: klargest.c	
** Author 	: Sameer Shende					
** Contents 	: program to calculate the kth largest element in two ways 
** Directory	: $(TAUDIR)/examples/autoinstrument/
** Usage 	: program [<size>] [<k>]
**		  e.g., % klargest 5000 675 
*****************************************************************************/
#include <string>
#include <vector>
#include <iostream>
using namespace std;
#include <stdio.h>
#include <sys/time.h>
#include <limits.h> /* for INT_MIN */
#include <stdlib.h>
#include "decl.h"

#define DEFAULT_SIZE 1000000
#define DEFAULT_K    4 /* fourth largest element from the array */
#define middle(i)	5*i+2
/* the large array is partitioned into 5 elements each 2, 7, 12 etc. are 
positions of the middle elements in the array */

int size; /* global - size of the array */
int *M;   /* the median array */

TAU_REGISTER_EVENT(qsize, "Size of Array given to QuickSort");

TAU_REGISTER_EVENT(ksize, "Size of Array given to Select Kth Largest");


/**************************************************************************
** Function   : select_kth_largest				   
** Parameters : k, array of integers S and n - the size of array.
** Description: The SELECT algorithm to find the kth largest element from 
** 		the set of integers S in O(n) time. Used recursively. 
** Returns    : returns the kth largest element.
***************************************************************************/
int select_kth_largest(int k, int *S, int n)
{
  TAU_PROFILE("int select_kth_largest(int, int *, int)", " ", TAU_USER);

  TAU_EVENT(ksize, n);
 /* return the kth largest element from the ordered set S of integers */
  /* n is the number of elements in S */
  /* Algorithm : if n < 50 then sort in dec. order S, return kth largest element
	                 in S
		 else
			divide S into ceil(n/5) sequences of 5 elements each 
			with upto four leftover elements
			sort in dec order each 5 element sequence
			let M be the sequence of medians of the 5 element sets
			m = select_kth_largest(ceil(n(M)/2), M, n/5);
			let S1, S2 and S3 be the sequences of elements in S 
			greater than, equal to and less than m respectively.
			if n(S1) >=k then return select_kth_largest(k, S1, n(S1));
			else
				if (n(S1) + n(S2) >= k) then return m
				else 
			return select_kth_largest (k - n(S1) - n(S2), S3);
		
		*/
  int n_M, n_S1, n_S2, n_S3; /* number of elements in M, S1, S2 and S3 resp. */
  int *S1, *S3; /* the other arrays */
  int m; /* the median element */
  int i, leftover, ret;

  if (n < 50)
    return kth_largest_qs(k, S, n);
  /* Use quicksort to sort the array S and return the kth largest element */
    
  leftover = n % 5; /* upto four leftover elements */
  if (leftover != 0)
  { /* then pad the remaining elements with min. negative values */
    for (i=n; i< n + 5 - leftover; i++)
      S[i] = INT_MIN; /* number of leftover elements */
             /* INT_MIN is defined for each system in /usr/include/limits.h */
  }
  

  /* after padding the remaining array, sort the 5 element sequence */
  n_M = ceil(n, 5); /* number of elements in M */

  for(i=0; i< n_M; i++)
  { 
    sort_5elements(&S[5*i]); /* beginning element */
  }
   /* 5 element sequences are sorted */
/*
  display_array(S, ceil(n,5)*5);
*/
   /* size of padded array is ceil(n,5)*5 */
  S1 = (int *) malloc ((3*n/4) * sizeof(int)); /* allocate S1 */
  S3 = (int *) malloc ((3*n/4) * sizeof(int)); /* allocate S3 */
  if((S1 == (int *) NULL) || (S3 == (int *) NULL)) 
  {
    perror("S1 or S3 malloc error");
    exit(1);
  }
  for (i=0; i< n_M; i++)
    M[i] = S[middle(i)]; /* fill up the median array */
  m = select_kth_largest(ceil(n_M,2), M, n_M); /* calculate the median element*/
  /* construct S1, S2, and S3 as sequences of elements in S greater than,  
	equal to and less than m. Don't need a separate S2 array. */
  /* initialize the count of elements in S1, S2, S3 */
  n_S1 = n_S2 = n_S3 = 0;
  /* go through every element in S */
  for (i = 0; i < n; i++)
  {
    if(S[i] > m) S1[n_S1++] = S[i];       /* goes to S1 */
    else if (S[i] < m) S3[n_S3++] = S[i]; /* goes to S3 */
         else n_S2++; /* S2 count incremented goes to S2 */
  } 
  /* now we have S1, and S3 */

  if(n_S1 >= k)  /* S1 has the elements greater than m and there are
	greater than k elements, so its bound to be in this section */
  { /* free memory */
    /* don't need S3 */
    free(S3);
    ret =  select_kth_largest(k, S1, n_S1);
    free(S1); /* before returning clean up S1 */
    return ret;
  }
  else
  {
    if(n_S1 + n_S2 >= k) /* its not in S1, but its in S2 */
    { 
      /* free memory */
      /* don't need S1 and S3 */
      free(S1);
      free(S3);
      return m; /* the median that we had calculated earlier */
    }
    else /* its in S3 */
    {
      /* free memory */
      /* don't need S1 */
      free(S1);
      ret =  select_kth_largest(k - n_S1 - n_S2, S3, n_S3);
      free(S3); /* before returning clean up S3 */ 
      return ret;
    } 
  } 
}


/**************************************************************************
** Function   : interchange
** Parameters : two integer pointers a, and b
** Description: interchanges the contents of a and b.
** Returns    : nothing
***************************************************************************/
void interchange(int *a, int *b)
{
  TAU_PROFILE("void interchange(int *, int *)", " ", TAU_USER);
 /* interchanges the contents of the two variables containing integers. */
int temp; 

  temp = *a;
  *a = *b;
  *b = temp;
}

/**************************************************************************
** Function   : setup
** Parameters : array to be initialized
** Description: assigns values to elements in the array used for finding 
**		the kth largest element.
** Returns    : nothing
***************************************************************************/
void setup(int *arr)
{
  TAU_PROFILE("void setup(int *)", " ", TAU_USER);

int i;

/* setup */
  arr[0] = 26;
  arr[1] = 5;
  arr[2] = 37;
  arr[3] = 1;
  arr[4] = 61;
  arr[5] = 11;
  arr[6] = 59;
  arr[7] = 15;
  arr[8] = 48;
  arr[9] = 19;
  if (size > 10)
  {
    for (i=10; i< size; i++)
      arr[i] = arr[i%10];
  }
  /* Uses the first ten values repeatedly and fills the array */
}

/**************************************************************************
** Function   : quicksort
** Parameters : array to be sorted and lower and upper limits m and n resp.
** Description: uses quicksort recursively to sort elements in O(nlog n) 
**		time complexity in decreasing order..
** Returns    : nothing
***************************************************************************/
/* quick sort */
void quicksort(int *arr, int m, int n)
{
  TAU_PROFILE("void quicksort(int *, int, int)", " ", TAU_USER);
 /* sort the array in decreasing order */

  TAU_EVENT(qsize, n);

int k; /* control key */
int i, j;

/* k is chosen as the control key and i and j are chosen such that at any time, 
	arr[l] >= k for l < i and arr[l] <= k for l > j. It is 
	assumed that arr[m] >= arr[n+1] */

/*
  printf("quicksort %d %d\n [", m, n);
  for(i=m; i<n; i++)
    printf(" %d ", arr[i]);
  printf("]\n");
*/
 
  if(m < n)
  {
    i = m;  /* lower index */
    j = n+1;
    k = arr[m]; /* control key */

    do 
    {
      do 
      { 
        i = i+1;
      } while (arr[i] > k);  /* Decreasing order for largest element first */
      do
      {
        j = j - 1;
      } while (arr[j] < k); /* Decreasing order */

      if (i < j)
        interchange(&arr[i], &arr[j]);
    } while (i < j);
    interchange(&arr[m], &arr[j]);  /* pivot */
    quicksort(arr, m, j - 1);       /* left portion sorted */
    quicksort(arr, j + 1, n);	    /* right side sorted - so array is sorted */
  } /*if */
}

/**************************************************************************
** Function   : sort_5elements
** Parameters : array of 5 elements to be sorted 
** Description: sorts the 5 elements in decreasing order  
** Returns    : nothing
***************************************************************************/
void sort_5elements(int *arr)
{
  TAU_PROFILE("void sort_5elements(int *)", " ", TAU_USER);

  //Dump this function's values every time we reach 100000 calls.
  static int counter = 0;
  counter++;
  if(counter == 100000){
    const char **inFuncs = (const char **) malloc(sizeof(const char *) * 2);
    inFuncs[0] = "void sort_5elements(int *)";
    TAU_DUMP_FUNC_VALS_INCR(inFuncs, 1);
    counter = 0;
  }
    

 /* sort the first five elements of the array arr */
  quicksort(arr, 0, 4); /* could be done by if statements too - but this way
	 		its easier to extend it for 7 element based select */
   
}

/**************************************************************************
** Function   : kth_largest_qs
** Parameters : k for kth largest, array to be sorted  and size of array
** Description: sorts the array using quicksort and finds the kth largest 
**		element
** Returns    : kth largest element
***************************************************************************/
int kth_largest_qs(int k, int *arr, int size)
{
  TAU_PROFILE("int kth_largest_qs(int, int *, int)", " ", TAU_USER);
 /* first we sort the array and then return the kth largest element */

  quicksort(arr, 0, size - 1); /* sort the array */
  return arr[k-1]; /* return the kth largest */
}

/**************************************************************************
** Function   : display_array
** Parameters : array and size of array
** Description: for debugging, prints contents of the array
** Returns    : nothing
***************************************************************************/
void display_array(int *A, int nelems)
{
  TAU_PROFILE("void display_array(int *, int)", " ", TAU_USER);

  int i;
  
  for(i=0; i < nelems; i++)
  {
    printf("A[%d] = %d\n", i, A[i]);
  }
}

/* utility functions */

/**************************************************************************
** Function   : floor
** Parameters : numerator and denominator 
** Description: calculates the floor of num/den 
** Returns    : floor 
***************************************************************************/
int floor (int num, int den)
{
  TAU_PROFILE("int floor(int, int)", " ", TAU_USER);
 
  return num / den;
}

/**************************************************************************
** Function   : ceil 
** Parameters : numerator and denominator 
** Description: calculates the ceiling of num/den
** Returns    : ceiling 
***************************************************************************/
int ceil (int num, int den)
{
  TAU_PROFILE("int ceil(int, int)", " ", TAU_USER);

  return  (num % den > 0) ? (num / den + 1) : (num / den);
}



/**************************************************************************
** Function   : main
** Parameters : command line parameters. 
** Description: Usage : main [<no. of elements>] [<k -for kth largest elt>]
**		Calculates kth largest element using two different algorithms
**		and returns the value and the time statistics for the two.
** Returns    : nothing
***************************************************************************/
int main(int argc, char **argv)
{
  TAU_PROFILE("int main(int, char **)", " ", TAU_DEFAULT);
  TAU_INIT(&argc, &argv); 
#ifndef TAU_MPI
  TAU_PROFILE_SET_NODE(0);
#endif /* TAU_MPI */

  int numOfFunctions;
  const char ** functionList;

  TAU_GET_FUNC_NAMES(functionList, numOfFunctions);

  for(int i=0;i<numOfFunctions;i++){
    cout << "This function names so far are: " << functionList[i] << endl;
  }

  TAU_DB_DUMP_INCR();
  TAU_DUMP_FUNC_NAMES();

  int numOfCounters;
  const char ** counterList;

  TAU_GET_COUNTER_NAMES(counterList, numOfCounters);

  for(int j=0;j<numOfCounters;j++){
    cout << "The counter names so far are: " << counterList[j] << endl;
  }

int klarge, k;
struct timeval tp1, tp2;
float time_taken;
int *A;


  /* extract the size of the array and k from the command line parameters */
  if (argc > 1)
    size = atoi(argv[1]);
  else
  {
    size = DEFAULT_SIZE;
    printf(" Usage : main [<no. of elements>] [<k -for kth largest elt>] \n");
    printf(" Calculates kth largest element using two different algorithms\n"); 
    printf(" and returns the value and the time statistics for the two.\n");
  }

  if (argc > 2)
    k = atoi(argv[2]); /* kth largest */
  else
    k = DEFAULT_K;     
  
  if (k > size) 
  {
    printf("ERROR: Please specify a value for k (%d) that is less than the array size (%d)\n",
	k, size);
    exit(0);
  }

/* there could be upto 4 leftover elements */
  A = (int *) malloc((size + 4) * sizeof(int)); /* allocate the array */
  if (A == (int *) NULL)
  {
    perror("Cannot malloc the size of array");
    exit(1);
  }
  M = (int *) malloc(ceil(size,5)*sizeof(int)); /*allocate memory for Median*/
/* its ok to recycle this array so its allocated here instead of doing it 
   in select_kth_largest */
  if (M == (int *) NULL)
  {
    perror("Cannot malloc M array"); /* its ok to recycle this array so its allocated here instead of doing it in select_kth_largest */
    exit(1);
  }
/* setup */
  setup(A);

/*
  display_array(A,size);
*/
  gettimeofday(&tp1, NULL);  /* timing info. */
  klarge = select_kth_largest(k, A, size); /* using SELECT O(n) algo. */
  gettimeofday(&tp2, NULL);  /* timing info. */
  printf("****************************************************\n");
  printf("Using select_kth_largest, size %d, %d th largest element = %d\n", size,k, klarge);
  time_taken = (tp2.tv_sec - tp1.tv_sec) + (tp2.tv_usec - tp1.tv_usec) * 1e-6;
  printf("Time taken (wall clock) = %f secs\n", time_taken);
  printf("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n");

/* Now calculate the kth largest element in A using the same array but 
   the "quick and dirty" quicksort O(nlog n) algorithm */

  gettimeofday(&tp1, NULL); /* timing info */

  klarge = kth_largest_qs(k, A, size); 
/* calculates the kth largest element of A */

  gettimeofday(&tp2, NULL);

/* print results */

  printf("Using quicksort,          size %d, %d th largest element = %d\n", size, k, klarge);
  time_taken = (tp2.tv_sec - tp1.tv_sec) + (tp2.tv_usec - tp1.tv_usec) * 1e-6;
  printf("Time taken (wall clock) = %f secs\n", time_taken);
/*  printf("%d 	%f\n", size, time_taken); */

  const char **inFuncs;
  /* The first dimension is functions, and the second dimension is counters */
  double **counterExclusiveValues;
  double **counterInclusiveValues;
  int *numOfCalls;
  int *numOfSubRoutines;
  const char **counterNames;
  int numOfCouns;

  TAU_GET_FUNC_NAMES(functionList, numOfFunctions);

  /* We are only interested in the first two routines that are executing in 
     this context. So, we allocate space for two routine names and get the 
     performance data for these two routines at runtime. */
  if(numOfFunctions >=2 ){ 
    inFuncs = (const char **) malloc(sizeof(const char *) * 2);

    inFuncs[0] = functionList[0];
    inFuncs[1] = functionList[1];

    //Just to show consistency.
    TAU_DB_DUMP();

    TAU_GET_FUNC_VALS(inFuncs, 2,
		      counterExclusiveValues,
		      counterInclusiveValues,
		      numOfCalls,
		      numOfSubRoutines,
		      counterNames,
		      numOfCouns);

    TAU_DUMP_FUNC_VALS_INCR(inFuncs, 2);
    
    
  cout << "@@@@@@@@@@@@@@@" << endl;
  
  cout << "The number of counters is: " << numOfCouns << endl;
  cout << "The first counter is: " << counterNames[0] << endl;

  cout << "The Exclusive value of: " << inFuncs[0]
       << " is: " << counterExclusiveValues[0][0] << endl;
  cout << "The numOfSubRoutines of: " << inFuncs[0]
       << " is: " << numOfSubRoutines[0]
       << endl;


  cout << "The Inclusive value of: " << inFuncs[1]
       << " is: " << counterInclusiveValues[1][0]
       << endl;
  cout << "The numOfCalls of: " << inFuncs[1]
       << " is: " << numOfCalls[1]
       << endl;

  cout << "@@@@@@@@@@@@@@@" << endl;
  }

  TAU_DB_DUMP_INCR();


  const char **eventList;
  int numEvents;
  
  TAU_GET_EVENT_NAMES(eventList, numEvents);

  cout << "numEvents: " << numEvents << endl;
  
  if (numEvents > 0) {
    int *numSamples;
    double *max;
    double *min;
    double *mean;
    double *sumSqr;

    TAU_GET_EVENT_VALS(eventList, numEvents, numSamples, max, min, mean, sumSqr);

    for (int i=0; i<numEvents; i++) {
      cout << "-------------------\n";
      cout << "User Event:        " << eventList[i] << endl;
      cout << "Number of Samples: " << numSamples[i] << endl;
      cout << "Maximum Value:     " << max[i] << endl;
      cout << "Minimum Value:     " << min[i] << endl;
      cout << "Mean Value:        " << mean[i] << endl;
      cout << "Sum Squared:       " << sumSqr[i] << endl;
    }
  }
}




/* EOF klargest.cpp */

