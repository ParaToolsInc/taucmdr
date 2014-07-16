#include <shmem.h>
#include <pshmem.h>
#include <Profile/Profiler.h>
#include <stdio.h>
#include <stddef.h>
int TAUDECL tau_totalnodes(int set_or_get, int value);
static int tau_shmem_tagid_f=0 ; 
#define TAU_SHMEM_TAGID tau_shmem_tagid_f=tau_shmem_tagid_f%250
#define TAU_SHMEM_TAGID_NEXT (++tau_shmem_tagid_f) % 250 


/* This section contains old API that are not part of openshmem.org specification
 *
 */
void pshmem_init (void)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

void pshmem_finalize (void)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

char * pshmem_nodename (void)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

int pshmem_version (int *major, int *minor)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

void * pshmem_malloc (size_t size)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

void pshmem_free (void *ptr)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

void * pshmem_realloc (void *ptr, size_t size)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

void * pshmem_memalign (size_t alignment, size_t size)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

char * psherror (void)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

char * pshmem_error (void)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
    return NULL;
}  

void pshmem_sync_init (long *pSync)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

#ifdef __cplusplus
# include <complex>
# define COMPLEXIFY(T) std::complex<T>
#else /* _cplusplus */
# include <complex.h>
# define COMPLEXIFY(T) T complex
#endif /* __cplusplus */
void pshmem_complexd_put (COMPLEXIFY (double) * dest,
                                 const COMPLEXIFY (double) * src,
                                 size_t nelems, int pe)
{
    TAU_VERBOSE("TAU: WARNING - Deprecated OpenSHMEM routine: %s\n", __FUNCTION__);
}  

/* Old API */


/**********************************************************
   start_pes
 **********************************************************/

