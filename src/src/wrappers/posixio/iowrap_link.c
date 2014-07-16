#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <aio.h>
#include <sys/uio.h>
#include <setjmp.h>
#include <stdarg.h>
#include <TAU.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <Profile/TauIoWrap.h>

// We should forward declare the TauEnv functions, but TAU_ASSERT is defined
// in tau_internal.h, and variadic macros are not supported by pgcc.
// So, for PGI, don't include this header.
#ifndef __PGI
#include <Profile/TauEnv.h>
#endif

#define TAU_MAX_SOCKET_LEN 1024
#define TAU_READ TAU_IO
#define TAU_WRITE TAU_IO
extern void Tau_iowrap_checkInit(void);

/* FIX for Apple: */
#ifdef __APPLE__
typedef int64_t               off64_t;
#endif /* __APPLE__ */

/* FIX for others... */
#ifndef off64_t
typedef int64_t               off64_t;
typedef struct stat               STRUCT_STAT64;
#else
typedef struct stat64               STRUCT_STAT64;
#endif

/*********************************************************************
 * fsync
 ********************************************************************/
int __real_fsync( int fd);
int __wrap_fsync( int fd)
{
  int ret;
  
  if (Tau_iowrap_checkPassThrough()) {
    return __real_fsync(fd); 
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fsync()", " ", TAU_IO);
  TAU_PROFILE_START(t);
  ret = __real_fsync(fd);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fsync_fd, "FSYNC fd");
    TAU_REGISTER_EVENT(fsync_ret, "FSYNC ret");
    TAU_EVENT(fsync_fd, fd);
    TAU_EVENT(fsync_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("Fsync call with fd %d ret %d\n", fd, ret);

  return ret;
}

/*********************************************************************
 * open
 ********************************************************************/
int __real_open(const char *pathname, int flags, ...);
int __wrap_open(const char *pathname, int flags, ...)
{
  int ret;
  int mode = 0;
  int mode_specified = 0; 
  TAU_VERBOSE("__wrap_open: pathname = %s\n", pathname); 
 
  if (flags & O_CREAT) {
    va_list arg;
    va_start(arg, flags);
    mode = va_arg(arg, int); 
    va_end(arg);
    mode_specified = 1; 
  }

  if (Tau_iowrap_checkPassThrough()) {
    if (!mode_specified) 
      return __real_open(pathname, flags); 
    else
      return __real_open(pathname, flags, mode); 
  }
  Tau_global_incr_insideTAU();
 Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "open()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  if (!mode_specified) 
    ret = __real_open(pathname, flags); 
  else
    ret = __real_open(pathname, flags, mode); 

  if (ret != -1) {
    Tau_iowrap_registerEvents(ret, pathname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(open_fd, "OPEN flags");
    TAU_REGISTER_EVENT(open_ret, "OPEN ret");
    TAU_EVENT(open_fd, flags);
    TAU_EVENT(open_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("Open call with pathname %s and flags %d: ret %d\n", pathname, flags, ret);

  return ret;
}

/*********************************************************************
 * open64
 ********************************************************************/
int __real_open64(const char *pathname, int flags, ...);
int __wrap_open64(const char *pathname, int flags, ...)
{
  int ret;
  int mode = 0;
  int mode_specified = 0;
  
  if (flags & O_CREAT) {
    va_list arg;
    va_start(arg, flags);
    mode = va_arg(arg, int);
    va_end(arg);
    mode_specified = 1;
  }

  if (Tau_iowrap_checkPassThrough()) {
    if (!mode_specified)
      return __real_open64(pathname, flags);
    else
      return __real_open64(pathname, flags, mode);
  }
  Tau_global_incr_insideTAU();
Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "open()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  if (!mode_specified)
    ret = __real_open64(pathname, flags);
  else
    ret = __real_open64(pathname, flags, mode);

  if (ret != -1) {
    Tau_iowrap_registerEvents(ret, pathname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(open64_fd, "OPEN flags");
    TAU_REGISTER_EVENT(open64_ret, "OPEN ret");
    TAU_EVENT(open64_fd, flags);
    TAU_EVENT(open64_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("Open call with pathname %s and flags %d: ret %d\n", pathname, flags, ret);

  return ret;
}

/*********************************************************************
 * creat
 ********************************************************************/
int __real_creat(const char *pathname, mode_t mode);
int __wrap_creat(const char *pathname, mode_t mode) 
{
  int ret;
  

  if (Tau_iowrap_checkPassThrough()) {
    return __real_creat(pathname, mode);
  }
  Tau_global_incr_insideTAU();
Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "creat()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_creat(pathname, mode);

  if (ret != -1) {
    Tau_iowrap_registerEvents(ret, pathname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(creat_fd, "CREAT mode");
    TAU_REGISTER_EVENT(creat_ret, "CREAT ret");
    TAU_EVENT(creat_fd, mode);
    TAU_EVENT(creat_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("creat called on pathname %s with mode %d: ret %d\n", pathname, mode, ret);

  return ret;
}

/*********************************************************************
 * creat64
 ********************************************************************/
int __real_creat64(const char *pathname, mode_t mode);
int __wrap_creat64(const char *pathname, mode_t mode)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_creat64(pathname, mode);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "creat64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_creat64(pathname, mode);

  if (ret != -1) {
    Tau_iowrap_registerEvents(ret, pathname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(creat64_fd, "CREAT64 mode");
    TAU_REGISTER_EVENT(creat64_ret, "CREAT64 ret");
    TAU_EVENT(creat64_fd, mode);
    TAU_EVENT(creat64_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("creat called on pathname %s with mode %d: ret %d\n", pathname, mode, ret);

  return ret;
}

/*********************************************************************
 * fopen
 ********************************************************************/
FILE * __real_fopen(const char *pathname, const char * mode);
FILE * __wrap_fopen(const char *pathname, const char * mode)
{
  FILE * ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fopen(pathname, mode);
  }
  Tau_global_incr_insideTAU();
    Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fopen()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fopen(pathname, mode);

  if (ret != NULL) {
    Tau_iowrap_registerEvents(fileno(ret), pathname);
  }
/* We can't track mode (const char *) or ret (FILE *) in fopen:
  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fopen_ret, "FOPEN ret");
    TAU_EVENT(fopen_ret, ret);
  }
*/

  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("fopen called with pathname=%s, mode=%d\n", pathname, mode);

  return ret;
}

/*********************************************************************
 * fopen64
 ********************************************************************/
FILE*  __real_fopen64(const char *pathname, const char * mode);
FILE * __wrap_fopen64(const char *pathname, const char * mode)
{
  FILE * ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fopen64(pathname, mode);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fopen64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fopen64(pathname, mode);

  if (ret != NULL) {
    Tau_iowrap_registerEvents(fileno(ret), pathname);
  }

/* We can't track mode (const char *) or ret (FILE *) in fopen64:
  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fopen64_ret, "FOPEN64 ret");
    TAU_EVENT(fopen64_ret, ret);
  }
*/

  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("fopen64 called with pathname=%s, mode=%d\n", pathname, mode);

  return ret;
}




 
/*********************************************************************
 * pipe
 ********************************************************************/
int __real_pipe(int filedes[2]);
int __wrap_pipe(int filedes[2])
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_pipe(filedes);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "pipe()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_pipe(filedes);

  if (ret ==0) {
    Tau_iowrap_registerEvents(filedes[0], "pipe");
    Tau_iowrap_registerEvents(filedes[1], "pipe");
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(pipe_fd0, "pipe fd[0]");
    TAU_REGISTER_EVENT(pipe_fd1, "pipe fd[1]");
    TAU_REGISTER_EVENT(pipe_ret, "pipe ret");
    TAU_EVENT(pipe_fd0, filedes[0]);
    TAU_EVENT(pipe_fd1, filedes[1]);
    TAU_EVENT(pipe_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("pipe called with filedes[0]= %d, filedes[1]=%d: ret %d\n", filedes[0], filedes[1], ret);

  return ret;
}

/*********************************************************************
 * Tau_wrapper_get_socketname returns the name of the socket (AF_INET/AF_UNIX)
 ********************************************************************/
char * Tau_wrapper_get_socket_name(const struct sockaddr *sa, char *s, size_t len) {
  int i;
  Tau_iowrap_checkInit();
  char addr[256];
  switch (sa->sa_family) {
    case AF_INET:
      inet_ntop(AF_INET, &(((struct sockaddr_in *) sa)->sin_addr), addr, len);
      sprintf(s,"%s,port=%d",addr,ntohs((((struct sockaddr_in *)sa)->sin_port)));
      break;
    case AF_INET6:
      inet_ntop(AF_INET6, &(((struct sockaddr_in6 *) sa)->sin6_addr), addr, len);
      for (i = 0; i < strlen(addr); i++) {
        if (addr[i] == ':' ) addr[i] = '.';
      }
      sprintf(s,"%s,port=%d",addr,ntohs((((struct sockaddr_in6 *)sa)->sin6_port)));
      break;
    case AF_UNIX:
      strncpy(s, ((char *)(((struct sockaddr_un *) sa)->sun_path)), len);
      break;
    default:
      strncpy(s, "Unknown address family", len);
      return NULL;
  }
  return s;
}

/*********************************************************************
 * socket
 ********************************************************************/
int __real_socket(int domain, int type, int protocol);
int __wrap_socket(int domain, int type, int protocol) {
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_socket(domain, type, protocol);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "socket()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_socket(domain, type, protocol);

  if (ret != -1) {
    Tau_iowrap_registerEvents(ret, "socket");
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(socket_domain, "socket domain");
    TAU_REGISTER_EVENT(socket_type, "socket type");
    TAU_REGISTER_EVENT(socket_protocol, "socket protocol");
    TAU_REGISTER_EVENT(socket_ret, "socket ret");
    TAU_EVENT(socket_domain, domain);
    TAU_EVENT(socket_type, type);
    TAU_EVENT(socket_protocol, protocol);
    TAU_EVENT(socket_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("socket called domain = %d, type = %d, protocol = %d\n", domain, type, protocol);

  return ret;
}

/*********************************************************************
 * socketpair
 ********************************************************************/
int __real_socketpair(int domain, int type, int protocol, int sv[2]);
int __wrap_socketpair(int domain, int type, int protocol, int sv[2]) {
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_socketpair(domain, type, protocol, sv);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "socketpair()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_socketpair(domain, type, protocol, sv);

  if (ret == 0) {
    Tau_iowrap_registerEvents(sv[0], "socketpair");
    Tau_iowrap_registerEvents(sv[1], "socketpair");
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(socket_domain, "socketpair domain");
    TAU_REGISTER_EVENT(socket_type, "socketpair type");
    TAU_REGISTER_EVENT(socket_protocol, "socketpair protocol");
    TAU_REGISTER_EVENT(socket_ret, "socketpair ret");
    TAU_EVENT(socket_domain, domain);
    TAU_EVENT(socket_type, type);
    TAU_EVENT(socket_protocol, protocol);
    TAU_EVENT(socket_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("socketpair called domain = %d, type = %d, protocol = %d, sv[0]=%d, sv[1]=%d\n", domain, type, protocol, sv[0], sv[1]);

  return ret;
}


/*********************************************************************
 * bind
 ********************************************************************/
int __real_bind(int socket, const struct sockaddr *address, socklen_t address_len);
int __wrap_bind(int socket, const struct sockaddr *address, socklen_t address_len) 
{
  int ret;

  char socketname[TAU_MAX_SOCKET_LEN];

  if (Tau_iowrap_checkPassThrough()) {
    return __real_bind(socket, address, address_len);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "bind()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_bind(socket, address, address_len);

  if (ret == 0) {
    Tau_wrapper_get_socket_name(address, (char *) socketname, address_len);
    Tau_iowrap_registerEvents(socket, (const char *) socketname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(bind_socket, "bind socket");
    TAU_REGISTER_EVENT(bind_ret, "bind ret");
    TAU_EVENT(bind_socket, socket);
    TAU_EVENT(bind_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("bind called socket = %d, socketname = %s, ret = %d\n", socket, socketname, ret);

  return ret;
}



/*********************************************************************
 * connect
 ********************************************************************/
int __real_connect(int socket, struct sockaddr *address, socklen_t address_len);
int __wrap_connect(int socket, struct sockaddr *address, socklen_t address_len)
{
  int ret;

  char socketname[TAU_MAX_SOCKET_LEN];

  if (Tau_iowrap_checkPassThrough()) {
    return __real_connect(socket, address, address_len);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "connect()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_connect(socket, address, address_len);

  if (ret != -1) {
    Tau_wrapper_get_socket_name(address, (char *) socketname, (size_t) address_len);
    Tau_iowrap_registerEvents(socket, (const char *) socketname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(connect_socket, "connect socket");
    TAU_REGISTER_EVENT(connect_ret, "connect ret");
    TAU_EVENT(connect_socket, socket);
    TAU_EVENT(connect_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("connect called socket = %d, socketname = %s, ret = %d\n", socket, socketname, ret);

  return ret;
}




/*********************************************************************
 * accept
 ********************************************************************/
int __real_accept(int socket, struct sockaddr *address, socklen_t* address_len);
int __wrap_accept(int socket, struct sockaddr *address, socklen_t* address_len)
{
  int ret;

  char socketname[TAU_MAX_SOCKET_LEN];

  if (Tau_iowrap_checkPassThrough()) {
    return __real_accept(socket, address, address_len);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "accept()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_accept(socket, address, address_len);

  if (ret != -1) {
    Tau_wrapper_get_socket_name(address, (char *) socketname, (size_t) (*address_len));
    Tau_iowrap_registerEvents(ret, (const char *) socketname);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(accept_socket, "accept socket");
    TAU_REGISTER_EVENT(accept_ret, "accept ret");
    TAU_EVENT(accept_socket, socket);
    TAU_EVENT(accept_ret, ret);
  }
  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  TAU_VERBOSE("accept called socket = %d, socketname = %s, ret = %d\n", socket, socketname, ret);

  return ret;
}

/*********************************************************************
 * fcntl
 ********************************************************************/
int __real_fcntl(int fd, int cmd, ...) ;
int __wrap_fcntl(int fd, int cmd, ...) 
{
  va_list ap;
  void *arg;
  int ret;

  switch (cmd) {
    /* No arg */
    case F_GETFD : /* From kernel source fs/fcntl.c:do_fcntl() */
    case F_GETFL :
#if defined(F_GETOWN)
    case F_GETOWN :
#endif
#if defined(F_GETSIG)
    case F_GETSIG :
#endif
#if defined(F_GETLEASE)
    case F_GETLEASE :
#endif
      ret = __real_fcntl(fd, cmd, 0);
      break;
    default :
      va_start (ap, cmd);
      arg = va_arg (ap, void *);
      va_end (ap);
      ret = __real_fcntl(fd, cmd, arg);
      break;
  }
  switch (cmd) {
    case F_DUPFD :
      Tau_iowrap_checkInit();
      Tau_iowrap_dupEvents(fd, ret);
      break;
  }
  TAU_VERBOSE ("fcntl(fid=%d,cmd=%d...) called\n", fd, cmd);
  return ret;
}


/*********************************************************************
 * read
 ********************************************************************/
size_t __real_read(int fd, void *buf, size_t nbytes);
size_t __wrap_read(int fd, void *buf, size_t nbytes)
{
  int ret;
  double currentRead = 0.0;
  struct timeval t1, t2; 

  if (Tau_iowrap_checkPassThrough()) {
    return __real_read(fd, buf, nbytes);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "read()", " ", TAU_READ|TAU_IO);
  TAU_GET_IOWRAP_EVENT(re, READ_BW, fd);
  TAU_GET_IOWRAP_EVENT(bytesread, READ_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_read(fd, buf, nbytes);
  gettimeofday(&t2, 0);


  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */

  if ((currentRead > 1e-12) && (ret > 0)) {
    TAU_CONTEXT_EVENT(re, (double) ret/currentRead);
    TAU_CONTEXT_EVENT(global_read_bandwidth, (double) ret/currentRead);
  } else {
    TAU_VERBOSE("TauWrapperRead: currentRead = %g\n", ret);
  }

  if (ret > 0 ) {
    TAU_CONTEXT_EVENT(bytesread, ret);
    TAU_CONTEXT_EVENT(global_bytes_read, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(read_fd, "READ fd");
    TAU_REGISTER_EVENT(read_ret, "READ ret");
    TAU_EVENT(read_fd, fd);
    TAU_EVENT(read_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Read fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * fread
 ********************************************************************/
size_t __real_fread(void *ptr, size_t size, size_t nmemb, FILE *stream) ;
size_t __wrap_fread(void *ptr, size_t size, size_t nmemb, FILE *stream) 
{
  size_t ret;
  double currentRead = 0.0;
  struct timeval t1, t2; 
  unsigned long long count; 
  int fd;
  fd = fileno(stream);

  if (Tau_iowrap_checkPassThrough()) {
    return __real_fread(ptr, size, nmemb, stream);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fread()", " ", TAU_READ|TAU_IO);
  TAU_GET_IOWRAP_EVENT(re, READ_BW, fd);
  TAU_GET_IOWRAP_EVENT(bytesread, READ_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_fread(ptr, size, nmemb, stream);
  gettimeofday(&t2, 0);


  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  count = ret * size; 

  if ((currentRead > 1e-12) && (ret > 0)) {
    TAU_CONTEXT_EVENT(re, (double) count/currentRead);
    TAU_CONTEXT_EVENT(global_read_bandwidth, (double) count/currentRead);
  } else {
    TAU_VERBOSE("TauWrapperRead: currentRead = %g\n", ret);
  }

  if (ret > 0 ) {
    TAU_CONTEXT_EVENT(bytesread, count);
    TAU_CONTEXT_EVENT(global_bytes_read, count);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fread_fd, "FREAD fd");
    TAU_REGISTER_EVENT(fread_ret, "FREAD ret");
    TAU_EVENT(fread_fd, fileno(stream));
    TAU_EVENT(fread_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fread fd=%d size=%d nmemb=%d ret=%d\n", fd, size, nmemb, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * readv
 ********************************************************************/
ssize_t __real_readv(int fd, const struct iovec *vec, int count) ;
ssize_t __wrap_readv(int fd, const struct iovec *vec, int count) 
{
  ssize_t ret;
  double currentRead = 0.0;
  struct timeval t1, t2;



  if (Tau_iowrap_checkPassThrough()) {
    return __real_readv(fd, vec, count);
  }

  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "readv()", " ", TAU_READ|TAU_IO);
  TAU_GET_IOWRAP_EVENT(re, READ_BW, fd);
  TAU_GET_IOWRAP_EVENT(bytesread, READ_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_readv(fd, vec, count);
  gettimeofday(&t2, 0);

/* On success, the readv() function returns the number of bytes read; the
   writev() function returns the number of bytes written.  On error, -1 is
   returned, and errno is set appropriately. */

  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */

  if ((currentRead > 1e-12) && (ret > 0)) {
    TAU_CONTEXT_EVENT(re, (double) ret/currentRead);
    TAU_CONTEXT_EVENT(global_read_bandwidth, (double) ret/currentRead);
  } else {
    TAU_VERBOSE("TauWrapperRead: currentRead = %g\n", ret);
  }

  if (ret > 0 ) {
    TAU_CONTEXT_EVENT(bytesread, ret);
    TAU_CONTEXT_EVENT(global_bytes_read, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(read_fd, "READV fd");
    TAU_REGISTER_EVENT(read_ret, "READV ret");
    TAU_EVENT(read_fd, fd);
    TAU_EVENT(read_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Readv fd %d ret %d\n", fd, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * write
 ********************************************************************/
size_t __real_write(int fd, void *buf, size_t nbytes);
size_t __wrap_write(int fd, void *buf, size_t nbytes)
{
  int ret;
  double currentWrite = 0.0;
  struct timeval t1, t2; 
  double bw = 0.0; 

  if (Tau_iowrap_checkPassThrough()) {
    return __real_write(fd, buf, nbytes);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "write()", " ", TAU_WRITE|TAU_IO);
  TAU_GET_IOWRAP_EVENT(wb, WRITE_BW, fd);
  TAU_GET_IOWRAP_EVENT(byteswritten, WRITE_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_write(fd, buf, nbytes);
  gettimeofday(&t2, 0);

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  if ((currentWrite > 1e-12) && (ret > 0)) {
    bw = (double) ret/currentWrite;
    TAU_CONTEXT_EVENT(wb, bw);
    TAU_CONTEXT_EVENT(global_write_bandwidth, bw);
  } else {
    TAU_VERBOSE("TauWrapperWrite: currentWrite = %g\n", currentWrite);
  }
  if (ret > 0) {
    TAU_CONTEXT_EVENT(byteswritten, ret);
    TAU_CONTEXT_EVENT(global_bytes_written, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(write_fd, "WRITE fd");
    TAU_REGISTER_EVENT(write_ret, "WRITE ret");
    TAU_EVENT(write_fd, fd);
    TAU_EVENT(write_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Write fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * fwrite
 ********************************************************************/
size_t __real_fwrite( const void *ptr, size_t size, size_t nmemb, FILE *stream);
size_t __wrap_fwrite( const void *ptr, size_t size, size_t nmemb, FILE *stream)
{
  size_t ret;
  unsigned long long count;
  double currentWrite = 0.0;
  struct timeval t1, t2; 
  double bw = 0.0; 


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fwrite(ptr, size, nmemb, stream);
  }

  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fwrite()", " ", TAU_WRITE|TAU_IO);
  TAU_GET_IOWRAP_EVENT(wb, WRITE_BW, fileno(stream));
  TAU_GET_IOWRAP_EVENT(byteswritten, WRITE_BYTES, fileno(stream));
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_fwrite(ptr, size, nmemb, stream);
  gettimeofday(&t2, 0);

  count = ret * size;

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  if ((currentWrite > 1e-12) && (ret > 0)) {
    bw = (double) count/currentWrite;
    TAU_CONTEXT_EVENT(wb, bw);
    TAU_CONTEXT_EVENT(global_write_bandwidth, bw);
  } else {
    TAU_VERBOSE("TauWrapperWrite: currentWrite = %g\n", currentWrite);
  }
  if (ret > 0) {
    TAU_CONTEXT_EVENT(byteswritten, count);
    TAU_CONTEXT_EVENT(global_bytes_written, count);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fwrite_fd, "FWRITE fd");
    TAU_REGISTER_EVENT(fwrite_ret, "FWRITE ret");
    TAU_EVENT(fwrite_fd, fileno(stream));
    TAU_EVENT(fwrite_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fwrite size = %d nmemb %d ret %d\n", size, nmemb, ret);
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * writev
 ********************************************************************/
ssize_t __real_writev(int fd,  const struct iovec *vec, int count) ;
ssize_t __wrap_writev(int fd,  const struct iovec *vec, int count) 
{
  ssize_t ret;
  double currentWrite = 0.0;
  struct timeval t1, t2;
  double bw = 0.0;

  if (Tau_iowrap_checkPassThrough()) {
    return __real_writev(fd, vec, count);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "writev()", " ", TAU_WRITE|TAU_IO);
  TAU_GET_IOWRAP_EVENT(wb, WRITE_BW, fd);
  TAU_GET_IOWRAP_EVENT(byteswritten, WRITE_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_writev(fd, vec, count);
  gettimeofday(&t2, 0);

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  if ((currentWrite > 1e-12) && (ret > 0)) {
    bw = (double) ret/currentWrite;
    TAU_CONTEXT_EVENT(wb, bw);
    TAU_CONTEXT_EVENT(global_write_bandwidth, bw);
  } else {
    TAU_VERBOSE("TauWrapperWrite: currentWrite = %g\n", currentWrite);
  }
  if (ret > 0) {
    TAU_CONTEXT_EVENT(byteswritten, ret);
    TAU_CONTEXT_EVENT(global_bytes_written, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(write_fd, "WRITEV fd");
    TAU_REGISTER_EVENT(write_ret, "WRITEV ret");
    TAU_EVENT(write_fd, fd);
    TAU_EVENT(write_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Writev fd %d ret %d\n", fd, ret);  
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * pwrite
 ********************************************************************/
ssize_t __real_pwrite(int fd, void *buf, size_t nbytes, off_t offset);
ssize_t __wrap_pwrite(int fd, void *buf, size_t nbytes, off_t offset)
{
  ssize_t ret;
  double currentWrite = 0.0;
  struct timeval t1, t2; 
  double bw = 0.0; 

  if (Tau_iowrap_checkPassThrough()) {
    return __real_pwrite(fd, buf, nbytes, offset);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "pwrite()", " ", TAU_WRITE|TAU_IO);
  TAU_GET_IOWRAP_EVENT(wb, WRITE_BW, fd);
  TAU_GET_IOWRAP_EVENT(byteswritten, WRITE_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_pwrite(fd, buf, nbytes, offset);
  gettimeofday(&t2, 0);

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  if ((currentWrite > 1e-12) && (ret > 0)) {
    bw = (double) ret/currentWrite;
    TAU_CONTEXT_EVENT(wb, bw);
    TAU_CONTEXT_EVENT(global_write_bandwidth, bw);
  } else {
    TAU_VERBOSE("TauWrapperWrite: currentWrite = %g\n", currentWrite);
  }
  if (ret > 0) {
    TAU_CONTEXT_EVENT(byteswritten, ret);
    TAU_CONTEXT_EVENT(global_bytes_written, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(pwrite_fd, "PWRITE fd");
    TAU_REGISTER_EVENT(pwrite_ret, "PWRITE ret");
    TAU_REGISTER_EVENT(pwrite_offset, "PWRITE offset");
    TAU_EVENT(pwrite_fd, fd);
    TAU_EVENT(pwrite_ret, ret);
    TAU_EVENT(pwrite_ret, offset);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Pwrite fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * pwrite64
 ********************************************************************/
ssize_t __real_pwrite64(int fd, void *buf, size_t nbytes, off64_t offset);
ssize_t __wrap_pwrite64(int fd, void *buf, size_t nbytes, off64_t offset)
{
  ssize_t ret;
  double currentWrite = 0.0;
  struct timeval t1, t2;
  double bw = 0.0;

  if (Tau_iowrap_checkPassThrough()) {
    return __real_pwrite64(fd, buf, nbytes, offset);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "pwrite64()", " ", TAU_WRITE|TAU_IO);
  TAU_GET_IOWRAP_EVENT(wb, WRITE_BW, fd);
  TAU_GET_IOWRAP_EVENT(byteswritten, WRITE_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_pwrite64(fd, buf, nbytes, offset);
  gettimeofday(&t2, 0);

  /* calculate the time spent in operation */
  currentWrite = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */
  if ((currentWrite > 1e-12) && (ret > 0)) {
    bw = (double) ret/currentWrite;
    TAU_CONTEXT_EVENT(wb, bw);
    TAU_CONTEXT_EVENT(global_write_bandwidth, bw);
  } else {
    TAU_VERBOSE("TauWrapperWrite: currentWrite = %g\n", currentWrite);
  }
  if (ret > 0) {
    TAU_CONTEXT_EVENT(byteswritten, ret);
    TAU_CONTEXT_EVENT(global_bytes_written, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(write_fd, "PWRITE64 fd");
    TAU_REGISTER_EVENT(write_ret, "PWRITE64 ret");
    TAU_EVENT(write_fd, fd);
    TAU_EVENT(write_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Pwrite64 fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}



/*********************************************************************
 * pread
 ********************************************************************/
ssize_t __real_pread(int fd, void *buf, size_t nbytes, off_t offset);
ssize_t __wrap_pread(int fd, void *buf, size_t nbytes, off_t offset)
{
  ssize_t ret;
  double currentRead = 0.0;
  struct timeval t1, t2; 

  if (Tau_iowrap_checkPassThrough()) {
    return __real_pread(fd, buf, nbytes, offset);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "pread()", " ", TAU_READ|TAU_IO);
  TAU_GET_IOWRAP_EVENT(re, READ_BW, fd);
  TAU_GET_IOWRAP_EVENT(bytesread, READ_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_pread(fd, buf, nbytes, offset);
  gettimeofday(&t2, 0);


  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */

  if ((currentRead > 1e-12) && (ret > 0)) {
    TAU_CONTEXT_EVENT(re, (double) ret/currentRead);
    TAU_CONTEXT_EVENT(global_read_bandwidth, (double) ret/currentRead);
  } else {
    TAU_VERBOSE("TauWrapperRead: currentRead = %g\n", ret);
  }

  if (ret > 0 ) {
    TAU_CONTEXT_EVENT(bytesread, ret);
    TAU_CONTEXT_EVENT(global_bytes_read, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(pread_fd, "PREAD fd");
    TAU_REGISTER_EVENT(pread_ret, "PREAD ret");
    TAU_REGISTER_EVENT(pread_offset, "PREAD offset");
    TAU_EVENT(pread_fd, fd);
    TAU_EVENT(pread_ret, ret);
    TAU_EVENT(pread_offset, offset);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("pread fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * pread64
 ********************************************************************/
ssize_t __real_pread64(int fd, void *buf, size_t nbytes, off64_t offset);
ssize_t __wrap_pread64(int fd, void *buf, size_t nbytes, off64_t offset)
{
  ssize_t ret;
  double currentRead = 0.0;
  struct timeval t1, t2; 

  if (Tau_iowrap_checkPassThrough()) {
    return __real_pread64(fd, buf, nbytes, offset);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "pread64()", " ", TAU_READ|TAU_IO);
  TAU_GET_IOWRAP_EVENT(re, READ_BW, fd);
  TAU_GET_IOWRAP_EVENT(bytesread, READ_BYTES, fd);
  TAU_PROFILE_START(t);

  gettimeofday(&t1, 0);
  ret = __real_pread64(fd, buf, nbytes, offset);
  gettimeofday(&t2, 0);


  /* calculate the time spent in operation */
  currentRead = (double) (t2.tv_sec - t1.tv_sec) * 1.0e6 + (t2.tv_usec - t1.tv_usec);
  /* now we trigger the events */

  if ((currentRead > 1e-12) && (ret > 0)) {
    TAU_CONTEXT_EVENT(re, (double) ret/currentRead);
    TAU_CONTEXT_EVENT(global_read_bandwidth, (double) ret/currentRead);
  } else {
    TAU_VERBOSE("TauWrapperRead: currentRead = %g\n", ret);
  }

  if (ret > 0 ) {
    TAU_CONTEXT_EVENT(bytesread, ret);
    TAU_CONTEXT_EVENT(global_bytes_read, ret);
  }

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(read_fd, "PREAD64 fd");
    TAU_REGISTER_EVENT(read_ret, "PREAD64 ret");
    TAU_EVENT(read_fd, fd);
    TAU_EVENT(read_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("pread64 fd %d nbytes %d buf %ld ret %d\n", fd, nbytes, (long)buf, ret);
  Tau_global_decr_insideTAU();

  return ret;
}




/*********************************************************************
 * close
 ********************************************************************/
size_t __real_close(int fd);
size_t __wrap_close(int fd)
{
  int ret;

  if (Tau_iowrap_checkPassThrough()) {
    return __real_close(fd);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "close()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_close(fd);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(close_fd, "CLOSE fd");
    TAU_REGISTER_EVENT(close_ret, "CLOSE ret");
    TAU_EVENT(close_fd, fd);
    TAU_EVENT(close_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("Close fd %d ret %d\n", fd, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * fclose
 ********************************************************************/
int __real_fclose(FILE *fp);
int __wrap_fclose(FILE *fp)
{
  int ret;
  int fd; 


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fclose(fp);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  fd = fileno(fp);
  TAU_PROFILE_TIMER(t, "fclose()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fclose(fp);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(close_fd, "CLOSE fd");
    TAU_REGISTER_EVENT(close_ret, "CLOSE ret");
    TAU_EVENT(close_fd, fd);
    TAU_EVENT(close_ret, ret);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fclose called on fd %d ret %d\n", fd, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * fdatasync
 ********************************************************************/
int __real_fdatasync(int fd);
int __wrap_fdatasync(int fd)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fdatasync(fd);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fdatasync()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fdatasync(fd);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fsyncdata_fd, "FSYNCDATA fd");
    TAU_REGISTER_EVENT(fsyncdata_ret, "FSYNCDATA ret");
    TAU_EVENT(fsyncdata_fd, fd);
    TAU_EVENT(fsyncdata_ret, ret);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fdatasync called on fd %d ret %d\n", fd, ret);
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * lseek
 ********************************************************************/
off_t __real_lseek(int fd, off_t offset, int whence) ;
off_t __wrap_lseek(int fd, off_t offset, int whence) 
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_lseek(fd, offset, whence);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "lseek()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_lseek(fd, offset, whence);

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
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * lseek64
 ********************************************************************/
off64_t __real_lseek64(int fd, off64_t offset, int whence);
off64_t __wrap_lseek64(int fd, off64_t offset, int whence)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_lseek64(fd, offset, whence);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "lseek64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_lseek64(fd, offset, whence);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(lseek64_fd, "LSEEK fd");
    TAU_REGISTER_EVENT(lseek64_offset, "LSEEK offset");
    TAU_REGISTER_EVENT(lseek64_whence, "LSEEK whence");
    TAU_EVENT(lseek64_fd, fd);
    TAU_EVENT(lseek64_offset, offset);
    TAU_EVENT(lseek64_whence, whence);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("lseek64 called\n");
  Tau_global_decr_insideTAU();

  return ret;
}


/*********************************************************************
 * fseek
 ********************************************************************/
off_t __real_fseek(FILE *stream, long offset, int whence) ;
off_t __wrap_fseek(FILE *stream, long offset, int whence) 
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fseek(stream, offset, whence);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fseek()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fseek(stream, offset, whence);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fseek_offset, "FSEEK offset");
    TAU_REGISTER_EVENT(fseek_whence, "FSEEK whence");
    TAU_REGISTER_EVENT(fseek_ret, "FSEEK ret");
    TAU_EVENT(fseek_offset, offset);
    TAU_EVENT(fseek_whence, whence);
    TAU_EVENT(fseek_ret, ret);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fseek called\n");
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * stat
 ********************************************************************/
int __real_stat(const char *path, struct stat *buf) ;
int __wrap_stat(const char *path, struct stat *buf) 
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_stat(path, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "stat()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_stat(path, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(stat_ret, "STAT ret");
    TAU_EVENT(stat_ret, ret);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("stat called: path=%s\n", path);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * stat64
 ********************************************************************/
int __real_stat64(const char *path, struct stat *buf);
int __wrap_stat64(const char *path, struct stat *buf)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_stat64(path, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "stat64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_stat64(path, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(stat64_ret, "STAT64 ret");
    TAU_EVENT(stat64_ret, ret);
  }


  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("stat64 called: path=%s\n", path);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * fstat
 ********************************************************************/
int __real_fstat(int filedes, STRUCT_STAT64 *buf);
int __wrap_fstat(int filedes, STRUCT_STAT64 *buf)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fstat(filedes, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fstat()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fstat(filedes, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fstat_filedes, "FSTAT filedes");
    TAU_REGISTER_EVENT(fstat_ret, "FSTAT ret");
    TAU_EVENT(fstat_filedes, filedes);
    TAU_EVENT(fstat_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fstat called: filedes=%d\n", filedes);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * fstat64
 ********************************************************************/
int __real_fstat64(int filedes, STRUCT_STAT64 *buf);
int __wrap_fstat64(int filedes, STRUCT_STAT64 *buf)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_fstat64(filedes, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "fstat64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_fstat64(filedes, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(fstat64_filedes, "FSTAT64 filedes");
    TAU_REGISTER_EVENT(fstat64_ret, "FSTAT64 ret");
    TAU_EVENT(fstat64_filedes, filedes);
    TAU_EVENT(fstat64_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("fstat64 called: filedes=%d\n", filedes);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * lstat
 ********************************************************************/
int __real_lstat(const char *path, struct stat *buf);
int __wrap_lstat(const char *path, struct stat *buf)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_lstat(path, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "lstat()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_lstat(path, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(lstat_ret, "LSTAT ret");
    TAU_EVENT(lstat_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("lstat called: path=%s\n", path);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * lstat64
 ********************************************************************/
int __real_lstat64(const char *path, STRUCT_STAT64 *buf);
int __wrap_lstat64(const char *path, STRUCT_STAT64 *buf)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_lstat64(path, buf);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "lstat64()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_lstat64(path, buf);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(lstat64_ret, "LSTAT64 ret");
    TAU_EVENT(lstat64_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("lstat64 called: path=%s\n", path);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * dup
 ********************************************************************/
int __real_dup(int filedes);
int __wrap_dup(int filedes)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_dup(filedes);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "dup()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_dup(filedes);
  Tau_iowrap_dupEvents(filedes, ret);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(dup_ret, "DUP ret");
    TAU_REGISTER_EVENT(dup_filedes, "DUP filedes");
    TAU_EVENT(dup_filedes, filedes);
    TAU_EVENT(dup_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("dup called: filedes=%d\n", filedes);
  Tau_global_decr_insideTAU();

  return ret;

}

/*********************************************************************
 * dup2
 ********************************************************************/
int __real_dup2(int filedes1, int filedes2);
int __wrap_dup2(int filedes1, int filedes2)
{
  int ret;


  if (Tau_iowrap_checkPassThrough()) {
    return __real_dup2(filedes1, filedes2);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "dup2()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_dup2(filedes1, filedes2);
  Tau_iowrap_dupEvents(filedes1, ret);

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(dup2_ret, "DUP2 ret");
    TAU_REGISTER_EVENT(dup2_filedes1, "DUP filedes1");
    TAU_REGISTER_EVENT(dup2_filedes2, "DUP filedes2");
    TAU_EVENT(dup2_filedes1, filedes1);
    TAU_EVENT(dup2_filedes2, filedes2);
    TAU_EVENT(dup2_ret, ret);
  }

  TAU_PROFILE_STOP(t);
  TAU_VERBOSE("dup2 called: filedes1=%d, filedes2=%d\n", filedes1, filedes2);
  Tau_global_decr_insideTAU();

  return ret;

}


/*********************************************************************
 * select
 ********************************************************************/
int __real_select(int nfds, fd_set *readfds, fd_set *writefds, 
  fd_set *exceptfds, const struct timeval *timeout);
int __wrap_select(int nfds, fd_set *readfds, fd_set *writefds, 
  fd_set *exceptfds, const struct timeval *timeout)
{
  int ret;

  if (Tau_iowrap_checkPassThrough()) {
    return __real_select(nfds, readfds, writefds, exceptfds, timeout);
  }
  Tau_global_incr_insideTAU();
  Tau_iowrap_checkInit();
  TAU_PROFILE_TIMER(t, "select()", " ", TAU_IO);
  TAU_PROFILE_START(t);

  ret = __real_select(nfds, readfds, writefds, exceptfds, timeout); 

  if (TauEnv_get_track_io_params()) {
    TAU_REGISTER_EVENT(select_nfds, "select nfds");
    TAU_REGISTER_EVENT(select_ret, "select ret");
    TAU_EVENT(select_nfds, nfds);
    TAU_EVENT(select_ret, ret);
  }

  TAU_VERBOSE("Select nfds %d ret %d\n", nfds, ret);

  TAU_PROFILE_STOP(t);
  Tau_global_decr_insideTAU();

  return ret;
}

/*********************************************************************
 * EOF
 ********************************************************************/
