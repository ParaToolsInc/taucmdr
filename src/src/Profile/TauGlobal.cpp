/******************************************************************************
 *
 *                        The TAU Performance System
 *                          http://tau.uoregon.edu/
 *
 * Copyright 1997-2014
 * Department of Computer and Information Science, University of Oregon
 * Advanced Computing Laboratory, Los Alamos National Laboratory
 *
 *****************************************************************************/
/**
 * @file
 * @brief
 * @date    Created 2014-06-27
 *
 * @authors
 * Adam Morris <amorris@cs.uoregon.edu>
 * Kevin Huck <khuck@cs.uoregon.edu>
 * Sameer Shende <sameer@cs.uoregon.edu>
 * Scott Biersdorff <scottb@cs.uoregon.edu>
 * Wyatt Joel Spear <wspear@cs.uoregon.edu>
 * John C. Linford <jlinford@paratools.com>
 *
 * @copyright
 * Copyright (c) 1997-2014
 * Department of Computer and Information Science, University of Oregon
 * Advanced Computing Laboratory, Los Alamos National Laboratory
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * (1) Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 * (2) Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 * (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
 *     be used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

#include <vector>
#include <Profile/FunctionInfo.h>
#include <Profile/TauInit.h>

using namespace std;


namespace tau {
//=============================================================================


//////////////////////////////////////////////////////////////////////
// Instead of using a global var., use static inside a function  to
// ensure that non-local static variables are initialised before being
// used (Ref: Scott Meyers, Item 47 Eff. C++).
//
// FunctionDB contains pointers to each FunctionInfo static object
//////////////////////////////////////////////////////////////////////
FIvector & TheFunctionDB()
{
  static FIvector FunctionDB;
  return FunctionDB;
}

//////////////////////////////////////////////////////////////////////
// It is not safe to call Profiler::StoreData() after
// FunctionInfo::~FunctionInfo has been called as names are null
//////////////////////////////////////////////////////////////////////
int & TheSafeToDumpData()
{
  static int SafeToDumpData = 1;
  return SafeToDumpData;
}

//////////////////////////////////////////////////////////////////////
// Set when uning Dyninst
//////////////////////////////////////////////////////////////////////
int & TheUsingDyninst()
{
  static int UsingDyninst = 0;
  return UsingDyninst;
}

//////////////////////////////////////////////////////////////////////
// Set when uning Compiler Instrumentation
//////////////////////////////////////////////////////////////////////
int & TheUsingCompInst()
{
  static int UsingCompInst = 0;
  return UsingCompInst;
}


//=============================================================================
} // END namespace tau

