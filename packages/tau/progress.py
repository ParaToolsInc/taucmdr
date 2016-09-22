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

import sys
import threading
import logging
import itertools
from termcolor import termcolor
from datetime import datetime
from contextlib import contextmanager
from tau import logger


LOGGER = logger.get_logger(__name__)


def _read_proc_stat_cpu():
    with open('/proc/stat') as fin:
        cpu_line = fin.readline()
    values = [float(x) for x in cpu_line.split()[1:]]
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
        cpu_load_avg = 0
    return cpu_load_avg


@contextmanager
def progress_spinner(show_cpu=True, stream=sys.stdout):
    """Show a progress spinner until the wrapped object returns."""
    flag = threading.Event()
    def show_progress():
        with ProgressIndicator(show_cpu=show_cpu, stream=stream) as spinner:
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

    def __init__(self, total_size=0, block_size=1, show_cpu=True, stream=sys.stdout):
        """ Initialize the ProgressBar object.

        Args:
            total_size (int): Total amount of work to be completed.
            block_size (int): Size of a work block.
            show_cpu (bool): If True, show CPU load average as well as progress.
            stream (file): Stream object to write progress indication to.
        """
        self._spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.count = 0
        self.total_size = total_size
        self.block_size = block_size
        self.show_cpu = show_cpu
        self.stream = stream
        self._start_time = None
        self._line_marker = logger.LINE_MARKER
        self._color_line_marker = termcolor.colored(logger.LINE_MARKER, 'red')

    def __enter__(self):
        self.update(0)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.complete()
        return False

    def update(self, count=None, block_size=None, total_size=None):
        """Show progress.

        Updates `block_size` or `total_size` if given for compatibility with :any:`urllib.urlretrieve`.

        Args:
            count (int): Number of blocks of `block_size` that have been completed.
            block_size (int): Size of a work block.
            total_size (int): Total amount of work to be completed.
        """
        if getattr(logging, logger.LOG_LEVEL) < logging.ERROR: 
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
            elapsed = "% 6.1f seconds " % tdelta.total_seconds()
            line_width = logger.LINE_WIDTH - len(self._line_marker) - len(elapsed) - 5
            if self.show_cpu:
                cpu_load = min(load_average(), 1.0)
                cpu_label = "CPU: {: 6.1%} ".format(cpu_load)
                cpu_width = 10 if show_bar else line_width - 5
                cpu_fill = '|'*min(max(int(cpu_load*cpu_width), 1), cpu_width)
                colored_cpu_fill = termcolor.colored(cpu_fill, 'white', 'on_white')
                hidden_chars = len(colored_cpu_fill) - len(cpu_fill)
                width = cpu_width + (hidden_chars if show_bar else 0)
                cpu_avg = "[{}{:<{width}}] ".format(cpu_label, colored_cpu_fill, width=width)
                line_width -= len(cpu_avg) - hidden_chars
            else:
                cpu_avg = ''
            if show_bar:
                percent = min(float(self.count*self.block_size) / self.total_size, 1.0)
                bar_width = line_width - 5
                bar_fill = '>'*min(max(int(percent*bar_width), 1), bar_width)
                colored_bar_fill = termcolor.colored(bar_fill, 'green')
                hidden_chars = len(colored_bar_fill) - len(bar_fill)
                width = bar_width + hidden_chars
                progress = "[{:-<{width}}] {: 6.1%}".format(colored_bar_fill, percent, width=width)
            else:
                progress = '[%s]' % self._spinner.next()
            self.stream.write('\r')
            self.stream.write(self._color_line_marker)
            self.stream.write(elapsed)
            self.stream.write(cpu_avg)
            self.stream.write(progress)
            self.stream.flush()

    def complete(self):
        tdelta = datetime.now() - self._start_time
        elapsed = "Completed in %s seconds" % tdelta.total_seconds()
        self.stream.write("\r{}{:{width}}\n".format(self._color_line_marker, elapsed, width=logger.LINE_WIDTH))
        self.stream.flush()

