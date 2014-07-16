// -*- C++ -*-
//
//-----------------------------------------------------------------------------
//
//                       VTF Development Team
//                       California Institute of Technology
//                       (C) 2002 All Rights Reserved
//
// <LicenseText>
//
//-----------------------------------------------------------------------------
//
// $Log: PyDatabase.h,v $
// Revision 1.5  2010/03/30 23:03:22  amorris
// Missed one file in committing python dbMergeDump.
//
// Revision 1.4  2008/10/24 22:48:46  sameer
// Added pytau.exit(msg) binding.
//
// Revision 1.3  2008/09/15 23:27:45  sameer
// Added pytau_setNode(<node>) API call:
// import pytau
// pytau.setNode(353)
//
// 	creates profile.353.0.0 file.
// Scott,
// 	Would you please document this in the users guide?
// 	Thanks!
//
// Revision 1.2  2007/03/02 02:35:37  amorris
// Added snapshot API for python
//
// Revision 1.1  2003/02/28 23:29:08  sameer
// Added Python Bindings  headers to TAU.
//
// Revision 1.2  2002/11/14 02:28:50  cummings
// Added bindings for some new Tau functions that let you access the
// profiling statistics database at run time.
//
// Revision 1.1  2002/01/16 02:05:07  cummings
// Original source and build procedure files for Python bindings of
// TAU runtime API.  These bindings allow you to do some rudimentary
// things from the Python script, such as enable/disable all Tau
// instrumentation, enable/disable a particular Tau profile group,
// and dump or purge the current Tau statistics.  Still to come are
// bindings for creating and using Tau global timers and user events.
//
// 

#if !defined(pytau_database_h)
#define pytau_database_h

extern char pytau_snapshot__name__[];
extern char pytau_snapshot__doc__[];
extern "C"
PyObject * pytau_snapshot(PyObject *, PyObject *);

extern char pytau_exit__name__[];
extern char pytau_exit__doc__[];
extern "C"
PyObject * pytau_exit(PyObject *, PyObject *);

extern char pytau_dbDump__name__[];
extern char pytau_dbDump__doc__[];
extern "C"
PyObject * pytau_dbDump(PyObject *, PyObject *);

extern char pytau_dbMergeDump__name__[];
extern char pytau_dbMergeDump__doc__[];
extern "C"
PyObject * pytau_dbMergeDump(PyObject *, PyObject *);

extern char pytau_dbDumpIncr__name__[];
extern char pytau_dbDumpIncr__doc__[];
extern "C"
PyObject * pytau_dbDumpIncr(PyObject *, PyObject *);

extern char pytau_dbPurge__name__[];
extern char pytau_dbPurge__doc__[];
extern "C"
PyObject * pytau_dbPurge(PyObject *, PyObject *);

extern char pytau_getFuncNames__name__[];
extern char pytau_getFuncNames__doc__[];
extern "C"
PyObject * pytau_getFuncNames(PyObject *, PyObject *);

extern char pytau_dumpFuncNames__name__[];
extern char pytau_dumpFuncNames__doc__[];
extern "C"
PyObject * pytau_dumpFuncNames(PyObject *, PyObject *);

extern char pytau_getCounterNames__name__[];
extern char pytau_getCounterNames__doc__[];
extern "C"
PyObject * pytau_getCounterNames(PyObject *, PyObject *);

extern char pytau_getFuncVals__name__[];
extern char pytau_getFuncVals__doc__[];
extern "C"
PyObject * pytau_getFuncVals(PyObject *, PyObject *);

extern char pytau_dumpFuncVals__name__[];
extern char pytau_dumpFuncVals__doc__[];
extern "C"
PyObject * pytau_dumpFuncVals(PyObject *, PyObject *);

extern char pytau_dumpFuncValsIncr__name__[];
extern char pytau_dumpFuncValsIncr__doc__[];
extern "C"
PyObject * pytau_dumpFuncValsIncr(PyObject *, PyObject *);

extern char pytau_setNode__name__[];
extern char pytau_setNode__doc__[];
extern "C"
PyObject * pytau_setNode(PyObject *, PyObject *);

extern char pytau_metadata__name__[];
extern char pytau_metadata__doc__[];
extern "C"
PyObject * pytau_metadata(PyObject *, PyObject *);

#endif // pytau_database_h

// version
// $Id: PyDatabase.h,v 1.5 2010/03/30 23:03:22 amorris Exp $

// End of file
