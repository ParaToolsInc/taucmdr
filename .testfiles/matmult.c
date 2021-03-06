/******************************************************************************
 *   OpenMp Example - Matrix Multiply - C Version
 *   Demonstrates a matrix multiply using OpenMP.
 *
 *   Modified from here:
 *   https://computing.llnl.gov/tutorials/openMP/samples/C/omp_mm.c
 *
 *   For  PAPI_FP_INS, the exclusive count for the event:
 *   for (null) [OpenMP location: file:matmult.c ]
 *   should be  2E+06 / Number of Threads
******************************************************************************/
#include <stdio.h>
#include <stdlib.h>

#ifdef TAU_MPI
int provided;
#include <mpi.h>
/* NOTE: MPI is just used to spawn multiple copies of the kernel to different ranks.
   This is not a parallel implementation */
#endif /* TAU_MPI */

#ifdef PTHREADS
#include <pthread.h>
#include <unistd.h>
#include <errno.h>
/*** NOTE THE ATTR INITIALIZER HERE! ***/
pthread_mutex_t mutexsum;
#endif /* PTHREADS */

#define APP_USE_INLINE_MULTIPLY 1

#ifndef MATRIX_SIZE
#define MATRIX_SIZE 512
#endif

#define NRA MATRIX_SIZE                 /* number of rows in matrix A */
#define NCA MATRIX_SIZE                 /* number of columns in matrix A */
#define NCB MATRIX_SIZE                 /* number of columns in matrix B */


void initialize(double **matrix, int rows, int cols) {
  int i,j;
#pragma omp parallel private(i,j) shared(matrix)
  {
    //set_num_threads();
    /*** Initialize matrices ***/
#pragma omp for nowait
    for (i=0; i<rows; i++) {
      for (j=0; j<cols; j++) {
        matrix[i][j]= i+j;
      }
    }
  }
}

double** allocateMatrix(int rows, int cols) {
  int i;
  double **matrix = (double**)malloc((sizeof(double*)) * rows);
  for (i=0; i<rows; i++) {
    matrix[i] = (double*)malloc((sizeof(double)) * cols);
  }
  return matrix;
}

void freeMatrix(double** matrix, int rows, int cols) {
  int i;
  for (i=0; i<rows; i++) {
    free(matrix[i]);
  }
  free(matrix);
}

double multiply(double a, double b) {
  return a * b;
}

#ifdef TAU_OPENMP
// cols_a and rows_b are the same value
void compute_nested(double **a, double **b, double **c, int rows_a, int cols_a, int cols_b) {
  int i,j,k;
  double tmp = 0.0;
  /*** Do matrix multiply sharing iterations on outer loop ***/
  /*** Display who does which iterations for demonstration purposes ***/
#pragma omp parallel for private(i,j,k) shared(a,b,c)
  for (i=0; i<rows_a; i++) {
    {
      for (k=0; k<cols_a; k++) {
        for(j=0; j<cols_b; j++) {
#ifdef APP_USE_INLINE_MULTIPLY
          c[i][j] += multiply(a[i][k], b[k][j]);
#else
          tmp = a[i][k];
          tmp = tmp * b[k][j];
          c[i][j] += tmp;
#endif
        }
      }
    }
  }
}
#endif

// cols_a and rows_b are the same value
void compute(double **a, double **b, double **c, int rows_a, int cols_a, int cols_b) {
  int i,j,k;
#pragma omp parallel private(i,j,k) shared(a,b,c)
  {
    /*** Do matrix multiply sharing iterations on outer loop ***/
    /*** Display who does which iterations for demonstration purposes ***/
#pragma omp for nowait
    for (i=0; i<rows_a; i++) {
      for(j=0; j<cols_b; j++) {
        for (k=0; k<cols_a; k++) {
#ifdef APP_USE_INLINE_MULTIPLY
          c[i][j] += multiply(a[i][k], b[k][j]);
#else /* APP_USE_INLINE_MULTIPLY */
          c[i][j] += a[i][k] * b[k][j];
#endif /* APP_USE_INLINE_MULTIPLY */
        }
      }
    }
  }   /*** End of parallel region ***/
}

void compute_interchange(double **a, double **b, double **c, int rows_a, int cols_a, int cols_b) {
  int i,j,k;
#pragma omp parallel private(i,j,k) shared(a,b,c)
  {
    /*** Do matrix multiply sharing iterations on outer loop ***/
    /*** Display who does which iterations for demonstration purposes ***/
#pragma omp for nowait
    for (i=0; i<rows_a; i++) {
      for (k=0; k<cols_a; k++) {
        for(j=0; j<cols_b; j++) {
#ifdef APP_USE_INLINE_MULTIPLY
          c[i][j] += multiply(a[i][k], b[k][j]);
#else /* APP_USE_INLINE_MULTIPLY */
          c[i][j] += a[i][k] * b[k][j];
#endif /* APP_USE_INLINE_MULTIPLY */
        }
      }
    }
  }   /*** End of parallel region ***/
}

