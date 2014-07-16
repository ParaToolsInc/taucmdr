/**
 * VampirTrace
 * http://www.tu-dresden.de/zih/vampirtrace
 *
 * Copyright (c) 2005-2006, ZIH, TU Dresden, Federal Republic of Germany
 *
 * Copyright (c) 1998-2005, Forschungszentrum Juelich GmbH, Federal
 * Republic of Germany
 *
 * See the file COPYRIGHT in the package base directory for details
 **/

#ifndef _VT_INTTYPES_H
#define _VT_INTTYPES_H

/*

define convenient integer types in case neither 'inttypes.h' nor 'stdint.h'
is available on a platform, e.g. for NEC SX6

*/

#if HAVE_CONFIG_H
#  include <config.h>
#endif

#if defined HAVE_STDINT_H
#  include <stdint.h>
#elif defined HAVE_INTTYPES_H
#  include <inttypes.h>
#else /* HAVE_INTTYPES_H || HAVE_STDINT_H */

/* Signed. */
typedef signed char             int8_t;
typedef signed short int        int16_t;
typedef signed int  	        int32_t;

#if SIZEOF_LONG == 8
typedef signed long int         int64_t;
#else /* SIZEOF_LONG */
typedef signed long long int    int64_t;
#endif /* SIZEOF_LONG */


/* Unsigned. */
typedef unsigned char           uint8_t;
typedef unsigned short int      uint16_t;
typedef unsigned int            uint32_t;

#if SIZEOF_LONG == 8
typedef unsigned long int       uint64_t;
#else /* SIZEOF_LONG */
typedef unsigned long long int  uint64_t;
#endif /* SIZEOF_LONG */


#endif /* HAVE_INTTYPES_H || HAVE_STDINT_H */


#endif /* _VT_INTTYPES_H */
