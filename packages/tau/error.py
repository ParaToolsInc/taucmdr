# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""TAU Commander error handling.

Only error base classes should be defined here.  
Error classes should be defined in their appropriate modules.
"""

import os
import sys
import traceback
from tau import HELP_CONTACT, EXIT_FAILURE, EXIT_WARNING, TAU_SCRIPT
from tau import logger


LOGGER = logger.get_logger(__name__)


class Error(Exception):
    """Base class for all errors in TAU Commander.
    
    Attributes:
        value: Some value attached to the error, typically a string but could be anything with a __str__ method.
        hints (list): String hints for the user to help resolve the error.
        show_backtrace (bool): Set to True to include a backtrace in the error message.
        message_fmt (str): Format string for the error message.
        message_fields (dict): String formatting fields to apply to message_fmt.
    """
    show_backtrace = False

    message_fmt = ("An unexpected %(typename)s exception was raised:\n"
                   "\n"
                   "%(value)s\n"
                   "\n"
                   "%(backtrace)s\n"
                   "\n"
                   "This is a bug in TAU Commander.\n"
                   "Please send '%(logfile)s' to %(contact)s for assistance.")
    
    def __init__(self, value, *hints):
        """Initialize the Error instance.
        
        Args:
            value (str): Message describing the error.
            *hints: Hint messages to help the user resolve this error.
        """
        super(Error, self).__init__()
        self.value = value
        self.hints = list(hints)
            
    @property
    def message_fields(self):
        fields = {'value': self.value, 'contact': HELP_CONTACT, 'logfile': logger.LOG_FILE}
        if not self.hints:
            hints_str = ''
        elif len(self.hints) == 1:
            hints_str = 'Hint: %s\n\n' % self.hints[0]
        else:
            hints_str = 'Hints:\n  * %s\n\n' % ('\n  * '.join(self.hints))
        fields['hints'] = hints_str
        return fields

    def __str__(self):
        return self.message_fmt % self.message_fields

    def handle(self, etype, value, tb):
        if self.show_backtrace:
            backtrace = ''.join(traceback.format_exception(etype, value, tb))
        else:
            backtrace = ''
        self.message_fields['typename'] = etype.__name__
        self.message_fields['backtrace'] = backtrace
        message = self.message_fmt % self.message_fields
        LOGGER.critical(message)
        sys.exit(EXIT_FAILURE)


class InternalError(Error):
    """Indicates that an internal error has occurred, i.e. a bug in TAU.
    
    These are bad and really shouldn't happen.
    """
    show_backtrace = True


class ConfigurationError(Error):
    """Indicates that TAU Commander cannot succeed with the given parameters.
    
    This is most commonly caused by user error, e.g the user specifies measurement
    settings that are incompatible with the application.
    """

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s"
                   "TAU cannot proceed with the given inputs.\n" 
                   "Please check the selected configuration for errors or contact %(contact)s for assistance.")

    def __init__(self, value, *hints):
        if not hints:
            hints = ["Try `%s --help`" % os.path.basename(TAU_SCRIPT)]
        super(ConfigurationError, self).__init__(value, *hints)


def excepthook(etype, value, tb):
    """Exception handler for any uncaught exception (except SystemExit).
    
    Replaces :any:`sys.excepthook`.
    
    Args:
        etype: Exception class.
        value: Exception instance.
        tb: Traceback object.
    """
    if etype == KeyboardInterrupt:
        LOGGER.info('Received keyboard interrupt.  Exiting.')
        sys.exit(EXIT_WARNING)
    else:
        try:
            sys.exit(value.handle(etype, value, tb))
        except AttributeError:
            message = Error.message_fmt % {'value': value,
                                           'typename': etype.__name__,
                                           'contact': HELP_CONTACT,
                                           'logfile': logger.LOG_FILE,
                                           'backtrace': ''.join(traceback.format_exception(etype, value, tb))}
            LOGGER.critical(message)
            sys.exit(EXIT_FAILURE)

sys.excepthook = excepthook
