"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief 

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# System modules
import sys
import traceback

# TAU modules
from tau import HELP_CONTACT, EXIT_FAILURE, EXIT_WARNING 
from logger import getLogger, LOG_LEVEL


LOGGER = logger.getLogger('error')


class Error(Exception):
  """
  Base class for errors in Tau
  """
  
  message_fmt = """
An unexpected %(typename)s exception was raised:

%(value)s

Please contact %(contact)s for assistance and 
include the output of this command:

tau --log=DEBUG %(cmd)s"""
  
  def __init__(self, value, hint="Contact %s" % HELP_CONTACT):
    self.value = value
    self.hint = hint
    
  def __str__(self):
    return self.value
  
  def handle(self, etype, e, tb):
    message = self.message_fmt % {'value': self.value,
                                  'hint': 'Hint: %s' % self.hint,
                                  'typename': etype.__name__, 
                                  'cmd': ' '.join([arg for arg in sys.argv[1:]]), 
                                  'contact': HELP_CONTACT}
    traceback.print_exception(etype, e, tb)
    LOGGER.critical(message)
    sys.exit(EXIT_FAILURE)


class InternalError(Error):
  """
  Indicates that an internal error has occurred
  These are bad and really shouldn't happen
  """
  def __init__(self, value):
    super(InternalError, self).__init__(value)


class ConfigurationError(Error):
  """
  Indicates that Tau cannot succeed with the given parameters
  """
  
  message_fmt = """
%(value)s
%(hint)s

TAU cannot proceed with the given inputs. 
Please review the input files and command line parameters
or contact %(contact)s for assistance."""
  
  def __init__(self, value, hint="Try `tau --help`"):
    super(ConfigurationError, self).__init__(value, hint)



def excepthook(etype, e, tb):
  """
  Exception handler for any uncaught exception (except SystemExit).
  """
  if etype == KeyboardInterrupt:
    LOGGER.info('Received keyboard interrupt.  Exiting.')
    sys.exit(EXIT_WARNING)
  else:
    if LOG_LEVEL == 'DEBUG':
      traceback.print_exception(etype, e, tb)
    try:
      sys.exit(e.handle(etype, e, tb))
    except AttributeError, err:
      traceback.print_exception(etype, e, tb)
      LOGGER.critical("""
An unexpected %(typename)s exception was raised:

%(value)s

This is a bug in TAU.
Please contact %(contact)s for assistance and 
include the output of this command:

tau --log=DEBUG %(cmd)s""" % {'value': e,
                              'typename': etype.__name__, 
                              'cmd': ' '.join([arg for arg in sys.argv[1:]]), 
                              'contact': HELP_CONTACT})
      sys.exit(EXIT_FAILURE)

# Set the default exception handler
sys.excepthook = excepthook