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

# System modules
import os
import sys
import errno
import logging
import textwrap
import socket
import platform
from datetime import datetime
from logging import handlers
from tau import USER_PREFIX


def getTerminalSize():
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _getTerminalSize_windows()
        if tuple_xy is None:
            tuple_xy = _getTerminalSize_tput()
            # needed for window's python in cygwin's xterm!
    if current_os == 'Linux' or current_os == 'Darwin' or current_os.startswith('CYGWIN'):
        tuple_xy = _getTerminalSize_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy


def _getTerminalSize_windows():
    res = None
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10, stdout -11, stderr -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
    except:
        return None
    if res:
        import struct
        (_,_,_,_,_, left,top,right,bottom, _,_) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
        return sizex, sizey
    else:
        return None


def _getTerminalSize_tput():
    # get terminal width
    # src:
    # http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        import subprocess
        proc = subprocess.Popen(["tput", "cols"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        cols = int(output[0])
        proc = subprocess.Popen(["tput", "lines"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        output = proc.communicate(input=None)
        rows = int(output[0])
        return (cols, rows)
    except:
        return None


def _getTerminalSize_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            import struct
            cr = struct.unpack(
                'hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return None
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])


def _textwrap_message(record):
    return ['%s%s' % (LINE_MARKER, _text_wrapper.fill(line))
            for line in record.getMessage().split('\n')]


def _msgbox(record, marker):
    width = LINE_WIDTH - len(LINE_MARKER)
    hline = LINE_MARKER + marker * width
    parts = [hline, LINE_MARKER, '%s%s' % (LINE_MARKER, record.levelname)]
    parts.extend(_textwrap_message(record))
    parts.append(hline)
    return '\n'.join(parts)


class LogFormatter(logging.Formatter, object):

    """
    Custom log message formatter.
    """

    def __init__(self):
        super(LogFormatter, self).__init__()

    def format(self, record):
        if record.levelno == logging.CRITICAL:
            return _msgbox(record, '!')
        elif record.levelno == logging.ERROR:
            return _msgbox(record, '!')
        elif record.levelno == logging.WARNING:
            return _msgbox(record, '*')
        elif record.levelno == logging.INFO:
            return '\n'.join(_textwrap_message(record))
        elif record.levelno == logging.DEBUG:
            return '%s%s:%s: %s' % (LINE_MARKER, record.levelname,
                                    record.name, record.getMessage())
        else:
            raise RuntimeError(
                'Unknown record level (name: %s)' % record.levelname)


def getLogger(name):
    """
    Returns a customized logging object by name
    """
    return logging.getLogger('tau.' + name)


def setLogLevel(level):
    """
    Sets the output level for all logging objects
    """
    global LOG_LEVEL
    LOG_LEVEL = level.upper()
    stdout_handler.setLevel(LOG_LEVEL)

LOG_LEVEL = 'INFO'

LOG_FILE = os.path.join(USER_PREFIX, 'debug_log')

# Marker for each line of output
LINE_MARKER = os.environ.get('TAU_LINE_MARKER', '')

# Terminal dimensions
TERM_SIZE = getTerminalSize()
LINE_WIDTH = TERM_SIZE[0] - len(LINE_MARKER)

_text_wrapper = textwrap.TextWrapper(width=LINE_WIDTH,
                                     subsequent_indent=LINE_MARKER + '  ',
                                     break_long_words=False,
                                     break_on_hyphens=False,
                                     drop_whitespace=False)

_root_logger = logging.getLogger('tau')
if not len(_root_logger.handlers):
    prefix = os.path.dirname(LOG_FILE)
    try:
        os.makedirs(prefix)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(prefix):
            pass
        else:
            raise
    file_handler = handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when='D',
        interval=1,
        backupCount=5)
    file_handler.setFormatter(LogFormatter())
    file_handler.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(LogFormatter())
    stdout_handler.setLevel(LOG_LEVEL)

    _root_logger.addHandler(file_handler)
    _root_logger.addHandler(stdout_handler)
    _root_logger.setLevel(logging.DEBUG)

    _root_logger.debug("""
%(bar)s
TAU COMMANDER LOGGING INITIALIZED

Timestamp         : %(timestamp)s
Hostname          : %(hostname)s
Platform          : %(platform)s
Python Version    : %(pyversion)s
Working Directory : %(cwd)s
Terminal Size     : %(termsize)s
%(bar)s
""" % {'bar': '#' * LINE_WIDTH,
       'timestamp': str(datetime.now()),
       'hostname': socket.gethostname(),
       'platform': platform.platform(),
       'pyversion': platform.python_version(),
       'cwd': os.getcwd(),
       'termsize': 'x'.join(map(str, TERM_SIZE))})
