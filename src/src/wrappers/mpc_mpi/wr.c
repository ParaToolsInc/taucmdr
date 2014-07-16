#include <mpc_mpi.h>
#include <Profile/Profiler.h>
#include <stdio.h>


/**********************************************************
   MPI_Default_error
 **********************************************************/

void   __real_MPI_Default_error(MPI_Comm *  a1, int *  a2, char *  a3, char *  a4, int  a5) ;
void   __wrap_MPI_Default_error(MPI_Comm *  a1, int *  a2, char *  a3, char *  a4, int  a5)  {

  TAU_PROFILE_TIMER(t,"void MPI_Default_error(MPI_Comm *, int *, char *, char *, int)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  __real_MPI_Default_error(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);

}

/* #warning "TAU: Not generating wrapper for function MPI_Return_error"
*/

/**********************************************************
   MPI_Send
 **********************************************************/

int   __real_MPI_Send(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Send(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Send(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Send(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Recv
 **********************************************************/

int   __real_MPI_Recv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Status *  a7) ;
int   __wrap_MPI_Recv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Status *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Recv(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Recv(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Get_count
 **********************************************************/

int   __real_MPI_Get_count(MPI_Status *  a1, MPI_Datatype  a2, int *  a3) ;
int   __wrap_MPI_Get_count(MPI_Status *  a1, MPI_Datatype  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Get_count(MPI_Status *, MPI_Datatype, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Get_count(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Bsend
 **********************************************************/

int   __real_MPI_Bsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Bsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Bsend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Bsend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Ssend
 **********************************************************/

int   __real_MPI_Ssend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Ssend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Ssend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Ssend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Rsend
 **********************************************************/

int   __real_MPI_Rsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Rsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Rsend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Rsend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Buffer_attach
 **********************************************************/

int   __real_MPI_Buffer_attach(void *  a1, int  a2) ;
int   __wrap_MPI_Buffer_attach(void *  a1, int  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Buffer_attach(void *, int)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Buffer_attach(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Buffer_detach
 **********************************************************/

int   __real_MPI_Buffer_detach(void *  a1, int *  a2) ;
int   __wrap_MPI_Buffer_detach(void *  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Buffer_detach(void *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Buffer_detach(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Isend
 **********************************************************/

int   __real_MPI_Isend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Isend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Isend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Isend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Ibsend
 **********************************************************/

int   __real_MPI_Ibsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Ibsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Ibsend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Ibsend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Issend
 **********************************************************/

int   __real_MPI_Issend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Issend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Issend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Issend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Irsend
 **********************************************************/

int   __real_MPI_Irsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Irsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Irsend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Irsend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Irecv
 **********************************************************/

int   __real_MPI_Irecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Irecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Irecv(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Irecv(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Wait
 **********************************************************/

int   __real_MPI_Wait(MPI_Request *  a1, MPI_Status *  a2) ;
int   __wrap_MPI_Wait(MPI_Request *  a1, MPI_Status *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Wait(MPI_Request *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Wait(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Test
 **********************************************************/

int   __real_MPI_Test(MPI_Request *  a1, int *  a2, MPI_Status *  a3) ;
int   __wrap_MPI_Test(MPI_Request *  a1, int *  a2, MPI_Status *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Test(MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Test(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Request_free
 **********************************************************/

int   __real_MPI_Request_free(MPI_Request *  a1) ;
int   __wrap_MPI_Request_free(MPI_Request *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Request_free(MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Request_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Waitany
 **********************************************************/

int   __real_MPI_Waitany(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4) ;
int   __wrap_MPI_Waitany(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Waitany(int, MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Waitany(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Testany
 **********************************************************/

int   __real_MPI_Testany(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_MPI_Testany(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Testany(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Testany(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Waitall
 **********************************************************/

int   __real_MPI_Waitall(int  a1, MPI_Request *  a2, MPI_Status *  a3) ;
int   __wrap_MPI_Waitall(int  a1, MPI_Request *  a2, MPI_Status *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Waitall(int, MPI_Request *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Waitall(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Testall
 **********************************************************/

int   __real_MPI_Testall(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4) ;
int   __wrap_MPI_Testall(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Testall(int, MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Testall(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Waitsome
 **********************************************************/

int   __real_MPI_Waitsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_MPI_Waitsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Waitsome(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Waitsome(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Testsome
 **********************************************************/

int   __real_MPI_Testsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_MPI_Testsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Testsome(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Testsome(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Iprobe
 **********************************************************/

int   __real_MPI_Iprobe(int  a1, int  a2, MPI_Comm  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_MPI_Iprobe(int  a1, int  a2, MPI_Comm  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Iprobe(int, int, MPI_Comm, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Iprobe(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Probe
 **********************************************************/

int   __real_MPI_Probe(int  a1, int  a2, MPI_Comm  a3, MPI_Status *  a4) ;
int   __wrap_MPI_Probe(int  a1, int  a2, MPI_Comm  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Probe(int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Probe(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cancel
 **********************************************************/

int   __real_MPI_Cancel(MPI_Request *  a1) ;
int   __wrap_MPI_Cancel(MPI_Request *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cancel(MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cancel(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Test_cancelled
 **********************************************************/

int   __real_MPI_Test_cancelled(MPI_Status *  a1, int *  a2) ;
int   __wrap_MPI_Test_cancelled(MPI_Status *  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Test_cancelled(MPI_Status *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Test_cancelled(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Send_init
 **********************************************************/

int   __real_MPI_Send_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Send_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Send_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Send_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Bsend_init
 **********************************************************/

int   __real_MPI_Bsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Bsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Bsend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Bsend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Ssend_init
 **********************************************************/

int   __real_MPI_Ssend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Ssend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Ssend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Ssend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Rsend_init
 **********************************************************/

int   __real_MPI_Rsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Rsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Rsend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Rsend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Recv_init
 **********************************************************/

int   __real_MPI_Recv_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_MPI_Recv_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Recv_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Recv_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Start
 **********************************************************/

int   __real_MPI_Start(MPI_Request *  a1) ;
int   __wrap_MPI_Start(MPI_Request *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Start(MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Start(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Startall
 **********************************************************/

int   __real_MPI_Startall(int  a1, MPI_Request *  a2) ;
int   __wrap_MPI_Startall(int  a1, MPI_Request *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Startall(int, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Startall(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Sendrecv
 **********************************************************/

int   __real_MPI_Sendrecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, void *  a6, int  a7, MPI_Datatype  a8, int  a9, int  a10, MPI_Comm  a11, MPI_Status *  a12) ;
int   __wrap_MPI_Sendrecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, void *  a6, int  a7, MPI_Datatype  a8, int  a9, int  a10, MPI_Comm  a11, MPI_Status *  a12)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Sendrecv(void *, int, MPI_Datatype, int, int, void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Sendrecv(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Sendrecv_replace
 **********************************************************/

int   __real_MPI_Sendrecv_replace(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, int  a6, int  a7, MPI_Comm  a8, MPI_Status *  a9) ;
int   __wrap_MPI_Sendrecv_replace(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, int  a6, int  a7, MPI_Comm  a8, MPI_Status *  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Sendrecv_replace(void *, int, MPI_Datatype, int, int, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Sendrecv_replace(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_contiguous
 **********************************************************/

int   __real_MPI_Type_contiguous(int  a1, MPI_Datatype  a2, MPI_Datatype *  a3) ;
int   __wrap_MPI_Type_contiguous(int  a1, MPI_Datatype  a2, MPI_Datatype *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_contiguous(int, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_contiguous(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_vector
 **********************************************************/

int   __real_MPI_Type_vector(int  a1, int  a2, int  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_MPI_Type_vector(int  a1, int  a2, int  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_vector(int, int, int, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_vector(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_hvector
 **********************************************************/

int   __real_MPI_Type_hvector(int  a1, int  a2, MPI_Aint  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_MPI_Type_hvector(int  a1, int  a2, MPI_Aint  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_hvector(int, int, MPI_Aint, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_hvector(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_indexed
 **********************************************************/

int   __real_MPI_Type_indexed(int  a1, int *  a2, int *  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_MPI_Type_indexed(int  a1, int *  a2, int *  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_indexed(int, int *, int *, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_indexed(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_hindexed
 **********************************************************/

int   __real_MPI_Type_hindexed(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_MPI_Type_hindexed(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_hindexed(int, int *, MPI_Aint *, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_hindexed(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_struct
 **********************************************************/

int   __real_MPI_Type_struct(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype *  a4, MPI_Datatype *  a5) ;
int   __wrap_MPI_Type_struct(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype *  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_struct(int, int *, MPI_Aint *, MPI_Datatype *, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_struct(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Address
 **********************************************************/

int   __real_MPI_Address(void *  a1, MPI_Aint *  a2) ;
int   __wrap_MPI_Address(void *  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Address(void *, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Address(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_extent
 **********************************************************/

int   __real_MPI_Type_extent(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_MPI_Type_extent(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_extent(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_extent(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_size
 **********************************************************/

int   __real_MPI_Type_size(MPI_Datatype  a1, int *  a2) ;
int   __wrap_MPI_Type_size(MPI_Datatype  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_size(MPI_Datatype, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_size(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_lb
 **********************************************************/

int   __real_MPI_Type_lb(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_MPI_Type_lb(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_lb(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_lb(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_ub
 **********************************************************/

int   __real_MPI_Type_ub(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_MPI_Type_ub(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_ub(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_ub(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_commit
 **********************************************************/

int   __real_MPI_Type_commit(MPI_Datatype *  a1) ;
int   __wrap_MPI_Type_commit(MPI_Datatype *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_commit(MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_commit(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Type_free
 **********************************************************/

int   __real_MPI_Type_free(MPI_Datatype *  a1) ;
int   __wrap_MPI_Type_free(MPI_Datatype *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Type_free(MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Type_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Get_elements
 **********************************************************/

int   __real_MPI_Get_elements(MPI_Status *  a1, MPI_Datatype  a2, int *  a3) ;
int   __wrap_MPI_Get_elements(MPI_Status *  a1, MPI_Datatype  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Get_elements(MPI_Status *, MPI_Datatype, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Get_elements(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Pack
 **********************************************************/

int   __real_MPI_Pack(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, int *  a6, MPI_Comm  a7) ;
int   __wrap_MPI_Pack(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, int *  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Pack(void *, int, MPI_Datatype, void *, int, int *, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Pack(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Unpack
 **********************************************************/

int   __real_MPI_Unpack(void *  a1, int  a2, int *  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_MPI_Unpack(void *  a1, int  a2, int *  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Unpack(void *, int, int *, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Unpack(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Pack_size
 **********************************************************/

int   __real_MPI_Pack_size(int  a1, MPI_Datatype  a2, MPI_Comm  a3, int *  a4) ;
int   __wrap_MPI_Pack_size(int  a1, MPI_Datatype  a2, MPI_Comm  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Pack_size(int, MPI_Datatype, MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Pack_size(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Barrier
 **********************************************************/

int   __real_MPI_Barrier(MPI_Comm  a1) ;
int   __wrap_MPI_Barrier(MPI_Comm  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Barrier(MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Barrier(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Bcast
 **********************************************************/

int   __real_MPI_Bcast(void *  a1, int  a2, MPI_Datatype  a3, int  a4, MPI_Comm  a5) ;
int   __wrap_MPI_Bcast(void *  a1, int  a2, MPI_Datatype  a3, int  a4, MPI_Comm  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Bcast(void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Bcast(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Gather
 **********************************************************/

int   __real_MPI_Gather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8) ;
int   __wrap_MPI_Gather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Gather(void *, int, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Gather(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Gatherv
 **********************************************************/

int   __real_MPI_Gatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9) ;
int   __wrap_MPI_Gatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Gatherv(void *, int, MPI_Datatype, void *, int *, int *, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Gatherv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Scatter
 **********************************************************/

int   __real_MPI_Scatter(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8) ;
int   __wrap_MPI_Scatter(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Scatter(void *, int, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Scatter(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Scatterv
 **********************************************************/

int   __real_MPI_Scatterv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9) ;
int   __wrap_MPI_Scatterv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Scatterv(void *, int *, int *, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Scatterv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Allgather
 **********************************************************/

int   __real_MPI_Allgather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_MPI_Allgather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Allgather(void *, int, MPI_Datatype, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Allgather(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Allgatherv
 **********************************************************/

int   __real_MPI_Allgatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, MPI_Comm  a8) ;
int   __wrap_MPI_Allgatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Allgatherv(void *, int, MPI_Datatype, void *, int *, int *, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Allgatherv(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Alltoall
 **********************************************************/

int   __real_MPI_Alltoall(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_MPI_Alltoall(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Alltoall(void *, int, MPI_Datatype, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Alltoall(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Alltoallv
 **********************************************************/

int   __real_MPI_Alltoallv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int *  a6, int *  a7, MPI_Datatype  a8, MPI_Comm  a9) ;
int   __wrap_MPI_Alltoallv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int *  a6, int *  a7, MPI_Datatype  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Alltoallv(void *, int *, int *, MPI_Datatype, void *, int *, int *, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Alltoallv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Reduce
 **********************************************************/

int   __real_MPI_Reduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, int  a6, MPI_Comm  a7) ;
int   __wrap_MPI_Reduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, int  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Reduce(void *, void *, int, MPI_Datatype, MPI_Op, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Reduce(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Op_create
 **********************************************************/

int   __real_MPI_Op_create(MPI_User_function *  a1, int  a2, MPI_Op *  a3) ;
int   __wrap_MPI_Op_create(MPI_User_function *  a1, int  a2, MPI_Op *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Op_create(MPI_User_function *, int, MPI_Op *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Op_create(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Op_free
 **********************************************************/

int   __real_MPI_Op_free(MPI_Op *  a1) ;
int   __wrap_MPI_Op_free(MPI_Op *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Op_free(MPI_Op *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Op_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Allreduce
 **********************************************************/

int   __real_MPI_Allreduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Allreduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Allreduce(void *, void *, int, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Allreduce(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Reduce_scatter
 **********************************************************/

int   __real_MPI_Reduce_scatter(void *  a1, void *  a2, int *  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Reduce_scatter(void *  a1, void *  a2, int *  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Reduce_scatter(void *, void *, int *, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Reduce_scatter(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Scan
 **********************************************************/

int   __real_MPI_Scan(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_MPI_Scan(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Scan(void *, void *, int, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Scan(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_size
 **********************************************************/

int   __real_MPI_Group_size(MPI_Group  a1, int *  a2) ;
int   __wrap_MPI_Group_size(MPI_Group  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_size(MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_size(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_rank
 **********************************************************/

int   __real_MPI_Group_rank(MPI_Group  a1, int *  a2) ;
int   __wrap_MPI_Group_rank(MPI_Group  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_rank(MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_rank(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_translate_ranks
 **********************************************************/

int   __real_MPI_Group_translate_ranks(MPI_Group  a1, int  a2, int *  a3, MPI_Group  a4, int *  a5) ;
int   __wrap_MPI_Group_translate_ranks(MPI_Group  a1, int  a2, int *  a3, MPI_Group  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_translate_ranks(MPI_Group, int, int *, MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_translate_ranks(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_compare
 **********************************************************/

int   __real_MPI_Group_compare(MPI_Group  a1, MPI_Group  a2, int *  a3) ;
int   __wrap_MPI_Group_compare(MPI_Group  a1, MPI_Group  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_compare(MPI_Group, MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_compare(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_group
 **********************************************************/

int   __real_MPI_Comm_group(MPI_Comm  a1, MPI_Group *  a2) ;
int   __wrap_MPI_Comm_group(MPI_Comm  a1, MPI_Group *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_group(MPI_Comm, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_group(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_union
 **********************************************************/

int   __real_MPI_Group_union(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_MPI_Group_union(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_union(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_union(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_intersection
 **********************************************************/

int   __real_MPI_Group_intersection(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_MPI_Group_intersection(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_intersection(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_intersection(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_difference
 **********************************************************/

int   __real_MPI_Group_difference(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_MPI_Group_difference(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_difference(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_difference(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_incl
 **********************************************************/

int   __real_MPI_Group_incl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4) ;
int   __wrap_MPI_Group_incl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_incl(MPI_Group, int, int *, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_incl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_excl
 **********************************************************/

int   __real_MPI_Group_excl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4) ;
int   __wrap_MPI_Group_excl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_excl(MPI_Group, int, int *, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_excl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_range_incl
 **********************************************************/

int   __real_MPI_Group_range_incl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4) ;
int   __wrap_MPI_Group_range_incl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_range_incl(MPI_Group, int, int [][3UL], MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_range_incl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_range_excl
 **********************************************************/

int   __real_MPI_Group_range_excl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4) ;
int   __wrap_MPI_Group_range_excl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_range_excl(MPI_Group, int, int [][3UL], MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_range_excl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Group_free
 **********************************************************/

int   __real_MPI_Group_free(MPI_Group *  a1) ;
int   __wrap_MPI_Group_free(MPI_Group *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Group_free(MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Group_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_size
 **********************************************************/

int   __real_MPI_Comm_size(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Comm_size(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_size(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_size(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_rank
 **********************************************************/

int   __real_MPI_Comm_rank(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Comm_rank(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_rank(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_rank(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_compare
 **********************************************************/

int   __real_MPI_Comm_compare(MPI_Comm  a1, MPI_Comm  a2, int *  a3) ;
int   __wrap_MPI_Comm_compare(MPI_Comm  a1, MPI_Comm  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_compare(MPI_Comm, MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_compare(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_dup
 **********************************************************/

int   __real_MPI_Comm_dup(MPI_Comm  a1, MPI_Comm *  a2) ;
int   __wrap_MPI_Comm_dup(MPI_Comm  a1, MPI_Comm *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_dup(MPI_Comm, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_dup(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_create
 **********************************************************/

int   __real_MPI_Comm_create(MPI_Comm  a1, MPI_Group  a2, MPI_Comm *  a3) ;
int   __wrap_MPI_Comm_create(MPI_Comm  a1, MPI_Group  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_create(MPI_Comm, MPI_Group, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_create(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_split
 **********************************************************/

int   __real_MPI_Comm_split(MPI_Comm  a1, int  a2, int  a3, MPI_Comm *  a4) ;
int   __wrap_MPI_Comm_split(MPI_Comm  a1, int  a2, int  a3, MPI_Comm *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_split(MPI_Comm, int, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_split(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_free
 **********************************************************/

int   __real_MPI_Comm_free(MPI_Comm *  a1) ;
int   __wrap_MPI_Comm_free(MPI_Comm *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_free(MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_test_inter
 **********************************************************/

int   __real_MPI_Comm_test_inter(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Comm_test_inter(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_test_inter(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_test_inter(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_remote_size
 **********************************************************/

int   __real_MPI_Comm_remote_size(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Comm_remote_size(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_remote_size(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_remote_size(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_remote_group
 **********************************************************/

int   __real_MPI_Comm_remote_group(MPI_Comm  a1, MPI_Group *  a2) ;
int   __wrap_MPI_Comm_remote_group(MPI_Comm  a1, MPI_Group *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_remote_group(MPI_Comm, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_remote_group(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Intercomm_create
 **********************************************************/

int   __real_MPI_Intercomm_create(MPI_Comm  a1, int  a2, MPI_Comm  a3, int  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_MPI_Intercomm_create(MPI_Comm  a1, int  a2, MPI_Comm  a3, int  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Intercomm_create(MPI_Comm, int, MPI_Comm, int, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Intercomm_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Intercomm_merge
 **********************************************************/

int   __real_MPI_Intercomm_merge(MPI_Comm  a1, int  a2, MPI_Comm *  a3) ;
int   __wrap_MPI_Intercomm_merge(MPI_Comm  a1, int  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Intercomm_merge(MPI_Comm, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Intercomm_merge(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Keyval_create
 **********************************************************/

int   __real_MPI_Keyval_create(MPI_Copy_function *  a1, MPI_Delete_function *  a2, int *  a3, void *  a4) ;
int   __wrap_MPI_Keyval_create(MPI_Copy_function *  a1, MPI_Delete_function *  a2, int *  a3, void *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Keyval_create(MPI_Copy_function *, MPI_Delete_function *, int *, void *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Keyval_create(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Keyval_free
 **********************************************************/

int   __real_MPI_Keyval_free(int *  a1) ;
int   __wrap_MPI_Keyval_free(int *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Keyval_free(int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Keyval_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Attr_put
 **********************************************************/

int   __real_MPI_Attr_put(MPI_Comm  a1, int  a2, void *  a3) ;
int   __wrap_MPI_Attr_put(MPI_Comm  a1, int  a2, void *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Attr_put(MPI_Comm, int, void *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Attr_put(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Attr_get
 **********************************************************/

int   __real_MPI_Attr_get(MPI_Comm  a1, int  a2, void *  a3, int *  a4) ;
int   __wrap_MPI_Attr_get(MPI_Comm  a1, int  a2, void *  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Attr_get(MPI_Comm, int, void *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Attr_get(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Attr_delete
 **********************************************************/

int   __real_MPI_Attr_delete(MPI_Comm  a1, int  a2) ;
int   __wrap_MPI_Attr_delete(MPI_Comm  a1, int  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Attr_delete(MPI_Comm, int)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Attr_delete(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Topo_test
 **********************************************************/

int   __real_MPI_Topo_test(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Topo_test(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Topo_test(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Topo_test(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_create
 **********************************************************/

int   __real_MPI_Cart_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_MPI_Cart_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_create(MPI_Comm, int, int *, int *, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Dims_create
 **********************************************************/

int   __real_MPI_Dims_create(int  a1, int  a2, int *  a3) ;
int   __wrap_MPI_Dims_create(int  a1, int  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Dims_create(int, int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Dims_create(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graph_create
 **********************************************************/

int   __real_MPI_Graph_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_MPI_Graph_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graph_create(MPI_Comm, int, int *, int *, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graph_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graphdims_get
 **********************************************************/

int   __real_MPI_Graphdims_get(MPI_Comm  a1, int *  a2, int *  a3) ;
int   __wrap_MPI_Graphdims_get(MPI_Comm  a1, int *  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graphdims_get(MPI_Comm, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graphdims_get(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graph_get
 **********************************************************/

int   __real_MPI_Graph_get(MPI_Comm  a1, int  a2, int  a3, int *  a4, int *  a5) ;
int   __wrap_MPI_Graph_get(MPI_Comm  a1, int  a2, int  a3, int *  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graph_get(MPI_Comm, int, int, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graph_get(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cartdim_get
 **********************************************************/

int   __real_MPI_Cartdim_get(MPI_Comm  a1, int *  a2) ;
int   __wrap_MPI_Cartdim_get(MPI_Comm  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cartdim_get(MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cartdim_get(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_get
 **********************************************************/

int   __real_MPI_Cart_get(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5) ;
int   __wrap_MPI_Cart_get(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_get(MPI_Comm, int, int *, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_get(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_rank
 **********************************************************/

int   __real_MPI_Cart_rank(MPI_Comm  a1, int *  a2, int *  a3) ;
int   __wrap_MPI_Cart_rank(MPI_Comm  a1, int *  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_rank(MPI_Comm, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_rank(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_coords
 **********************************************************/

int   __real_MPI_Cart_coords(MPI_Comm  a1, int  a2, int  a3, int *  a4) ;
int   __wrap_MPI_Cart_coords(MPI_Comm  a1, int  a2, int  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_coords(MPI_Comm, int, int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_coords(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graph_neighbors_count
 **********************************************************/

int   __real_MPI_Graph_neighbors_count(MPI_Comm  a1, int  a2, int *  a3) ;
int   __wrap_MPI_Graph_neighbors_count(MPI_Comm  a1, int  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graph_neighbors_count(MPI_Comm, int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graph_neighbors_count(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graph_neighbors
 **********************************************************/

int   __real_MPI_Graph_neighbors(MPI_Comm  a1, int  a2, int  a3, int *  a4) ;
int   __wrap_MPI_Graph_neighbors(MPI_Comm  a1, int  a2, int  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graph_neighbors(MPI_Comm, int, int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graph_neighbors(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_shift
 **********************************************************/

int   __real_MPI_Cart_shift(MPI_Comm  a1, int  a2, int  a3, int *  a4, int *  a5) ;
int   __wrap_MPI_Cart_shift(MPI_Comm  a1, int  a2, int  a3, int *  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_shift(MPI_Comm, int, int, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_shift(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_sub
 **********************************************************/

int   __real_MPI_Cart_sub(MPI_Comm  a1, int *  a2, MPI_Comm *  a3) ;
int   __wrap_MPI_Cart_sub(MPI_Comm  a1, int *  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_sub(MPI_Comm, int *, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_sub(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Cart_map
 **********************************************************/

int   __real_MPI_Cart_map(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5) ;
int   __wrap_MPI_Cart_map(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Cart_map(MPI_Comm, int, int *, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Cart_map(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Graph_map
 **********************************************************/

int   __real_MPI_Graph_map(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5) ;
int   __wrap_MPI_Graph_map(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Graph_map(MPI_Comm, int, int *, int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Graph_map(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Get_processor_name
 **********************************************************/

int   __real_MPI_Get_processor_name(char *  a1, int *  a2) ;
int   __wrap_MPI_Get_processor_name(char *  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Get_processor_name(char *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Get_processor_name(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Get_version
 **********************************************************/

int   __real_MPI_Get_version(int *  a1, int *  a2) ;
int   __wrap_MPI_Get_version(int *  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Get_version(int *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Get_version(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Errhandler_create
 **********************************************************/

int   __real_MPI_Errhandler_create(MPI_Handler_function *  a1, MPI_Errhandler *  a2) ;
int   __wrap_MPI_Errhandler_create(MPI_Handler_function *  a1, MPI_Errhandler *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Errhandler_create(MPI_Handler_function *, MPI_Errhandler *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Errhandler_create(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Errhandler_set
 **********************************************************/

int   __real_MPI_Errhandler_set(MPI_Comm  a1, MPI_Errhandler  a2) ;
int   __wrap_MPI_Errhandler_set(MPI_Comm  a1, MPI_Errhandler  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Errhandler_set(MPI_Comm, MPI_Errhandler)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Errhandler_set(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Errhandler_get
 **********************************************************/

int   __real_MPI_Errhandler_get(MPI_Comm  a1, MPI_Errhandler *  a2) ;
int   __wrap_MPI_Errhandler_get(MPI_Comm  a1, MPI_Errhandler *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Errhandler_get(MPI_Comm, MPI_Errhandler *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Errhandler_get(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Errhandler_free
 **********************************************************/

int   __real_MPI_Errhandler_free(MPI_Errhandler *  a1) ;
int   __wrap_MPI_Errhandler_free(MPI_Errhandler *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Errhandler_free(MPI_Errhandler *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Errhandler_free(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Error_string
 **********************************************************/

int   __real_MPI_Error_string(int  a1, char *  a2, int *  a3) ;
int   __wrap_MPI_Error_string(int  a1, char *  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Error_string(int, char *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Error_string(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Error_class
 **********************************************************/

int   __real_MPI_Error_class(int  a1, int *  a2) ;
int   __wrap_MPI_Error_class(int  a1, int *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Error_class(int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Error_class(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Wtime
 **********************************************************/

double   __real_MPI_Wtime() ;
double   __wrap_MPI_Wtime()  {

  double  retval;
  TAU_PROFILE_TIMER(t,"double MPI_Wtime()  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Wtime();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Wtick
 **********************************************************/

double   __real_MPI_Wtick() ;
double   __wrap_MPI_Wtick()  {

  double  retval;
  TAU_PROFILE_TIMER(t,"double MPI_Wtick()  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Wtick();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Init
 **********************************************************/

int   __real_MPI_Init(int *  a1, char ***  a2) ;
int   __wrap_MPI_Init(int *  a1, char ***  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Init(int *, char ***)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Init(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Finalize
 **********************************************************/

int   __real_MPI_Finalize() ;
int   __wrap_MPI_Finalize()  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Finalize()  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Finalize();
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Initialized
 **********************************************************/

int   __real_MPI_Initialized(int *  a1) ;
int   __wrap_MPI_Initialized(int *  a1)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Initialized(int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Initialized(a1);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Abort
 **********************************************************/

int   __real_MPI_Abort(MPI_Comm  a1, int  a2) ;
int   __wrap_MPI_Abort(MPI_Comm  a1, int  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Abort(MPI_Comm, int)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Abort(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}

/*
#warning "TAU: Not generating wrapper for function MPI_Pcontrol"
*/

/**********************************************************
   MPI_Comm_get_name
 **********************************************************/

int   __real_MPI_Comm_get_name(MPI_Comm  a1, char *  a2, int *  a3) ;
int   __wrap_MPI_Comm_get_name(MPI_Comm  a1, char *  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_get_name(MPI_Comm, char *, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_get_name(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Comm_set_name
 **********************************************************/

int   __real_MPI_Comm_set_name(MPI_Comm  a1, char *  a2) ;
int   __wrap_MPI_Comm_set_name(MPI_Comm  a1, char *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Comm_set_name(MPI_Comm, char *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Comm_set_name(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Send
 **********************************************************/

int   __real_PMPI_Send(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Send(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Send(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Send(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Recv
 **********************************************************/

int   __real_PMPI_Recv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Status *  a7) ;
int   __wrap_PMPI_Recv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Status *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Recv(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Recv(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Get_count
 **********************************************************/

int   __real_PMPI_Get_count(MPI_Status *  a1, MPI_Datatype  a2, int *  a3) ;
int   __wrap_PMPI_Get_count(MPI_Status *  a1, MPI_Datatype  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Get_count(MPI_Status *, MPI_Datatype, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Get_count(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Bsend
 **********************************************************/

int   __real_PMPI_Bsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Bsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Bsend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Bsend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Ssend
 **********************************************************/

int   __real_PMPI_Ssend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Ssend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Ssend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Ssend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Rsend
 **********************************************************/

int   __real_PMPI_Rsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Rsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Rsend(void *, int, MPI_Datatype, int, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Rsend(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Isend
 **********************************************************/

int   __real_PMPI_Isend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Isend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Isend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Isend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Ibsend
 **********************************************************/

int   __real_PMPI_Ibsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Ibsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Ibsend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Ibsend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Issend
 **********************************************************/

int   __real_PMPI_Issend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Issend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Issend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Issend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Irsend
 **********************************************************/

int   __real_PMPI_Irsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Irsend(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Irsend(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Irsend(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Irecv
 **********************************************************/

int   __real_PMPI_Irecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Irecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Irecv(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Irecv(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Wait
 **********************************************************/

int   __real_PMPI_Wait(MPI_Request *  a1, MPI_Status *  a2) ;
int   __wrap_PMPI_Wait(MPI_Request *  a1, MPI_Status *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Wait(MPI_Request *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Wait(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Test
 **********************************************************/

int   __real_PMPI_Test(MPI_Request *  a1, int *  a2, MPI_Status *  a3) ;
int   __wrap_PMPI_Test(MPI_Request *  a1, int *  a2, MPI_Status *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Test(MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Test(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Waitany
 **********************************************************/

int   __real_PMPI_Waitany(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4) ;
int   __wrap_PMPI_Waitany(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Waitany(int, MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Waitany(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Testany
 **********************************************************/

int   __real_PMPI_Testany(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_PMPI_Testany(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Testany(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Testany(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Waitall
 **********************************************************/

int   __real_PMPI_Waitall(int  a1, MPI_Request *  a2, MPI_Status *  a3) ;
int   __wrap_PMPI_Waitall(int  a1, MPI_Request *  a2, MPI_Status *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Waitall(int, MPI_Request *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Waitall(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Testall
 **********************************************************/

int   __real_PMPI_Testall(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4) ;
int   __wrap_PMPI_Testall(int  a1, MPI_Request *  a2, int *  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Testall(int, MPI_Request *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Testall(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Waitsome
 **********************************************************/

int   __real_PMPI_Waitsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_PMPI_Waitsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Waitsome(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Waitsome(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Testsome
 **********************************************************/

int   __real_PMPI_Testsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_PMPI_Testsome(int  a1, MPI_Request *  a2, int *  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Testsome(int, MPI_Request *, int *, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Testsome(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Iprobe
 **********************************************************/

int   __real_PMPI_Iprobe(int  a1, int  a2, MPI_Comm  a3, int *  a4, MPI_Status *  a5) ;
int   __wrap_PMPI_Iprobe(int  a1, int  a2, MPI_Comm  a3, int *  a4, MPI_Status *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Iprobe(int, int, MPI_Comm, int *, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Iprobe(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Probe
 **********************************************************/

int   __real_PMPI_Probe(int  a1, int  a2, MPI_Comm  a3, MPI_Status *  a4) ;
int   __wrap_PMPI_Probe(int  a1, int  a2, MPI_Comm  a3, MPI_Status *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Probe(int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Probe(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Send_init
 **********************************************************/

int   __real_PMPI_Send_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Send_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Send_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Send_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Bsend_init
 **********************************************************/

int   __real_PMPI_Bsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Bsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Bsend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Bsend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Ssend_init
 **********************************************************/

int   __real_PMPI_Ssend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Ssend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Ssend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Ssend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Rsend_init
 **********************************************************/

int   __real_PMPI_Rsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Rsend_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Rsend_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Rsend_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Recv_init
 **********************************************************/

int   __real_PMPI_Recv_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7) ;
int   __wrap_PMPI_Recv_init(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, MPI_Comm  a6, MPI_Request *  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Recv_init(void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Recv_init(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Startall
 **********************************************************/

int   __real_PMPI_Startall(int  a1, MPI_Request *  a2) ;
int   __wrap_PMPI_Startall(int  a1, MPI_Request *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Startall(int, MPI_Request *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Startall(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Sendrecv
 **********************************************************/

int   __real_PMPI_Sendrecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, void *  a6, int  a7, MPI_Datatype  a8, int  a9, int  a10, MPI_Comm  a11, MPI_Status *  a12) ;
int   __wrap_PMPI_Sendrecv(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, void *  a6, int  a7, MPI_Datatype  a8, int  a9, int  a10, MPI_Comm  a11, MPI_Status *  a12)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Sendrecv(void *, int, MPI_Datatype, int, int, void *, int, MPI_Datatype, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Sendrecv(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Sendrecv_replace
 **********************************************************/

int   __real_PMPI_Sendrecv_replace(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, int  a6, int  a7, MPI_Comm  a8, MPI_Status *  a9) ;
int   __wrap_PMPI_Sendrecv_replace(void *  a1, int  a2, MPI_Datatype  a3, int  a4, int  a5, int  a6, int  a7, MPI_Comm  a8, MPI_Status *  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Sendrecv_replace(void *, int, MPI_Datatype, int, int, int, int, MPI_Comm, MPI_Status *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Sendrecv_replace(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_contiguous
 **********************************************************/

int   __real_PMPI_Type_contiguous(int  a1, MPI_Datatype  a2, MPI_Datatype *  a3) ;
int   __wrap_PMPI_Type_contiguous(int  a1, MPI_Datatype  a2, MPI_Datatype *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_contiguous(int, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_contiguous(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_vector
 **********************************************************/

int   __real_PMPI_Type_vector(int  a1, int  a2, int  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_PMPI_Type_vector(int  a1, int  a2, int  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_vector(int, int, int, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_vector(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_hvector
 **********************************************************/

int   __real_PMPI_Type_hvector(int  a1, int  a2, MPI_Aint  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_PMPI_Type_hvector(int  a1, int  a2, MPI_Aint  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_hvector(int, int, MPI_Aint, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_hvector(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_indexed
 **********************************************************/

int   __real_PMPI_Type_indexed(int  a1, int *  a2, int *  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_PMPI_Type_indexed(int  a1, int *  a2, int *  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_indexed(int, int *, int *, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_indexed(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_hindexed
 **********************************************************/

int   __real_PMPI_Type_hindexed(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype  a4, MPI_Datatype *  a5) ;
int   __wrap_PMPI_Type_hindexed(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_hindexed(int, int *, MPI_Aint *, MPI_Datatype, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_hindexed(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_struct
 **********************************************************/

int   __real_PMPI_Type_struct(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype *  a4, MPI_Datatype *  a5) ;
int   __wrap_PMPI_Type_struct(int  a1, int *  a2, MPI_Aint *  a3, MPI_Datatype *  a4, MPI_Datatype *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_struct(int, int *, MPI_Aint *, MPI_Datatype *, MPI_Datatype *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_struct(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Address
 **********************************************************/

int   __real_PMPI_Address(void *  a1, MPI_Aint *  a2) ;
int   __wrap_PMPI_Address(void *  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Address(void *, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Address(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_extent
 **********************************************************/

int   __real_PMPI_Type_extent(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_PMPI_Type_extent(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_extent(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_extent(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_lb
 **********************************************************/

int   __real_PMPI_Type_lb(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_PMPI_Type_lb(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_lb(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_lb(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Type_ub
 **********************************************************/

int   __real_PMPI_Type_ub(MPI_Datatype  a1, MPI_Aint *  a2) ;
int   __wrap_PMPI_Type_ub(MPI_Datatype  a1, MPI_Aint *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Type_ub(MPI_Datatype, MPI_Aint *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Type_ub(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Get_elements
 **********************************************************/

int   __real_PMPI_Get_elements(MPI_Status *  a1, MPI_Datatype  a2, int *  a3) ;
int   __wrap_PMPI_Get_elements(MPI_Status *  a1, MPI_Datatype  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Get_elements(MPI_Status *, MPI_Datatype, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Get_elements(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Pack
 **********************************************************/

int   __real_PMPI_Pack(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, int *  a6, MPI_Comm  a7) ;
int   __wrap_PMPI_Pack(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, int *  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Pack(void *, int, MPI_Datatype, void *, int, int *, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Pack(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Unpack
 **********************************************************/

int   __real_PMPI_Unpack(void *  a1, int  a2, int *  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_PMPI_Unpack(void *  a1, int  a2, int *  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Unpack(void *, int, int *, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Unpack(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Pack_size
 **********************************************************/

int   __real_PMPI_Pack_size(int  a1, MPI_Datatype  a2, MPI_Comm  a3, int *  a4) ;
int   __wrap_PMPI_Pack_size(int  a1, MPI_Datatype  a2, MPI_Comm  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Pack_size(int, MPI_Datatype, MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Pack_size(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Bcast
 **********************************************************/

int   __real_PMPI_Bcast(void *  a1, int  a2, MPI_Datatype  a3, int  a4, MPI_Comm  a5) ;
int   __wrap_PMPI_Bcast(void *  a1, int  a2, MPI_Datatype  a3, int  a4, MPI_Comm  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Bcast(void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Bcast(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Gather
 **********************************************************/

int   __real_PMPI_Gather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8) ;
int   __wrap_PMPI_Gather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Gather(void *, int, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Gather(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Gatherv
 **********************************************************/

int   __real_PMPI_Gatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9) ;
int   __wrap_PMPI_Gatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Gatherv(void *, int, MPI_Datatype, void *, int *, int *, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Gatherv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Scatter
 **********************************************************/

int   __real_PMPI_Scatter(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8) ;
int   __wrap_PMPI_Scatter(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, int  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Scatter(void *, int, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Scatter(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Scatterv
 **********************************************************/

int   __real_PMPI_Scatterv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9) ;
int   __wrap_PMPI_Scatterv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int  a6, MPI_Datatype  a7, int  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Scatterv(void *, int *, int *, MPI_Datatype, void *, int, MPI_Datatype, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Scatterv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Allgather
 **********************************************************/

int   __real_PMPI_Allgather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_PMPI_Allgather(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Allgather(void *, int, MPI_Datatype, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Allgather(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Allgatherv
 **********************************************************/

int   __real_PMPI_Allgatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, MPI_Comm  a8) ;
int   __wrap_PMPI_Allgatherv(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int *  a5, int *  a6, MPI_Datatype  a7, MPI_Comm  a8)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Allgatherv(void *, int, MPI_Datatype, void *, int *, int *, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Allgatherv(a1, a2, a3, a4, a5, a6, a7, a8);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Alltoall
 **********************************************************/

int   __real_PMPI_Alltoall(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7) ;
int   __wrap_PMPI_Alltoall(void *  a1, int  a2, MPI_Datatype  a3, void *  a4, int  a5, MPI_Datatype  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Alltoall(void *, int, MPI_Datatype, void *, int, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Alltoall(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Alltoallv
 **********************************************************/

int   __real_PMPI_Alltoallv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int *  a6, int *  a7, MPI_Datatype  a8, MPI_Comm  a9) ;
int   __wrap_PMPI_Alltoallv(void *  a1, int *  a2, int *  a3, MPI_Datatype  a4, void *  a5, int *  a6, int *  a7, MPI_Datatype  a8, MPI_Comm  a9)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Alltoallv(void *, int *, int *, MPI_Datatype, void *, int *, int *, MPI_Datatype, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Alltoallv(a1, a2, a3, a4, a5, a6, a7, a8, a9);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Reduce
 **********************************************************/

int   __real_PMPI_Reduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, int  a6, MPI_Comm  a7) ;
int   __wrap_PMPI_Reduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, int  a6, MPI_Comm  a7)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Reduce(void *, void *, int, MPI_Datatype, MPI_Op, int, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Reduce(a1, a2, a3, a4, a5, a6, a7);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Op_create
 **********************************************************/

int   __real_PMPI_Op_create(MPI_User_function *  a1, int  a2, MPI_Op *  a3) ;
int   __wrap_PMPI_Op_create(MPI_User_function *  a1, int  a2, MPI_Op *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Op_create(MPI_User_function *, int, MPI_Op *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Op_create(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Allreduce
 **********************************************************/

int   __real_PMPI_Allreduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Allreduce(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Allreduce(void *, void *, int, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Allreduce(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Reduce_scatter
 **********************************************************/

int   __real_PMPI_Reduce_scatter(void *  a1, void *  a2, int *  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Reduce_scatter(void *  a1, void *  a2, int *  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Reduce_scatter(void *, void *, int *, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Reduce_scatter(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Scan
 **********************************************************/

int   __real_PMPI_Scan(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6) ;
int   __wrap_PMPI_Scan(void *  a1, void *  a2, int  a3, MPI_Datatype  a4, MPI_Op  a5, MPI_Comm  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Scan(void *, void *, int, MPI_Datatype, MPI_Op, MPI_Comm)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Scan(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_translate_ranks
 **********************************************************/

int   __real_PMPI_Group_translate_ranks(MPI_Group  a1, int  a2, int *  a3, MPI_Group  a4, int *  a5) ;
int   __wrap_PMPI_Group_translate_ranks(MPI_Group  a1, int  a2, int *  a3, MPI_Group  a4, int *  a5)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_translate_ranks(MPI_Group, int, int *, MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_translate_ranks(a1, a2, a3, a4, a5);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_compare
 **********************************************************/

int   __real_PMPI_Group_compare(MPI_Group  a1, MPI_Group  a2, int *  a3) ;
int   __wrap_PMPI_Group_compare(MPI_Group  a1, MPI_Group  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_compare(MPI_Group, MPI_Group, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_compare(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_group
 **********************************************************/

int   __real_PMPI_Comm_group(MPI_Comm  a1, MPI_Group *  a2) ;
int   __wrap_PMPI_Comm_group(MPI_Comm  a1, MPI_Group *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_group(MPI_Comm, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_group(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_union
 **********************************************************/

int   __real_PMPI_Group_union(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_PMPI_Group_union(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_union(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_union(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_intersection
 **********************************************************/

int   __real_PMPI_Group_intersection(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_PMPI_Group_intersection(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_intersection(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_intersection(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_difference
 **********************************************************/

int   __real_PMPI_Group_difference(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3) ;
int   __wrap_PMPI_Group_difference(MPI_Group  a1, MPI_Group  a2, MPI_Group *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_difference(MPI_Group, MPI_Group, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_difference(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_incl
 **********************************************************/

int   __real_PMPI_Group_incl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4) ;
int   __wrap_PMPI_Group_incl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_incl(MPI_Group, int, int *, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_incl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_excl
 **********************************************************/

int   __real_PMPI_Group_excl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4) ;
int   __wrap_PMPI_Group_excl(MPI_Group  a1, int  a2, int *  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_excl(MPI_Group, int, int *, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_excl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_range_incl
 **********************************************************/

int   __real_PMPI_Group_range_incl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4) ;
int   __wrap_PMPI_Group_range_incl(MPI_Group  a1, int  a2, int **  a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_range_incl(MPI_Group, int, int [][3UL], MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_range_incl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Group_range_excl
 **********************************************************/

int   __real_PMPI_Group_range_excl(MPI_Group  a1, int  a2, int ** a3, MPI_Group *  a4) ;
int   __wrap_PMPI_Group_range_excl(MPI_Group  a1, int  a2, int ** a3, MPI_Group *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Group_range_excl(MPI_Group, int, int [][3UL], MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Group_range_excl(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_compare
 **********************************************************/

int   __real_PMPI_Comm_compare(MPI_Comm  a1, MPI_Comm  a2, int *  a3) ;
int   __wrap_PMPI_Comm_compare(MPI_Comm  a1, MPI_Comm  a2, int *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_compare(MPI_Comm, MPI_Comm, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_compare(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_dup
 **********************************************************/

int   __real_PMPI_Comm_dup(MPI_Comm  a1, MPI_Comm *  a2) ;
int   __wrap_PMPI_Comm_dup(MPI_Comm  a1, MPI_Comm *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_dup(MPI_Comm, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_dup(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_create
 **********************************************************/

int   __real_PMPI_Comm_create(MPI_Comm  a1, MPI_Group  a2, MPI_Comm *  a3) ;
int   __wrap_PMPI_Comm_create(MPI_Comm  a1, MPI_Group  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_create(MPI_Comm, MPI_Group, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_create(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_split
 **********************************************************/

int   __real_PMPI_Comm_split(MPI_Comm  a1, int  a2, int  a3, MPI_Comm *  a4) ;
int   __wrap_PMPI_Comm_split(MPI_Comm  a1, int  a2, int  a3, MPI_Comm *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_split(MPI_Comm, int, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_split(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Comm_remote_group
 **********************************************************/

int   __real_PMPI_Comm_remote_group(MPI_Comm  a1, MPI_Group *  a2) ;
int   __wrap_PMPI_Comm_remote_group(MPI_Comm  a1, MPI_Group *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Comm_remote_group(MPI_Comm, MPI_Group *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Comm_remote_group(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Intercomm_create
 **********************************************************/

int   __real_PMPI_Intercomm_create(MPI_Comm  a1, int  a2, MPI_Comm  a3, int  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_PMPI_Intercomm_create(MPI_Comm  a1, int  a2, MPI_Comm  a3, int  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Intercomm_create(MPI_Comm, int, MPI_Comm, int, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Intercomm_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Intercomm_merge
 **********************************************************/

int   __real_PMPI_Intercomm_merge(MPI_Comm  a1, int  a2, MPI_Comm *  a3) ;
int   __wrap_PMPI_Intercomm_merge(MPI_Comm  a1, int  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Intercomm_merge(MPI_Comm, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Intercomm_merge(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Keyval_create
 **********************************************************/

int   __real_PMPI_Keyval_create(MPI_Copy_function *  a1, MPI_Delete_function *  a2, int *  a3, void *  a4) ;
int   __wrap_PMPI_Keyval_create(MPI_Copy_function *  a1, MPI_Delete_function *  a2, int *  a3, void *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Keyval_create(MPI_Copy_function *, MPI_Delete_function *, int *, void *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Keyval_create(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Cart_create
 **********************************************************/

int   __real_PMPI_Cart_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_PMPI_Cart_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Cart_create(MPI_Comm, int, int *, int *, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Cart_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Graph_create
 **********************************************************/

int   __real_PMPI_Graph_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6) ;
int   __wrap_PMPI_Graph_create(MPI_Comm  a1, int  a2, int *  a3, int *  a4, int  a5, MPI_Comm *  a6)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Graph_create(MPI_Comm, int, int *, int *, int, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Graph_create(a1, a2, a3, a4, a5, a6);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Cart_sub
 **********************************************************/

int   __real_PMPI_Cart_sub(MPI_Comm  a1, int *  a2, MPI_Comm *  a3) ;
int   __wrap_PMPI_Cart_sub(MPI_Comm  a1, int *  a2, MPI_Comm *  a3)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Cart_sub(MPI_Comm, int *, MPI_Comm *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Cart_sub(a1, a2, a3);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Errhandler_create
 **********************************************************/

int   __real_PMPI_Errhandler_create(MPI_Handler_function *  a1, MPI_Errhandler *  a2) ;
int   __wrap_PMPI_Errhandler_create(MPI_Handler_function *  a1, MPI_Errhandler *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Errhandler_create(MPI_Handler_function *, MPI_Errhandler *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Errhandler_create(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Errhandler_set
 **********************************************************/

int   __real_PMPI_Errhandler_set(MPI_Comm  a1, MPI_Errhandler  a2) ;
int   __wrap_PMPI_Errhandler_set(MPI_Comm  a1, MPI_Errhandler  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Errhandler_set(MPI_Comm, MPI_Errhandler)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Errhandler_set(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   PMPI_Errhandler_get
 **********************************************************/

int   __real_PMPI_Errhandler_get(MPI_Comm  a1, MPI_Errhandler *  a2) ;
int   __wrap_PMPI_Errhandler_get(MPI_Comm  a1, MPI_Errhandler *  a2)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int PMPI_Errhandler_get(MPI_Comm, MPI_Errhandler *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_PMPI_Errhandler_get(a1, a2);
  TAU_PROFILE_STOP(t);
  return retval;

}


/**********************************************************
   MPI_Init_thread
 **********************************************************/

int   __real_MPI_Init_thread(int *  a1, char ***  a2, int  a3, int *  a4) ;
int   __wrap_MPI_Init_thread(int *  a1, char ***  a2, int  a3, int *  a4)  {

  int  retval;
  TAU_PROFILE_TIMER(t,"int MPI_Init_thread(int *, char ***, int, int *)  C", "", TAU_USER);
  TAU_PROFILE_START(t);
  retval  =  __real_MPI_Init_thread(a1, a2, a3, a4);
  TAU_PROFILE_STOP(t);
  return retval;

}

