#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

import sys
import traceback
from tau import HELP_CONTACT, EXIT_FAILURE, EXIT_WARNING
from tau import logger


LOGGER = logger.getLogger(__name__)


class Error(Exception):

    """
    Base class for errors in Tau
    """

    show_backtrace = False

    message_fmt = """
An unexpected %(typename)s exception was raised:

%(value)s

%(backtrace)s

Please e-mail '%(logfile)s' to %(contact)s for assistance.
"""
    
    def __init__(self, value, hint="Contact %s" % HELP_CONTACT):
        self.value = value
        self.hint = hint
        self.message_fields = {'value': self.value,
                               'hint': 'Hint: %s' % self.hint,
                               'cmd': ' '.join([arg for arg in sys.argv[1:]]),
                               'contact': HELP_CONTACT,
                               'logfile': logger.LOG_FILE}

    def __str__(self):
        return self.value

    def handle(self, etype, e, tb):
        if self.show_backtrace:
            backtrace = ''.join(traceback.format_exception(etype, e, tb))
        else:
            backtrace = ''
        self.message_fields['typename'] = etype.__name__
        self.message_fields['backtrace'] = backtrace
        message = self.message_fmt % self.message_fields
        LOGGER.critical(message)
        sys.exit(EXIT_FAILURE)


class InternalError(Error):

    """
    Indicates that an internal error has occurred
    These are bad and really shouldn't happen
    """
    show_backtrace = True

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
Please check the selected configuration for errors or contact %(contact)s for assistance.
"""

    def __init__(self, value, hint="Try `tau --help`"):
        super(ConfigurationError, self).__init__(value, hint)


class SoftwarePackageError(Error):

    """
    Indicates there was an error in an external software package  
    """

    message_fmt = """
%(value)s
%(hint)s

Please check the selected configuration for errors or email '%(logfile)s' to  %(contact)s for assistance.
"""

    def __init__(self, value, hint="Try `tau --help`"):
        super(SoftwarePackageError, self).__init__(value, hint)


def excepthook(etype, e, tb):
    """
    Exception handler for any uncaught exception (except SystemExit).
    """
    if etype == KeyboardInterrupt:
        LOGGER.info('Received keyboard interrupt.  Exiting.')
        sys.exit(EXIT_WARNING)
    else:
        try:
            sys.exit(e.handle(etype, e, tb))
        except AttributeError:
            LOGGER.critical("""
An unexpected %(typename)s exception was raised:

%(value)s

%(backtrace)s

This is a bug in TAU.
Please email '%(logfile)s' to %(contact)s for assistance
""" % {'value': e,
                'typename': etype.__name__,
                'cmd': ' '.join([arg for arg in sys.argv[1:]]),
                'contact': HELP_CONTACT,
                'logfile': logger.LOG_FILE,
                'backtrace': ''.join(traceback.format_exception(etype, e, tb))})
            sys.exit(EXIT_FAILURE)

# Set the default exception handler
sys.excepthook = excepthook
