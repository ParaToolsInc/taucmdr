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


LOGGER = getLogger('error')


def _default_handle(etype, e, tb):
    traceback.print_exception(etype, e, tb)
    args = [arg for arg in sys.argv[1:] 
            if not ('--log' in arg or '--verbose' in arg)] 
    message = """
An unexpected %(typename)s exception was raised.
Please contact %(contact)s for assistance.
If possible, please include the output of this command:

tau --log=DEBUG %(cmd)s""" % {'typename': etype.__name__, 
                      'cmd': ' '.join(args), 
                      'contact': HELP_CONTACT}
    LOGGER.critical(message)
    sys.exit(EXIT_FAILURE)


class Error(Exception):
    """
    Base class for errors in Tau
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    def handle(self):
        _default_handle(*sys.exc_info())


class InternalError(Error):
    """
    Indicates that an internal error has occurred
    """
    def __init__(self, value, hint="Contact %s" % HELP_CONTACT):
        super(InternalError, self).__init__(value)
        self.hint = hint


class ConfigurationError(Error):
    """
    Indicates that Tau cannot succeed with the given parameters
    """
    def __init__(self, value, hint="Try 'tau --help'."):
        super(ConfigurationError, self).__init__(value)
        self.hint = hint

    def handle(self):
        hint = 'Hint: %s\n' % self.hint if self.hint else ''
        message = """
%(value)s
%(hint)s
TAU cannot proceed with the given inputs.
Please review the input files and command line parameters
or contact %(contact)s for assistance.""" % {'value': self.value, 
                                             'hint': hint, 
                                             'contact': HELP_CONTACT}
        LOGGER.error(message)
        sys.exit(EXIT_FAILURE)


class MissingFeatureError(Error):
    """
    Indicates that a promised feature has not been implemented yet
    """
    def __init__(self, value, missing, hint="Contact %s" % HELP_CONTACT):
        super(MissingFeatureError, self).__init__(value)
        self.missing = missing
        self.hint = hint
        
    def handle(self):
        hint = 'Hint: %s\n' % self.hint if self.hint else ''
        message = """
Unimplemented feature %(missing)r: %(value)s
%(hint)s
Sorry, you have requested a feature that is not yet implemented.
Please contact %(contact)s for assistance.""" % {'missing': self.missing, 
                                                 'value': self.value, 
                                                 'hint': hint, 
                                                 'contact': HELP_CONTACT}
        LOGGER.error(message)
        sys.exit(EXIT_FAILURE)



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
            sys.exit(e.handle())
        except AttributeError:
            _default_handle(etype, e, tb)

# Set the default exception handler
sys.excepthook = excepthook