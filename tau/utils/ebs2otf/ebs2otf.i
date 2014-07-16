/* ebs2otf.i */
%module ebs2otf
%{
  #include "otf.h"
%}


%apply unsigned int { uint32_t }
%apply unsigned long long { uint64_t }

%include "OTF_CopyHandler.h"
%include "OTF_FileManager.h"
%include "OTF_inttypes.h"
%include "OTF_Reader.h"
%include "OTF_Writer.h"
%include "OTF_Definitions.h"
%include "OTF_Filenames.h"
%include "OTF_inttypes_unix.h"
%include "OTF_RStream.h"
%include "OTF_WStream.h"
%include "OTF_Errno.h"
%include "otf.h"
%include "OTF_MasterControl.h"
%include "OTF_Version.h"
%include "OTF_File.h"
%include "OTF_HandlerArray.h"
%include "OTF_RBuffer.h"
%include "OTF_WBuffer.h"
%include "OTF_KeyValue.h"
