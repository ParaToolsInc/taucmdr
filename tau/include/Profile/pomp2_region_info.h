/*
 * This file is part of the Score-P software (http://www.score-p.org)
 *
 * Copyright (c) 2009-2011,
 *    RWTH Aachen University, Germany
 *    Gesellschaft fuer numerische Simulation mbH Braunschweig, Germany
 *    Technische Universitaet Dresden, Germany
 *    University of Oregon, Eugene, USA
 *    Forschungszentrum Juelich GmbH, Germany
 *    German Research School for Simulation Sciences GmbH, Juelich/Aachen, Germany
 *    Technische Universitaet Muenchen, Germany
 *
 * See the COPYING file in the package base directory for details.
 *
 */
/****************************************************************************
**  SCALASCA    http://www.scalasca.org/                                   **
**  KOJAK       http://www.fz-juelich.de/jsc/kojak/                        **
*****************************************************************************
**  Copyright (c) 1998-2009                                                **
**  Forschungszentrum Juelich, Juelich Supercomputing Centre               **
**                                                                         **
**  See the file COPYRIGHT in the package base directory for details       **
****************************************************************************/
#ifdef __cplusplus
 extern "C" {
#endif
#ifndef POMP2_REGION_INFO_H
#define POMP2_REGION_INFO_H

/**
 * @file    pomp2_region_info.h
 * @author  Christian R&ouml;ssel <c.roessel@fz-juelich.de>
 * @status     alpha
 * @date    Started Fri Mar 20 16:30:45 2009
 *
 * @brief This file contains function declarations and structs
 * which handle informations on OpenMP regions. POMP2_Region_info
 * is used to store these informations. It can be filled with a
 * ctcString by ctcString2RegionInfo().
 *
 */

#include <stdbool.h>

/**
 * POMP2_Region_type
 *
 */
typedef enum /* POMP2_Region_type */
{
    POMP2_No_type,
    POMP2_Atomic,
    POMP2_Barrier,
    POMP2_Critical,
    POMP2_Do,
    POMP2_Flush,
    POMP2_For,
    POMP2_Master,
    POMP2_Ordered,
    POMP2_Parallel,
    POMP2_Parallel_do,
    POMP2_Parallel_for,
    POMP2_Parallel_sections,
    POMP2_Parallel_workshare,
    POMP2_Sections,
    POMP2_Single,
    POMP2_Task,
    POMP2_Taskuntied,
    POMP2_Taskwait,
    POMP2_User_region,
    POMP2_Workshare
} POMP2_Region_type;

/** converts regionType into a string
 * @param regionType The regionType to be converted.
 * @return string representation of the region type*/
const char*
pomp2RegionType2String( POMP2_Region_type regionType );

/**
 * type to store the scheduling type of a for worksharing constuct
 *
 */
typedef enum
{
    POMP2_No_schedule,
    POMP2_Static,  /* needs chunk size */
    POMP2_Dynamic, /* needs chunk size */
    POMP2_Guided,  /* needs chunk size */
    POMP2_Runtime,
    POMP2_Auto
} POMP2_Schedule_type;

/** converts scheduleType into a string
 *  @param scheduleType The scheduleType to be converted.
 *  @return string representation of the scheduleType*/
const char*
pomp2ScheduleType2String( POMP2_Schedule_type scheduleType );

/**
 *  @brief This struct stores all information on an OpenMP region, like the
 *  region type or corresponding source lines. The function
 *  ctcString2RegionInfo() can be used to fill this struct with data
 *  from a ctcString.
 */
typedef struct
{
    /** @name Required attributes
     */
    /*@{*/
    /** type of the OpenMP region*/
    POMP2_Region_type mRegionType;
    /** name of the corresponding source file from the opening pragma */
    char*             mStartFileName;
    /** line number of the first line from the opening pragma */
    unsigned          mStartLine1;
    /** line number of the last line from the opening pragma */
    unsigned          mStartLine2;
    /** name of the corresponding source file from the closing pragma */
    char*             mEndFileName;
    /** line number of the first line from the closing pragma */
    unsigned          mEndLine1;
    /** line number of the last line from the closing pragma */
    unsigned          mEndLine2;
    /*@}*/

    /** @name Currently not provided by opari
     */
    /*@{*/
    /**true if a copyin clause is present*/
    bool mHasCopyIn;
    /**true if a copyprivate clause is present*/
    bool mHasCopyPrivate;
    /**true if an if clause is present*/
    bool mHasIf;
    /**true if a firstprivate clause is present*/
    bool mHasFirstPrivate;
    /**true if a lastprivate clause is present*/
    bool mHasLastPrivate;
    /**true if a nowait clause is present*/
    bool mHasNoWait;
    /**true if a numThreads clause is present*/
    bool mHasNumThreads;
    /**true if an ordered clause is present*/
    bool mHasOrdered;
    /**true if a reduction clause is present*/
    bool mHasReduction;
    /**true if a collapse clause is present*/
    bool mHasCollapse;
    /**true if a untied clause was present, even if the task was changed to tied
       during instrumentation.*/
    bool                mHasUntied;
    /** schedule type in the schedule clause*/
    POMP2_Schedule_type mScheduleType;
    /** user group name*/
    char*               mUserGroupName;
    /*@}*/

    /** @name Attributes for specific region types
     */
    /*@{*/
    /** number of sections*/
    unsigned mNumSections;
    /** name of a named critical region*/
    char*    mCriticalName;
    /** name of a user defined region*/
    char*    mUserRegionName;
    /*@}*/
} POMP2_Region_info;

/**
 * ctcString2RegionInfo() fills the POMP2_Region_info object with data read
 * from the ctcString. If the ctcString does not comply with the
 * specification, the program aborts with exit code 1. @n Rationale:
 * ctcString2RegionInfo() is used during initialization of the measurement
 * system. If an error occurs, it is better to abort than to struggle with
 * undefined behaviour or @e guessing the meaning of the broken string.
 *
 * @note Can be called from multiple threads concurrently, assuming malloc is
 * thread-safe.
 *
 * @note ctcString2RegionInfo() will assign memory to the members of @e
 * regionInfo. You are supposed to to release this memory by calling
 * freePOMP2RegionInfoMembers().
 *
 * @param ctcString A string in the format
 * "length*key=value*[key=value]*". The length field is parsed but not used by
 * this implementation. Possible values for key are listed in
 * ctcTokenMap. The string must at least contain values for the keys @c
 * regionType, @c sscl and @c escl. Possible values for the key @c regionType
 * are listed in regionTypesMap. The format for @c sscl resp. @c escl values
 * is @c "filename:lineNo1:lineNo2".
 *
 * @param regionInfo must be a valid object
 *
 * @post At least the required attributes (see POMP2_Region_info) are set. @n
 * All other members of @e regionInfo are set to 0 resp. false
 * resp. POMP2_No_schedule. @n If @c regionType=sections than
 * POMP2_Region_info::mNumSections has a value > 0. @n If @c regionType=region
 * than POMP2_Region_info::mUserRegionName has a value != 0. @n If @c
 * regionType=critical than POMP2_Region_info::mCriticalName may have a value
 * != 0.
 *
 */
void
ctcString2RegionInfo( const char         ctcString[],
                      POMP2_Region_info* regionInfo );

/**
 * Free the memory of the regionInfo members.
 * @param regionInfo The regioninfo to be freed.
 */
void
freePOMP2RegionInfoMembers( POMP2_Region_info* regionInfo );


#endif /* POMP2_REGION_INFO_H */

#ifdef __cplusplus
}
#endif