void start_pes(int a1)  {

  TAU_PROFILE_TIMER(t,"void start_pes(int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pstart_pes(a1);
  tau_totalnodes(1,_num_pes());
  TAU_PROFILE_SET_NODE(_my_pe());
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_put
 **********************************************************/

void shmem_short_put(short * a1, const short * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_put(short *, const short *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(short)*a3);
   pshmem_short_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(short)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_put
 **********************************************************/

void shmem_int_put(int * a1, const int * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_put(int *, const int *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(int)*a3);
   pshmem_int_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_put
 **********************************************************/

void shmem_long_put(long * a1, const long * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_put(long *, const long *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(long)*a3);
   pshmem_long_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_put
 **********************************************************/

void shmem_longlong_put(long long * a1, const long long * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_put(long long *, const long long *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(long long)*a3);
   pshmem_longlong_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_put
 **********************************************************/

void shmem_longdouble_put(long double * a1, const long double * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_put(long double *, const long double *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(long double)*a3);
   pshmem_longdouble_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long double)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_put
 **********************************************************/

void shmem_double_put(double * a1, const double * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_put(double *, const double *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(double)*a3);
   pshmem_double_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(double)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_complexd_put
 **********************************************************/

void shmem_complexd_put(double _Complex * a1, const double _Complex * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_complexd_put(double _Complex *, const double _Complex *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, a3);
   pshmem_complexd_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_put
 **********************************************************/

void shmem_float_put(float * a1, const float * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_put(float *, const float *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(float)*a3);
   pshmem_float_put(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(float)*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_putmem
 **********************************************************/

void shmem_putmem(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_putmem(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, a3);
   pshmem_putmem(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_put32
 **********************************************************/

void shmem_put32(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_put32(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, 4*a3);
   pshmem_put32(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 4*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_put64
 **********************************************************/

void shmem_put64(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_put64(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, 8*a3);
   pshmem_put64(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 8*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_put128
 **********************************************************/

void shmem_put128(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_put128(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, 16*a3);
   pshmem_put128(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 16*a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_get
 **********************************************************/

void shmem_short_get(short * a1, const short * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_get(short *, const short *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(short)*a3, a4);
   pshmem_short_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(short)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_get
 **********************************************************/

void shmem_int_get(int * a1, const int * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_get(int *, const int *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*a3, a4);
   pshmem_int_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(int)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_get
 **********************************************************/

void shmem_long_get(long * a1, const long * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_get(long *, const long *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*a3, a4);
   pshmem_long_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(long)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_get
 **********************************************************/

void shmem_longlong_get(long long * a1, const long long * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_get(long long *, const long long *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*a3, a4);
   pshmem_longlong_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(long long)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_get
 **********************************************************/

void shmem_longdouble_get(long double * a1, const long double * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_get(long double *, const long double *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long double)*a3, a4);
   pshmem_longdouble_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(long double)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_get
 **********************************************************/

void shmem_double_get(double * a1, const double * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_get(double *, const double *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(double)*a3, a4);
   pshmem_double_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(double)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_get
 **********************************************************/

void shmem_float_get(float * a1, const float * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_get(float *, const float *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(float)*a3, a4);
   pshmem_float_get(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(float)*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_getmem
 **********************************************************/

void shmem_getmem(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_getmem(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), a3, a4);
   pshmem_getmem(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_get32
 **********************************************************/

void shmem_get32(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_get32(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 4*a3, a4);
   pshmem_get32(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, 4*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_get64
 **********************************************************/

void shmem_get64(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_get64(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 8*a3, a4);
   pshmem_get64(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, 8*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_get128
 **********************************************************/

void shmem_get128(void * a1, const void * a2, size_t a3, int a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_get128(void *, const void *, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 16*a3, a4);
   pshmem_get128(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, 16*a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_char_p
 **********************************************************/

void shmem_char_p(char * a1, char a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_char_p(char *, char, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(char)*1);
   pshmem_char_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(char)*1, a3);
  TAU_PROFILE_STOP(t);
}

/**********************************************************
   shmem_short_p
 **********************************************************/

void shmem_short_p(short * a1, short a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_p(short *, short, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(short)*1);
   pshmem_short_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(short)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_p
 **********************************************************/

void shmem_int_p(int * a1, int a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_p(int *, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(int)*1);
   pshmem_int_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_p
 **********************************************************/

void shmem_long_p(long * a1, long a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_p(long *, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long)*1);
   pshmem_long_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_p
 **********************************************************/

void shmem_longlong_p(long long * a1, long long a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_p(long long *, long long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long long)*1);
   pshmem_longlong_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_p
 **********************************************************/

void shmem_float_p(float * a1, float a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_p(float *, float, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(float)*1);
   pshmem_float_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(float)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_p
 **********************************************************/

void shmem_double_p(double * a1, double a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_p(double *, double, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(double)*1);
   pshmem_double_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(double)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_p
 **********************************************************/

void shmem_longdouble_p(long double * a1, long double a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_p(long double *, long double, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long double)*1);
   pshmem_longdouble_p(a1, a2, a3);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long double)*1, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_char_g
 **********************************************************/

char shmem_char_g(char * a1, int a2)  {

  char retval = 0;
  TAU_PROFILE_TIMER(t,"char shmem_char_g(char *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(char)*1, a2);
  retval  =   pshmem_char_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(char)*1);
  TAU_PROFILE_STOP(t);
  return retval;
}


/**********************************************************
   shmem_short_g
 **********************************************************/

short shmem_short_g(short * a1, int a2)  {

  short retval = 0;
  TAU_PROFILE_TIMER(t,"short shmem_short_g(short *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(short)*1, a2);
  retval  =   pshmem_short_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(short)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_int_g
 **********************************************************/

int shmem_int_g(int * a1, int a2)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_int_g(int *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*1, a2);
  retval  =   pshmem_int_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(int)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_long_g
 **********************************************************/

long shmem_long_g(long * a1, int a2)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_long_g(long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*1, a2);
  retval  =   pshmem_long_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(long)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longlong_g
 **********************************************************/

long long shmem_longlong_g(long long * a1, int a2)  {

  long long retval = 0;
  TAU_PROFILE_TIMER(t,"long long shmem_longlong_g(long long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*1, a2);
  retval  =   pshmem_longlong_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(long long)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_float_g
 **********************************************************/

float shmem_float_g(float * a1, int a2)  {

  float retval = 0;
  TAU_PROFILE_TIMER(t,"float shmem_float_g(float *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(float)*1, a2);
  retval  =   pshmem_float_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(float)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_double_g
 **********************************************************/

double shmem_double_g(double * a1, int a2)  {

  double retval = 0;
  TAU_PROFILE_TIMER(t,"double shmem_double_g(double *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(double)*1, a2);
  retval  =   pshmem_double_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(double)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longdouble_g
 **********************************************************/

long double shmem_longdouble_g(long double * a1, int a2)  {

  long double retval = 0;
  TAU_PROFILE_TIMER(t,"long double shmem_longdouble_g(long double *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long double)*1, a2);
  retval  =   pshmem_longdouble_g(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(long double)*1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_double_iput
 **********************************************************/

void shmem_double_iput(double * a1, const double * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_iput(double *, const double *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(double)*a5);
   pshmem_double_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(double)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_iput
 **********************************************************/

void shmem_float_iput(float * a1, const float * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_iput(float *, const float *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(float)*a5);
   pshmem_float_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(float)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_iput
 **********************************************************/

void shmem_int_iput(int * a1, const int * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_iput(int *, const int *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(int)*a5);
   pshmem_int_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iput32
 **********************************************************/

void shmem_iput32(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iput32(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, 4*a5);
   pshmem_iput32(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 4*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iput64
 **********************************************************/

void shmem_iput64(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iput64(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, 8*a5);
   pshmem_iput64(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 8*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iput128
 **********************************************************/

void shmem_iput128(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iput128(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, 16*a5);
   pshmem_iput128(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 16*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_iput
 **********************************************************/

void shmem_long_iput(long * a1, const long * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_iput(long *, const long *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(long)*a5);
   pshmem_long_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_iput
 **********************************************************/

void shmem_longdouble_iput(long double * a1, const long double * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_iput(long double *, const long double *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(long double)*a5);
   pshmem_longdouble_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long double)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_iput
 **********************************************************/

void shmem_longlong_iput(long long * a1, const long long * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_iput(long long *, const long long *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(long long)*a5);
   pshmem_longlong_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_iput
 **********************************************************/

void shmem_short_iput(short * a1, const short * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_iput(short *, const short *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a6, sizeof(short)*a5);
   pshmem_short_iput(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(short)*a5, a6);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_iget
 **********************************************************/

void shmem_double_iget(double * a1, const double * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_iget(double *, const double *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(double)*a5, a6);
   pshmem_double_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(double)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_iget
 **********************************************************/

void shmem_float_iget(float * a1, const float * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_iget(float *, const float *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(float)*a5, a6);
   pshmem_float_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(float)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_iget
 **********************************************************/

void shmem_int_iget(int * a1, const int * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_iget(int *, const int *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*a5, a6);
   pshmem_int_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(int)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iget32
 **********************************************************/

void shmem_iget32(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iget32(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 4*a5, a6);
   pshmem_iget32(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, 4*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iget64
 **********************************************************/

void shmem_iget64(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iget64(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 8*a5, a6);
   pshmem_iget64(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, 8*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_iget128
 **********************************************************/

void shmem_iget128(void * a1, const void * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_iget128(void *, const void *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 16*a5, a6);
   pshmem_iget128(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, 16*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_iget
 **********************************************************/

void shmem_long_iget(long * a1, const long * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_iget(long *, const long *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*a5, a6);
   pshmem_long_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(long)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_iget
 **********************************************************/

void shmem_longdouble_iget(long double * a1, const long double * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_iget(long double *, const long double *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long double)*a5, a6);
   pshmem_longdouble_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(long double)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_iget
 **********************************************************/

void shmem_longlong_iget(long long * a1, const long long * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_iget(long long *, const long long *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*a5, a6);
   pshmem_longlong_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(long long)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_iget
 **********************************************************/

void shmem_short_iget(short * a1, const short * a2, ptrdiff_t a3, ptrdiff_t a4, size_t a5, int a6)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_iget(short *, const short *, ptrdiff_t, ptrdiff_t, size_t, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(short)*a5, a6);
   pshmem_short_iget(a1, a2, a3, a4, a5, a6);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a6, sizeof(short)*a5);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_barrier_all
 **********************************************************/

void shmem_barrier_all()  {

  TAU_PROFILE_TIMER(t,"void shmem_barrier_all(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_barrier_all();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_barrier
 **********************************************************/

void shmem_barrier(int a1, int a2, int a3, long * a4)  {

  TAU_PROFILE_TIMER(t,"void shmem_barrier(int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_barrier(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_fence
 **********************************************************/

void shmem_fence()  {

  TAU_PROFILE_TIMER(t,"void shmem_fence(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_fence();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_quiet
 **********************************************************/

void shmem_quiet()  {

  TAU_PROFILE_TIMER(t,"void shmem_quiet(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_quiet();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_pe_accessible
 **********************************************************/

int shmem_pe_accessible(int a1)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_pe_accessible(int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_pe_accessible(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_addr_accessible
 **********************************************************/

int shmem_addr_accessible(void * a1, int a2)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_addr_accessible(void *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_addr_accessible(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_ptr
 **********************************************************/

#if 0
// 
// WARNING: Uncommenting this may break OpenSHMEM 10e
// We should look at this further...
// 
void * shmem_ptr(void * a1, int a2)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void * shmem_ptr(void *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_ptr(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}
#endif


/**********************************************************
   shmalloc
 **********************************************************/

void * shmalloc(size_t a1)  
{
  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shmalloc(size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmalloc(a1);
  TAU_PROFILE_STOP(t);
  return retval;
}


/**********************************************************
   shfree
 **********************************************************/

void shfree(void * a1)  {

  TAU_PROFILE_TIMER(t,"void shfree(void *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshfree(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shrealloc
 **********************************************************/

void * shrealloc(void * a1, size_t a2)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shrealloc(void *, size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshrealloc(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmemalign
 **********************************************************/

void * shmemalign(size_t a1, size_t a2)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shmemalign(size_t, size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmemalign(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}

/**********************************************************
   shmem_short_wait_until
 **********************************************************/

void shmem_short_wait_until(short * a1, int a2, short a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_wait_until(short *, int, short) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_wait_until(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_wait_until
 **********************************************************/

void shmem_int_wait_until(int * a1, int a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_wait_until(int *, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_wait_until(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_wait_until
 **********************************************************/

void shmem_long_wait_until(long * a1, int a2, long a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_wait_until(long *, int, long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_wait_until(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_wait_until
 **********************************************************/

void shmem_longlong_wait_until(long long * a1, int a2, long long a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_wait_until(long long *, int, long long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_wait_until(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_wait_until
 **********************************************************/

void shmem_wait_until(long * a1, int a2, long a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_wait_until(long *, int, long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_wait_until(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_wait
 **********************************************************/

void shmem_short_wait(short * a1, short a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_wait(short *, short) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_wait(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_wait
 **********************************************************/

void shmem_int_wait(int * a1, int a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_wait(int *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_wait(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_wait
 **********************************************************/

void shmem_long_wait(long * a1, long a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_wait(long *, long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_wait(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_wait
 **********************************************************/

void shmem_longlong_wait(long long * a1, long long a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_wait(long long *, long long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_wait(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_wait
 **********************************************************/

void shmem_wait(long * a1, long a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_wait(long *, long) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_wait(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_swap
 **********************************************************/

int shmem_int_swap(int * a1, int a2, int a3)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_int_swap(int *, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*1, a3);
  retval  =   pshmem_int_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(int)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(int)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_long_swap
 **********************************************************/

long shmem_long_swap(long * a1, long a2, int a3)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_long_swap(long *, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*1, a3);
  retval  =   pshmem_long_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longlong_swap
 **********************************************************/

long long shmem_longlong_swap(long long * a1, long long a2, int a3)  {

  long long retval = 0;
  TAU_PROFILE_TIMER(t,"long long shmem_longlong_swap(long long *, long long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*1, a3);
  retval  =   pshmem_longlong_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(long long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_float_swap
 **********************************************************/

float shmem_float_swap(float * a1, float a2, int a3)  {

  float retval = 0;
  TAU_PROFILE_TIMER(t,"float shmem_float_swap(float *, float, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(float)*1, a3);
  retval  =   pshmem_float_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(float)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(float)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(float)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_double_swap
 **********************************************************/

double shmem_double_swap(double * a1, double a2, int a3)  {

  double retval = 0;
  TAU_PROFILE_TIMER(t,"double shmem_double_swap(double *, double, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(double)*1, a3);
  retval  =   pshmem_double_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(double)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(double)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(double)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_swap
 **********************************************************/

long shmem_swap(long * a1, long a2, int a3)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_swap(long *, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), 1, a3);
  retval  =   pshmem_swap(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, 1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, 1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), 1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_int_cswap
 **********************************************************/

int shmem_int_cswap(int * a1, int a2, int a3, int a4)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_int_cswap(int *, int, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*1, a4);
  retval  =   pshmem_int_cswap(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(int)*1);
  if (retval == a2) { 
    TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(int)*1);
    TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*1, a4);
  }
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_long_cswap
 **********************************************************/

long shmem_long_cswap(long * a1, long a2, long a3, int a4)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_long_cswap(long *, long, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*1, a4);
  retval  =   pshmem_long_cswap(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(long)*1);
  if (retval == a2) { 
    TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(long)*1);
    TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*1, a4);
  }
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longlong_cswap
 **********************************************************/

long long shmem_longlong_cswap(long long * a1, long long a2, long long a3, int a4)  {

  long long retval = 0;
  TAU_PROFILE_TIMER(t,"long long shmem_longlong_cswap(long long *, long long, long long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*1, a4);
  retval  =   pshmem_longlong_cswap(a1, a2, a3, a4);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a4, sizeof(long long)*1);
  if (retval == a2) { 
    TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a4, sizeof(long long)*1);
    TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*1, a4);
  }
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_int_fadd
 **********************************************************/

int shmem_int_fadd(int * a1, int a2, int a3)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_int_fadd(int *, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*1, a3);
  retval  =   pshmem_int_fadd(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(int)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(int)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_long_fadd
 **********************************************************/

long shmem_long_fadd(long * a1, long a2, int a3)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_long_fadd(long *, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*1, a3);
  retval  =   pshmem_long_fadd(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longlong_fadd
 **********************************************************/

long long shmem_longlong_fadd(long long * a1, long long a2, int a3)  {

  long long retval = 0;
  TAU_PROFILE_TIMER(t,"long long shmem_longlong_fadd(long long *, long long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*1, a3);
  retval  =   pshmem_longlong_fadd(a1, a2, a3);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a3, sizeof(long long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a3, sizeof(long long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*1, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_int_finc
 **********************************************************/

int shmem_int_finc(int * a1, int a2)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_int_finc(int *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(int)*1, a2);
  retval  =   pshmem_int_finc(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(int)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a2, sizeof(int)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(int)*1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_long_finc
 **********************************************************/

long shmem_long_finc(long * a1, int a2)  {

  long retval = 0;
  TAU_PROFILE_TIMER(t,"long shmem_long_finc(long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long)*1, a2);
  retval  =   pshmem_long_finc(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a2, sizeof(long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long)*1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_longlong_finc
 **********************************************************/

long long shmem_longlong_finc(long long * a1, int a2)  {

  long long retval = 0;
  TAU_PROFILE_TIMER(t,"long long shmem_longlong_finc(long long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  TAU_TRACE_SENDMSG_REMOTE(TAU_SHMEM_TAGID_NEXT, Tau_get_node(), sizeof(long long)*1, a2);
  retval  =   pshmem_longlong_finc(a1, a2);
  TAU_TRACE_RECVMSG(TAU_SHMEM_TAGID, a2, sizeof(long long)*1);
  TAU_TRACE_SENDMSG(TAU_SHMEM_TAGID_NEXT, a2, sizeof(long long)*1);
  TAU_TRACE_RECVMSG_REMOTE(TAU_SHMEM_TAGID, Tau_get_node(), sizeof(long long)*1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_int_add
 **********************************************************/

void shmem_int_add(int * a1, int a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_add(int *, int, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_add(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_add
 **********************************************************/

void shmem_long_add(long * a1, long a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_add(long *, long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_add(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_add
 **********************************************************/

void shmem_longlong_add(long long * a1, long long a2, int a3)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_add(long long *, long long, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_add(a1, a2, a3);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_inc
 **********************************************************/

void shmem_int_inc(int * a1, int a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_inc(int *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_inc(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_inc
 **********************************************************/

void shmem_long_inc(long * a1, int a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_inc(long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_inc(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_inc
 **********************************************************/

void shmem_longlong_inc(long long * a1, int a2)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_inc(long long *, int) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_inc(a1, a2);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_clear_cache_inv
 **********************************************************/

void shmem_clear_cache_inv()  {

  TAU_PROFILE_TIMER(t,"void shmem_clear_cache_inv(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_clear_cache_inv();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_set_cache_inv
 **********************************************************/

void shmem_set_cache_inv()  {

  TAU_PROFILE_TIMER(t,"void shmem_set_cache_inv(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_set_cache_inv();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_clear_cache_line_inv
 **********************************************************/

void shmem_clear_cache_line_inv(void * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_clear_cache_line_inv(void *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_clear_cache_line_inv(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_set_cache_line_inv
 **********************************************************/

void shmem_set_cache_line_inv(void * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_set_cache_line_inv(void *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_set_cache_line_inv(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_udcflush
 **********************************************************/

void shmem_udcflush()  {

  TAU_PROFILE_TIMER(t,"void shmem_udcflush(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_udcflush();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_udcflush_line
 **********************************************************/

void shmem_udcflush_line(void * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_udcflush_line(void *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_udcflush_line(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_complexd_sum_to_all
 **********************************************************/

void shmem_complexd_sum_to_all(double _Complex * a1, double _Complex * a2, int a3, int a4, int a5, int a6, double _Complex * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_complexd_sum_to_all(double _Complex *, double _Complex *, int, int, int, int, double _Complex *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_complexd_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_complexf_sum_to_all
 **********************************************************/

void shmem_complexf_sum_to_all(float _Complex * a1, float _Complex * a2, int a3, int a4, int a5, int a6, float _Complex * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_complexf_sum_to_all(float _Complex *, float _Complex *, int, int, int, int, float _Complex *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_complexf_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_sum_to_all
 **********************************************************/

void shmem_double_sum_to_all(double * a1, double * a2, int a3, int a4, int a5, int a6, double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_sum_to_all(double *, double *, int, int, int, int, double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_double_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_sum_to_all
 **********************************************************/

void shmem_float_sum_to_all(float * a1, float * a2, int a3, int a4, int a5, int a6, float * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_sum_to_all(float *, float *, int, int, int, int, float *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_float_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_sum_to_all
 **********************************************************/

void shmem_int_sum_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_sum_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_sum_to_all
 **********************************************************/

void shmem_long_sum_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_sum_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_sum_to_all
 **********************************************************/

void shmem_longdouble_sum_to_all(long double * a1, long double * a2, int a3, int a4, int a5, int a6, long double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_sum_to_all(long double *, long double *, int, int, int, int, long double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longdouble_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_sum_to_all
 **********************************************************/

void shmem_longlong_sum_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_sum_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_sum_to_all
 **********************************************************/

void shmem_short_sum_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_sum_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_sum_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_complexd_prod_to_all
 **********************************************************/

void shmem_complexd_prod_to_all(double _Complex * a1, double _Complex * a2, int a3, int a4, int a5, int a6, double _Complex * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_complexd_prod_to_all(double _Complex *, double _Complex *, int, int, int, int, double _Complex *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_complexd_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_complexf_prod_to_all
 **********************************************************/

void shmem_complexf_prod_to_all(float _Complex * a1, float _Complex * a2, int a3, int a4, int a5, int a6, float _Complex * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_complexf_prod_to_all(float _Complex *, float _Complex *, int, int, int, int, float _Complex *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_complexf_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_prod_to_all
 **********************************************************/

void shmem_double_prod_to_all(double * a1, double * a2, int a3, int a4, int a5, int a6, double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_prod_to_all(double *, double *, int, int, int, int, double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_double_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_prod_to_all
 **********************************************************/

void shmem_float_prod_to_all(float * a1, float * a2, int a3, int a4, int a5, int a6, float * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_prod_to_all(float *, float *, int, int, int, int, float *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_float_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_prod_to_all
 **********************************************************/

void shmem_int_prod_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_prod_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_prod_to_all
 **********************************************************/

void shmem_long_prod_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_prod_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_prod_to_all
 **********************************************************/

void shmem_longdouble_prod_to_all(long double * a1, long double * a2, int a3, int a4, int a5, int a6, long double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_prod_to_all(long double *, long double *, int, int, int, int, long double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longdouble_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_prod_to_all
 **********************************************************/

void shmem_longlong_prod_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_prod_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_prod_to_all
 **********************************************************/

void shmem_short_prod_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_prod_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_prod_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_and_to_all
 **********************************************************/

void shmem_int_and_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_and_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_and_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_and_to_all
 **********************************************************/

void shmem_long_and_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_and_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_and_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_and_to_all
 **********************************************************/

void shmem_longlong_and_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_and_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_and_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_and_to_all
 **********************************************************/

void shmem_short_and_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_and_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_and_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_or_to_all
 **********************************************************/

void shmem_int_or_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_or_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_or_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_or_to_all
 **********************************************************/

void shmem_long_or_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_or_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_or_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_or_to_all
 **********************************************************/

void shmem_longlong_or_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_or_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_or_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_or_to_all
 **********************************************************/

void shmem_short_or_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_or_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_or_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_xor_to_all
 **********************************************************/

void shmem_int_xor_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_xor_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_xor_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_xor_to_all
 **********************************************************/

void shmem_long_xor_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_xor_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_xor_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_xor_to_all
 **********************************************************/

void shmem_longlong_xor_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_xor_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_xor_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_xor_to_all
 **********************************************************/

void shmem_short_xor_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_xor_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_xor_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_max_to_all
 **********************************************************/

void shmem_int_max_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_max_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_max_to_all
 **********************************************************/

void shmem_long_max_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_max_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_max_to_all
 **********************************************************/

void shmem_longlong_max_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_max_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_max_to_all
 **********************************************************/

void shmem_short_max_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_max_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_max_to_all
 **********************************************************/

void shmem_longdouble_max_to_all(long double * a1, long double * a2, int a3, int a4, int a5, int a6, long double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_max_to_all(long double *, long double *, int, int, int, int, long double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longdouble_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_max_to_all
 **********************************************************/

void shmem_float_max_to_all(float * a1, float * a2, int a3, int a4, int a5, int a6, float * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_max_to_all(float *, float *, int, int, int, int, float *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_float_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_max_to_all
 **********************************************************/

void shmem_double_max_to_all(double * a1, double * a2, int a3, int a4, int a5, int a6, double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_max_to_all(double *, double *, int, int, int, int, double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_double_max_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_int_min_to_all
 **********************************************************/

void shmem_int_min_to_all(int * a1, int * a2, int a3, int a4, int a5, int a6, int * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_int_min_to_all(int *, int *, int, int, int, int, int *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_int_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_long_min_to_all
 **********************************************************/

void shmem_long_min_to_all(long * a1, long * a2, int a3, int a4, int a5, int a6, long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_long_min_to_all(long *, long *, int, int, int, int, long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_long_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longlong_min_to_all
 **********************************************************/

void shmem_longlong_min_to_all(long long * a1, long long * a2, int a3, int a4, int a5, int a6, long long * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longlong_min_to_all(long long *, long long *, int, int, int, int, long long *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longlong_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_short_min_to_all
 **********************************************************/

void shmem_short_min_to_all(short * a1, short * a2, int a3, int a4, int a5, int a6, short * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_short_min_to_all(short *, short *, int, int, int, int, short *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_short_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_longdouble_min_to_all
 **********************************************************/

void shmem_longdouble_min_to_all(long double * a1, long double * a2, int a3, int a4, int a5, int a6, long double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_longdouble_min_to_all(long double *, long double *, int, int, int, int, long double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_longdouble_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_float_min_to_all
 **********************************************************/

void shmem_float_min_to_all(float * a1, float * a2, int a3, int a4, int a5, int a6, float * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_float_min_to_all(float *, float *, int, int, int, int, float *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_float_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_double_min_to_all
 **********************************************************/

void shmem_double_min_to_all(double * a1, double * a2, int a3, int a4, int a5, int a6, double * a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_double_min_to_all(double *, double *, int, int, int, int, double *, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_double_min_to_all(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_broadcast32
 **********************************************************/

void shmem_broadcast32(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, int a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_broadcast32(void *, const void *, size_t, int, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_broadcast32(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_broadcast64
 **********************************************************/

void shmem_broadcast64(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, int a7, long * a8)  {

  TAU_PROFILE_TIMER(t,"void shmem_broadcast64(void *, const void *, size_t, int, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_broadcast64(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_fcollect32
 **********************************************************/

void shmem_fcollect32(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, long * a7)  {

  TAU_PROFILE_TIMER(t,"void shmem_fcollect32(void *, const void *, size_t, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_fcollect32(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_fcollect64
 **********************************************************/

void shmem_fcollect64(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, long * a7)  {

  TAU_PROFILE_TIMER(t,"void shmem_fcollect64(void *, const void *, size_t, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_fcollect64(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_collect32
 **********************************************************/

void shmem_collect32(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, long * a7)  {

  TAU_PROFILE_TIMER(t,"void shmem_collect32(void *, const void *, size_t, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_collect32(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_collect64
 **********************************************************/

void shmem_collect64(void * a1, const void * a2, size_t a3, int a4, int a5, int a6, long * a7)  {

  TAU_PROFILE_TIMER(t,"void shmem_collect64(void *, const void *, size_t, int, int, int, long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_collect64(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_set_lock
 **********************************************************/

void shmem_set_lock(long * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_set_lock(long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_set_lock(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_clear_lock
 **********************************************************/

void shmem_clear_lock(long * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_clear_lock(long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_clear_lock(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_test_lock
 **********************************************************/

int shmem_test_lock(long * a1)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_test_lock(long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_test_lock(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_init
 **********************************************************/

void shmem_init()  {

  TAU_PROFILE_TIMER(t,"void shmem_init(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_init();
  tau_totalnodes(1,_num_pes());
  TAU_PROFILE_SET_NODE(_my_pe());
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_finalize
 **********************************************************/

void shmem_finalize()  {

  TAU_PROFILE_TIMER(t,"void shmem_finalize(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_finalize();
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_my_pe
 **********************************************************/

int shmem_my_pe()  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_my_pe(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   _my_pe();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_num_pes
 **********************************************************/

int shmem_num_pes()  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_num_pes(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   _num_pes();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_n_pes
 **********************************************************/

int shmem_n_pes()  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_n_pes(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   _num_pes();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_nodename
 **********************************************************/

char * shmem_nodename()  {

  char * retval = 0;
  TAU_PROFILE_TIMER(t,"char *shmem_nodename(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_nodename();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_version
 **********************************************************/

int shmem_version(int * a1, int * a2)  {

  int retval = 0;
  TAU_PROFILE_TIMER(t,"int shmem_version(int *, int *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_version(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


#ifdef TAU_OPENSHMEM_EXTENSION_1
/**********************************************************
   shmem_malloc
 **********************************************************/

void * shmem_malloc(size_t a1)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shmem_malloc(size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_malloc(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_free
 **********************************************************/

void shmem_free(void * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_free(void *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_free(a1);
  TAU_PROFILE_STOP(t);

}


/**********************************************************
   shmem_realloc
 **********************************************************/

void * shmem_realloc(void * a1, size_t a2)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shmem_realloc(void *, size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_realloc(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   shmem_memalign
 **********************************************************/

void * shmem_memalign(size_t a1, size_t a2)  {

  void * retval = 0;
  TAU_PROFILE_TIMER(t,"void *shmem_memalign(size_t, size_t) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_memalign(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}
#endif /* TAU_OPENSHMEM_EXTENSION_1 */


/**********************************************************
   sherror
 **********************************************************/


char * sherror()  {

  char * retval = 0;
  TAU_PROFILE_TIMER(t,"char *sherror(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   psherror();
  TAU_PROFILE_STOP(t);
  return retval;

}



#ifdef TAU_OPENSHMEM_EXTENSION_1
/**********************************************************
   shmem_error
 **********************************************************/

char * shmem_error()  {

  char * retval = 0;
  TAU_PROFILE_TIMER(t,"char *shmem_error(void) C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =   pshmem_error();
  TAU_PROFILE_STOP(t);
  return retval;

}
#endif /* TAU_OPENSHMEM_EXTENSION_1 */


/**********************************************************
   shmem_sync_init
 **********************************************************/

void shmem_sync_init(long * a1)  {

  TAU_PROFILE_TIMER(t,"void shmem_sync_init(long *) C", "", TAU_USER);
  TAU_PROFILE_START(t);
   pshmem_sync_init(a1);
  TAU_PROFILE_STOP(t);

}

