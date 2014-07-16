// -*- C++ -*-
//
//-----------------------------------------------------------------------------
//
//                       TAU Development Team
//                       University of Oregon, Los Alamos National Laboratory,
//                       FZJ Germany
//                       (C) 2003 All Rights Reserved
//
// <LicenseText>
//
//-----------------------------------------------------------------------------
//
// $Log: PyTimer.h,v $
// Revision 1.2  2007/03/01 22:14:37  amorris
// Added phase API for python
//
// Revision 1.1  2003/02/28 23:29:09  sameer
// Added Python Bindings  headers to TAU.
//
// 

#if !defined(pytau_timer_h)
#define pytau_timer_h


extern char pytau_profileTimer__name__[];
extern char pytau_profileTimer__doc__[];
extern "C"
PyObject * pytau_profileTimer(PyObject *, PyObject *);

extern char pytau_phase__name__[];
extern char pytau_phase__doc__[];
extern "C"
PyObject * pytau_phase(PyObject *, PyObject *);

extern char pytau_start__name__[];
extern char pytau_start__doc__[];
extern "C"
PyObject * pytau_start(PyObject *, PyObject *);

extern char pytau_stop__name__[];
extern char pytau_stop__doc__[];
extern "C"
PyObject * pytau_stop(PyObject *, PyObject *);

extern char pytau_registerEvent__name__[];
extern char pytau_registerEvent__doc__[];
extern "C"
PyObject * pytau_registerEvent(PyObject *, PyObject *);

extern char pytau_event__name__[];
extern char pytau_event__doc__[];
extern "C"
PyObject * pytau_event(PyObject *, PyObject *);

#endif // pytau_timer_h
// version
// $Id: PyTimer.h,v 1.2 2007/03/01 22:14:37 amorris Exp $

// End of file
