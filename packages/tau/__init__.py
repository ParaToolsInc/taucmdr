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

import os
import sys
import logging
import textwrap
import tau

# Exit codes
EXIT_FAILURE = -100
EXIT_WARNING = 100
EXIT_SUCCESS = 0

# Tau source code root directory
try:
    TAU_MASTER_SRC_DIR = os.environ['TAU_MASTER_SRC_DIR']
except KeyError:
    print '!'*80
    print '!'
    print '! CRITICAL ERROR: TAU_MASTER_SRC_DIR environment variable not set.'
    print '!'
    print '!'*80
    exit(EXIT_FAILURE)
    
# Check for custom line marker
try:
    TAU_LINE_MARKER = os.environ['TAU_LINE_MARKER']
except KeyError:
    TAU_LINE_MARKER = 'TAU: '

# Contact for bugs, etc.
HELP_CONTACT = '<support@paratools.com>'

# Logging level
LOG_LEVEL = 'INFO'

#Expected Python version
MINIMUM_PYTHON_VERSION = (2, 7)

# Path to this package
PACKAGE_HOME = os.path.dirname(os.path.realpath(__file__))

# Search paths for included files
INCLUDE_PATH = [os.path.realpath('.')]

# User-level TAU files
USER_PREFIX = os.path.join(os.path.expanduser('~'), '.tau')

# System-level TAU files
SYSTEM_PREFIX = os.path.realpath(os.path.join(TAU_MASTER_SRC_DIR, '..', 'installed'))

# TODO: Probably shouldn't be here...
DEFAULT_TAU_COMPILER_OPTIONS = ['-optRevert']


class LogFormatter(logging.Formatter, object):
    """
    Custom log message formatter.
    """
    
    LINE_WIDTH = 80
    LINE_MARKER = TAU_LINE_MARKER
    TEXT_WRAPPER = textwrap.TextWrapper(width=(LINE_WIDTH-len(LINE_MARKER)), 
                                        subsequent_indent=LINE_MARKER+'  ',
                                        break_long_words=False,
                                        break_on_hyphens=False,
                                        drop_whitespace=False)
    def __init__(self):
        super(LogFormatter, self).__init__()
        
    def _textwrap_message(self, record):
        return ['%s%s' % (self.LINE_MARKER, self.TEXT_WRAPPER.fill(line))
                for line in record.getMessage().split('\n')]
        
    def debug_msg(self, record):
        return '%s%s:%s: %s' % (self.LINE_MARKER, record.levelname, 
                                 record.module, record.getMessage()) 

    def info_msg(self, record):
        return '\n'.join(self._textwrap_message(record))       
    
    def msgbox(self, record, marker):
        line_marker = self.LINE_MARKER
        line_width = self.LINE_WIDTH - len(line_marker)
        hline = line_marker + marker*line_width
        parts = [hline, line_marker, '%s%s' % (line_marker, record.levelname)]
        parts.extend(self._textwrap_message(record))
        parts.append(hline)
        return '\n'.join(parts)

    def format(self, record):
        if record.levelno == logging.CRITICAL:
            return self.msgbox(record, '!')
        elif record.levelno == logging.ERROR:
            return self.msgbox(record, '!')
        elif record.levelno == logging.WARNING:
            return self.msgbox(record, '*')
        elif record.levelno == logging.INFO:
            return self.info_msg(record)
        elif record.levelno == logging.DEBUG:
            return self.debug_msg(record)
        else:
            raise tau.error.InternalError(record.levelno, 'Unknown record level (name: %s)' % record.levelname)

_loggers = set()
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(LogFormatter())

def getLogger(name):
    """
    Returns a customized logging object by name
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(_handler)
    logger.propagate = False
    _loggers.add(logger)
    return logger

def setLogLevel(level):
    """
    Sets the output level for all logging objects
    """
    global LOG_LEVEL
    LOG_LEVEL = level.upper()
    _handler.setLevel(LOG_LEVEL)
    for logger in _loggers:
        logger.setLevel(LOG_LEVEL)
