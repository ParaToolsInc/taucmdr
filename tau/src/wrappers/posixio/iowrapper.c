#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <TAU.h>
#include <string.h>
#include <stdlib.h>

// We should forward declare the TauEnv functions, but TAU_ASSERT is defined
// in tau_internal.h, and variadic macros are not supported by pgcc.
// So, for PGI, don't include this header.
#ifndef __PGI
#include <Profile/TauEnv.h>
#endif

#define TAU_READ TAU_IO
#define TAU_WRITE TAU_IO

int TauWrapperFsync( int fd)
{
  int ret;
  TAU_PROFILE_TIMER(t, "fsync()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = fsync(fd);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fsync_fd, "FSYNC fd");
    TAU_REGISTER_EVENT(fsync_ret, "FSYNC ret");
    TAU_EVENT(fsync_fd, fd);
    TAU_EVENT(fsync_ret, ret);
  }

  TAU_PROFILE_STOP(t);

  TAU_VERBOSE("Fsync call with fd %d ret %d\n", fd, ret);

  return ret;
}

int TauWrapperOpen(const char *pathname, int flags)
{
  int ret;
  TAU_PROFILE_TIMER(t, "open()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = open(pathname, flags);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(open_fd, "OPEN flags");
    TAU_REGISTER_EVENT(open_ret, "OPEN ret");
    TAU_EVENT(open_fd, flags);
    TAU_EVENT(open_ret, ret);
  }

  TAU_PROFILE_STOP(t);

  TAU_VERBOSE("Open call with pathname %s and flags %d: ret %d\n", pathname, flags, ret);

  return ret;
}

size_t TauWrapperRead(int fd, void *buf, size_t nbytes)
{
  int ret;
  double currentRead = 0.0;
  struct timeval t1, t2; 
  TAU_PROFILE_TIMER(t, "read()", " ", TAU_IO);
  TAU_REGISTER_CONTEXT_EVENT(re, "READ Bandwidth (MB/s)");
  TAU_REGISTER_CONTEXT_EVENT(bytesread, "READ Bytes Read");
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = read(fd, buf, nbytes);
  gettimeofday(&t2, 0);


  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  /*  if (currentRead > 1e-12) {
    TAU_CONTEXT_EVENT(re, (double) nbytes/currentRead);
    }
  else {
  printf("TauWrapperRead: currentRead = %g\n", currentRead);
    }*/

  if (currentRead > 1e-12) {
    TAU_CONTEXT_EVENT(re, (double) nbytes/currentRead);
  }

  TAU_CONTEXT_EVENT(bytesread, nbytes);
  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(read_fd, "READ fd");
    TAU_REGISTER_EVENT(read_ret, "READ ret");
    TAU_EVENT(read_fd, fd);
    TAU_EVENT(read_ret, ret);
  }

  TAU_VERBOSE("Read fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);

  TAU_PROFILE_STOP(t);

  return ret;
}

size_t TauWrapperWrite(int fd, void *buf, size_t nbytes)
{
  int ret;
  double currentWrite = 0.0;
  struct timeval t1, t2; 
  TAU_PROFILE_TIMER(t, "write()", " ", TAU_IO);
  TAU_REGISTER_CONTEXT_EVENT(wb, "WRITE Bandwidth (MB/s)");
  TAU_REGISTER_CONTEXT_EVENT(byteswritten, "WRITE Bytes Written");
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = write(fd, buf, nbytes);
  gettimeofday(&t2, 0);

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events *//*
  if (currentWrite > 1e-12) {
    TAU_CONTEXT_EVENT(wb, (double) nbytes/currentWrite);
  }
  else {
    printf("TauWrapperWrite: currentWrite = %g\n", currentWrite);
    }*/

  if (currentWrite > 1e-12) {
    TAU_CONTEXT_EVENT(wb, (double) nbytes/currentWrite);
    TAU_CONTEXT_EVENT(byteswritten, nbytes);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(write_fd, "WRITE fd");
    TAU_REGISTER_EVENT(write_ret, "WRITE ret");
    TAU_EVENT(write_fd, fd);
    TAU_EVENT(write_ret, ret);
  }

  TAU_VERBOSE("Write fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);

  TAU_PROFILE_STOP(t);

  return ret;
}
size_t TauWrapperClose(int fd)
{
  int ret;
  TAU_PROFILE_TIMER(t, "close()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = close(fd);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(close_fd, "CLOSE fd");
    TAU_REGISTER_EVENT(close_ret, "CLOSE ret");
    TAU_EVENT(close_fd, fd);
    TAU_EVENT(close_ret, ret);
  }

  TAU_VERBOSE("Close fd %d ret %d\n", fd, ret);

  TAU_PROFILE_STOP(t);

  return ret;
}

/*********************************************************************
 * lseek
 ********************************************************************/
off_t TauWrapperLseek(int fd, off_t offset, int whence)
{
  int ret;

  TAU_PROFILE_TIMER(t, "lseek()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = lseek(fd, offset, whence);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(lseek_fd, "LSEEK fd");
    TAU_REGISTER_EVENT(lseek_offset, "LSEEK offset");
    TAU_REGISTER_EVENT(lseek_whence, "LSEEK whence");
    TAU_EVENT(lseek_fd, fd);
    TAU_EVENT(lseek_offset, offset);
    TAU_EVENT(lseek_whence, whence);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("lseek called\n");
  // *CWL* - Bug?
  Tau_global_decr_insideTAU();

  return ret;
}

