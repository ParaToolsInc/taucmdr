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
"""Draw progress indicators on the console.

Show bars or spinners, possibly with instantaneous CPU load average.
"""

import os
import sys
import threading
import logging
import itertools
from contextlib import contextmanager
from datetime import datetime
from taucmdr import logger
from taucmdr.error import ConfigurationError


LOGGER = logger.get_logger(__name__)


def _read_proc_stat_cpu():
    with open('/proc/stat') as fin:
        cpu_line = fin.readline()
    values = (float(x) for x in cpu_line.split()[1:])
    fields = 'user', 'nice', 'sys', 'idle', 'iowait', 'irq', 'sirq'
    return dict(zip(fields, values))

def _proc_stat_cpu_load_average():
    if not hasattr(_proc_stat_cpu_load_average, 'prev'):
        _proc_stat_cpu_load_average.prev = _read_proc_stat_cpu()
    prev = _proc_stat_cpu_load_average.prev
    cur = _read_proc_stat_cpu()
    if prev and cur:
        prev_idle = prev['idle'] + prev['iowait']
        cur_idle = cur['idle'] + cur['iowait']
        prev_total = sum(prev.itervalues())
        cur_total = sum(cur.itervalues())
        diff_total = cur_total - prev_total
        diff_idle = cur_idle - prev_idle
        _proc_stat_cpu_load_average.prev = cur
        if diff_total:
            return (diff_total - diff_idle) / diff_total
    return 0.0

def load_average():
    """Calculate the CPU load average.

    Returns:
        float: Load average since last time this routine was called
               or 0.0 if couldn't calculate load average.
    """
    try:
        cpu_load_avg = _proc_stat_cpu_load_average()
    except IOError:
        cpu_load_avg = 0.0
    return cpu_load_avg


@contextmanager
def progress_spinner(show_cpu=True):
    """Show a progress spinner until the wrapped object returns."""
    flag = threading.Event()
    def show_progress():
        with ProgressIndicator(show_cpu=show_cpu) as spinner:
            while not flag.wait(0.25):
                spinner.update()
    thread = threading.Thread(target=show_progress)
    # Kill thread ungracefully when main thread exits, see
    # https://docs.python.org/2/library/threading.html#thread-objects
    thread.daemon = True
    thread.start()
    # Send control to wrapped object
    yield
    # Wrapped object has returned, stop the thread
    flag.set()
    thread.join()


class ProgressIndicator(object):
    """Display a progress bar or spinner on a stream."""
    
    _spinner = itertools.cycle(['-', '/', '|', '\\'])
    
    def __init__(self, total_size=0, block_size=1, show_cpu=True, mode=None):
        """ Initialize the ProgressBar object.

        Args:
            total_size (int): Total amount of work to be completed.
            block_size (int): Size of a work block.
            show_cpu (bool): If True, show CPU load average as well as progress.
            mode (str): One of 'full', 'minimal', 'disabled', or None.
                        If ``mode == None`` then the default value for ``mode`` is taken from  
                            the __TAUCMDR_PROGRESS_BARS__ environment variable. If that variable is not set 
                            then the default is 'full'.
                        If ``mode == 'full'`` then all output is written to :any:`sys.stdout`.
                        If ``mode == 'minimal'`` then a single '.' character is written to sys.stdout approximately
                            every five seconds without erasing the line (best for Travis regression test).
                        If ``mode == 'disabled'`` then no output is written to stdout.
        """
        if mode is None:
            mode = os.environ.get('__TAUCMDR_PROGRESS_BARS__', 'full').lower()
        if mode not in ('none', 'disabled', 'minimal', 'full'):
            raise ConfigurationError('Invalid value for __TAUCMDR_PROGRESS_BARS__ environment variable: %s' % mode)               
        self.count = 0
        self.total_size = total_size
        self.block_size = block_size
        self.show_cpu = show_cpu
        self.mode = mode
        self._last_time = datetime.now()
        self._start_time = None
        self._line_remaining = 0
        
    def __enter__(self):
        self.update(0)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.complete()
        return False
    
    def _line_reset(self):
        sys.stdout.write('\r')
        sys.stdout.write(logger.COLORED_LINE_MARKER)
        self._line_remaining = logger.LINE_WIDTH
        
    def _line_append(self, text):
        from taucmdr import util
        sys.stdout.write(text)
        self._line_remaining -= len(util.uncolor_text(text))
        
    def _line_flush(self):
        sys.stdout.flush()
        assert self._line_remaining >= 0
        
    def _draw_bar(self, percent, width, char, *args, **kwargs):
        from taucmdr import util          
        bar_on = max(int(percent*width), 1)
        bar_off = width - bar_on
        self._line_append(util.color_text(char*bar_on, *args, **kwargs))
        self._line_append(' '*bar_off)
        
    def _update_minimal(self):
        if self._start_time is None:
            self._start_time = datetime.now()
            sys.stdout.write(logger.COLORED_LINE_MARKER)
        tdelta = datetime.now() - self._last_time
        if tdelta.total_seconds() >= 5:
            self._last_time = datetime.now()
            sys.stdout.write('.')
            sys.stdout.flush()
            
    def _update_full(self, count, block_size, total_size):
        if count is not None:
            self.count = count
        if block_size is not None:
            self.block_size = block_size
        if total_size is not None:
            self.total_size = total_size
        if self._start_time is None:
            self._start_time = datetime.now()
        show_bar = self.total_size > 0
        tdelta = datetime.now() - self._start_time
        self._line_reset()
        self._line_append("%0.1f seconds " % tdelta.total_seconds())        
        if (not self.show_cpu and not show_bar) or (self._line_remaining < 40):
            self._line_append('[%s]' % self._spinner.next())
            self._line_flush()
        else:
            if self.show_cpu:
                cpu_load = min(load_average(), 1.0)
                self._line_append("[CPU: %0.1f " % (100*cpu_load))
                width = (self._line_remaining/4) if show_bar else (self._line_remaining-2)
                self._draw_bar(cpu_load, width, '|', 'white', 'on_white')
                self._line_append("]")
            if show_bar:
                if self.show_cpu:
                    self._line_append(" ")
                percent = max(min(float(self.count*self.block_size) / self.total_size, 1.0), 0.0)
                self._line_append("[%0.1f%% " % (100*percent))
                width = self._line_remaining - 3
                self._draw_bar(percent, width, '>', 'green', 'on_green')
                self._line_append("]")
            self._line_flush()

    def update(self, count=None, block_size=None, total_size=None):
        """Show progress.

        Updates `block_size` or `total_size` if given for compatibility with :any:`urllib.urlretrieve`.

        Args:
            count (int): Number of blocks of `block_size` that have been completed.
            block_size (int): Size of a work block.
            total_size (int): Total amount of work to be completed.
        """
        if self.mode == 'disabled' or getattr(logging, logger.LOG_LEVEL) >= logging.ERROR:
            return
        elif self.mode == 'minimal':
            self._update_minimal()
        elif self.mode == 'full':
            self._update_full(count, block_size, total_size)

    def complete(self):
        if self.mode != 'disabled':
            tdelta = datetime.now() - self._start_time
            elapsed = "Completed in %0.3f seconds" % tdelta.total_seconds()
            if self.mode == 'minimal':
                sys.stdout.write(' %s\n' % elapsed)
                sys.stdout.flush()
            elif self.mode == 'full':
                self._line_reset()
                self._line_append(elapsed)
                self._line_append(' '*self._line_remaining)
                self._line_flush()
            self._start_time = None
