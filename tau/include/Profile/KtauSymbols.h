/****************************************************************************
**			TAU Portable Profiling Package			   **
**			http://www.acl.lanl.gov/tau		           **
*****************************************************************************
**    Copyright 1997  						   	   **
**    Department of Computer and Information Science, University of Oregon **
**    Advanced Computing Laboratory, Los Alamos National Laboratory        **
****************************************************************************/
/***************************************************************************
**	File 		: KtauSymbols.h					  **
**	Description 	: TAU Kernel Profiling Interface		  **
**	Author		: Aroon Nataraj					  **
**			: Suravee Suthikulpanit				  **
**	Contact		: {suravee,anataraj}@cs.uoregon.edu               **
**	Flags		: Compile with				          **
**			  -DTAU_KTAU to enable KTAU	                  **
**	Documentation	: 					          **
***************************************************************************/

#ifndef _KTAUSYMBOLS_H_
#define _KTAUSYMBOLS_H_

//--------------------------------------------------------

#include <string>
#include <map>

// Putting "using namespace" statements in header files can create ambiguity
// between user-defined symbols and std symbols, creating unparsable code
// or even changing the behavior of user codes.  This is also widely considered
// to be bad practice.  Here's a code PDT can't parse because of this line:
//   EX: #include <complex>
//   EX: typedef double real;
//
//using namespace std;

class KtauSymbols {

	public:
	//cons / dest
	KtauSymbols(const std::string& path);
	~KtauSymbols();

	std::string& MapSym(unsigned int);
	unsigned long MapRevSym(std::string);
	int ReadKallsyms();

	private:
	//stl map to hold the addr-to-name lookup data
	typedef std::map<unsigned int, std::string> KERN_SYMTAB;
	KERN_SYMTAB table;
	typedef std::map<std::string, unsigned long> KERN_REV_SYMTAB;
	KERN_REV_SYMTAB rev_table;

	//file-path to the kernel-symbol info
	const std::string filepath;
};

#endif /* _KTAUSYMBOLS_H_  */
/***************************************************************************
 * $RCSfile: KtauSymbols.h,v $   $Author: anataraj $
 * $Revision: 1.2 $   $Date: 2007/04/19 03:21:44 $
 * POOMA_VERSION_ID: $Id: KtauSymbols.h,v 1.2 2007/04/19 03:21:44 anataraj Exp $ 
 ***************************************************************************/