double do_work(void) {
  double **a,           /* matrix A to be multiplied */
         **b,           /* matrix B to be multiplied */
         **c;           /* result matrix C */
  a = allocateMatrix(NRA, NCA);
  b = allocateMatrix(NCA, NCB);
  c = allocateMatrix(NRA, NCB);

  /*** Spawn a parallel region explicitly scoping all variables ***/

  initialize(a, NRA, NCA);
  initialize(b, NCA, NCB);
  initialize(c, NRA, NCB);

  compute(a, b, c, NRA, NCA, NCB);
#if defined(TAU_OPENMP)
  //if (omp_get_nested()) {
  compute_nested(a, b, c, NRA, NCA, NCB);
  //}
#endif
#ifdef TAU_MPI
  if (provided == MPI_THREAD_MULTIPLE) {
    printf("provided is MPI_THREAD_MULTIPLE\n");
  } else if (provided == MPI_THREAD_FUNNELED) {
    printf("provided is MPI_THREAD_FUNNELED\n");
  }
#endif /* TAU_MPI */
  compute_interchange(a, b, c, NRA, NCA, NCB);

  double result = c[0][1];

  freeMatrix(a, NRA, NCA);
  freeMatrix(b, NCA, NCB);
  freeMatrix(c, NCA, NCB);

  return result;
}

#ifdef PTHREADS
int busy_sleep() {
  int i, sum = 0;
  for (i = 0 ; i < 100000000 ; i++) {
    sum = sum+i;
  }
  return sum;
}

void * threaded_func(void *data)
{
  int rc;
  int sum = 0;
  // compute
  do_work();

#ifdef APP_DO_LOCK_TEST
  // test locking - sampling should catch this
  if ((rc = pthread_mutex_lock(&mutexsum)) != 0)
  {
    errno = rc;
    perror("thread lock error");
    exit(1);
  }
  fprintf(stderr,"Thread 'sleeping'...\n"); fflush(stderr);
  sum += busy_sleep();
  fprintf(stderr,"Thread 'awake'...\n"); fflush(stderr);
  if ((rc = pthread_mutex_unlock(&mutexsum)) != 0)
  {
    errno = rc;
    perror("thread unlock error");
    exit(1);
  }
  pthread_exit((void*) 0);
  //return NULL;
#endif // APP_DO_LOCK_TEST
}
#endif // PTHREADS

int main (int argc, char *argv[])
{

#ifdef PTHREADS
  int ret;
  pthread_attr_t  attr;
  pthread_t       tid1, tid2, tid3;
  pthread_mutexattr_t Attr;
  pthread_mutexattr_init(&Attr);
  pthread_mutexattr_settype(&Attr, PTHREAD_MUTEX_ERRORCHECK);
  if (pthread_mutex_init(&mutexsum, &Attr)) {
    printf("Error while using pthread_mutex_init\n");
  }
#endif /* PTHREADS */

#ifdef TAU_MPI
  int rc = MPI_SUCCESS;
#if defined(PTHREADS)
  rc = MPI_Init_thread(&argc, &argv, MPI_THREAD_MULTIPLE, &provided);
  printf("MPI_Init_thread: provided = %d, MPI_THREAD_MULTIPLE=%d\n", provided, MPI_THREAD_MULTIPLE);
#elif defined(TAU_OPENMP)
  rc = MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);
  printf("MPI_Init_thread: provided = %d, MPI_THREAD_FUNNELED=%d\n", provided, MPI_THREAD_FUNNELED);
#else
  rc = MPI_Init(&argc, &argv);
#endif /* THREADS */
  if (rc != MPI_SUCCESS) {
    char *errorstring;
    int length = 0;
    MPI_Error_string(rc, errorstring, &length);
    printf("Error: MPI_Init failed, rc = %d\n%s\n", rc, errorstring);
    exit(1);
  }
#endif /* TAU_MPI */

#ifdef PTHREADS
  if (ret = pthread_create(&tid1, NULL, threaded_func, NULL) )
  {
    printf("Error: pthread_create (1) fails ret = %d\n", ret);
    exit(1);
  }

  if (ret = pthread_create(&tid2, NULL, threaded_func, NULL) )
  {
    printf("Error: pthread_create (2) fails ret = %d\n", ret);
    exit(1);
  }

  if (ret = pthread_create(&tid3, NULL, threaded_func, NULL) )
  {
    printf("Error: pthread_create (3) fails ret = %d\n", ret);
    exit(1);
  }

#endif /* PTHREADS */

  /* On thread 0: */
  int i;
  //for (i = 0 ; i < 100 ; i++) {
  do_work();
  //}

#ifdef PTHREADS
  if (ret = pthread_join(tid1, NULL) )
  {
    printf("Error: pthread_join (1) fails ret = %d\n", ret);
    exit(1);
  }

  if (ret = pthread_join(tid2, NULL) )
  {
    printf("Error: pthread_join (2) fails ret = %d\n", ret);
    exit(1);
  }

  if (ret = pthread_join(tid3, NULL) )
  {
    printf("Error: pthread_join (3) fails ret = %d\n", ret);
    exit(1);
  }

  pthread_mutex_destroy(&mutexsum);
#endif /* PTHREADS */

#ifdef TAU_MPI
  MPI_Finalize();
#endif /* TAU_MPI */
  printf ("Done.\n");

  return 0;
}
