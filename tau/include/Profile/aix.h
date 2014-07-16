#ifndef _AIX_H_
#define _AIX_H_

#ifndef _XOPEN_SOURCE
#define _XOPEN_SOURCE


//#define _XOPEN _SOURCE
//#define _XOPEN_SOURCE_EXTENDED 1

#ifndef _TIME_T
#define _TIME_T
typedef long            time_t;
#endif

#ifndef _SIZE_T
#define _SIZE_T
typedef unsigned long   size_t;
#endif


#ifndef KAI
#ifndef __GNUC__
struct timeval {
        time_t          tv_sec;         /* seconds */
        long            tv_usec;        /* microseconds */
};
#endif /* __GNUC__ */
#endif // KAI

#ifdef __cplusplus
extern "C" {
#endif /*__cplusplus */
#ifndef __GNUC__
int              getdtablesize(void);
#ifndef KAI
int gettimeofday(struct timeval *, void *);
#endif // KAI
#endif /* __GNUC__ */
int  strncasecmp(const char *, const char *, size_t);
int  strcasecmp(const char *, const char *);
#ifdef __cplusplus 
}
#endif /* __cplusplus */
/*
extern "C" {
//#include <sys/types.h>
//#include <unistd.h>
//extern int     getopt(int, char* const*, const char*);
}
*/
#endif /* XOPEN_SOURCE */
#endif /* _AIX_H_ */
