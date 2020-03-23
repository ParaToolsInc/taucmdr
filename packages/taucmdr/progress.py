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

from __future__ import absolute_import
import os
import sys
import threading
import logging
import itertools
from datetime import datetime, timedelta
from taucmdr import logger
from taucmdr.error import ConfigurationError
import six
from six.moves import range
from six.moves import zip


LOGGER = logger.get_logger(__name__)


def _read_proc_stat_cpu():
    with open('/proc/stat') as fin:
        cpu_line = fin.readline()
    values = (float(x) for x in cpu_line.split()[1:])
    fields = 'user', 'nice', 'sys', 'idle', 'iowait', 'irq', 'sirq'
    return dict(list(zip(fields, values)))

def _proc_stat_cpu_load_average():
    if not hasattr(_proc_stat_cpu_load_average, 'prev'):
        _proc_stat_cpu_load_average.prev = _read_proc_stat_cpu()
    prev = _proc_stat_cpu_load_average.prev
    cur = _read_proc_stat_cpu()
    if prev and cur:
        prev_idle = prev['idle'] + prev['iowait']
        cur_idle = cur['idle'] + cur['iowait']
        prev_total = sum(six.itervalues(prev))
        cur_total = sum(six.itervalues(cur))
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
               or None if couldn't calculate load average.
    """
    try:
        cpu_load_avg = _proc_stat_cpu_load_average()
    except IOError:
        cpu_load_avg = None
    return cpu_load_avg


class ProgressIndicator(object):
    """A fancy progress indicator to entertain antsy users."""

    _spinner = itertools.cycle(['-', '\\', '|', '/'])

    _indent = '    '

    def __init__(self, label, total_size=0, block_size=1, show_cpu=True, auto_refresh=0.25):
        mode = os.environ.get('__TAUCMDR_PROGRESS_BARS__', 'full').lower()
        if mode not in ('full', 'disabled'):
            raise ConfigurationError('Invalid value for __TAUCMDR_PROGRESS_BARS__ environment variable: %s' % mode)
        self.label = label
        self.count = 0
        self.total_size = total_size
        self.block_size = block_size
        self.show_cpu = show_cpu if load_average() is not None else False
        self.auto_refresh = auto_refresh if mode != 'disabled' else 0
        self._mode = mode
        self._line_remaining = 0
        self._phases = []
        self._phase_count = 0
        self._phase_depth = 0
        self._phase_base = 0
        self._thread = None
        self._exiting = None
        self._updating = None

    def _thread_progress(self):
        while not self._exiting.wait(self.auto_refresh):
            self._updating.acquire()
            self.update()
            self._updating.notify()
            self._updating.release()

    def __enter__(self):
        self.push_phase(self.label)
        return self

    def __exit__(self, unused_exc_type, unused_exc_value, unused_traceback):
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

    def _line_flush(self, newline=False):
        self._line_append(' '*self._line_remaining)
        if newline:
            sys.stdout.write('\n')
        sys.stdout.flush()
        assert self._line_remaining == 0, str(self._line_remaining)

    def _draw_bar(self, percent, width, char, *args, **kwargs):
        from taucmdr import util
        bar_on = max(int(percent*width), 1)
        bar_off = width - bar_on
        self._line_append(util.color_text(char*bar_on, *args, **kwargs))
        self._line_append(' '*bar_off)

    def _draw_phase_labels(self):
        start = self._phase_base
        printed_phases = self._phases[:start]
        for i, (label, timestamp, implicit) in enumerate(self._phases[start:-1], start):
            if label is not None:
                if self._phases[i+1][0] is not None:
                    self._line_reset()
                    self._line_append("%s:" % label)
                    self._line_flush(newline=True)
                printed_phases.append((label, timestamp, implicit))
            else:
                label, tstart, _ = printed_phases.pop()
                tdelta = (timestamp - tstart).total_seconds()
                self._line_reset()
                self._line_append("%s [%0.3f seconds]" % (label, tdelta))
                self._line_flush(newline=True)
        label, timestamp, implicit = self._phases[-1]
        if label is not None:
            printed_phases.append((label, timestamp, implicit))
        else:
            label, tstart, _ = printed_phases.pop()
            tdelta = (timestamp - tstart).total_seconds()
            self._line_reset()
            self._line_append("%s [%0.3f seconds]" % (label, tdelta))
            self._line_flush(newline=True)
        self._phases = printed_phases
        self._phase_depth = len(printed_phases)
        self._phase_base = max(self._phase_base, self._phase_depth-1)

    def push_phase(self, label, implicit=False):
        if self.auto_refresh:
            if self._thread is None:
                self._thread = threading.Thread(target=self._thread_progress)
                self._exiting = threading.Event()
                self._updating = threading.Condition()
                self._thread.daemon = True
                self._thread.start()
            self._updating.acquire()
        try:
            top_phase = self._phases[-1]
        except IndexError:
            new_phase = True
        else:
            new_phase = top_phase[0] is not None and top_phase[0].strip() != label
            if top_phase[2]:
                self.pop_phase()
        if new_phase:
            label = (self._phase_depth*self._indent) + label
            self._phases.append((label, datetime.now(), implicit))
        if self.auto_refresh:
            self._updating.wait()
            self._updating.release()
        else:
            self.update()

    def pop_phase(self):
        if self.auto_refresh:
            self._updating.acquire()
        if self._phases:
            self._phases.append((None, datetime.now(), None))
        if self.auto_refresh:
            self._updating.wait()
            self._updating.release()
        else:
            self.update()

    def phase(self, label):
        self.push_phase(label, True)

    def increment(self, count=1):
        self.count += count


    def update(self, count=None, block_size=None, total_size=None):
        """Show progress.

        Updates `block_size` or `total_size` if given for compatibility with :any:`urllib.urlretrieve`.

        Args:
            count (int): Number of blocks of `block_size` that have been completed.
            block_size (int): Size of a work block.
            total_size (int): Total amount of work to be completed.
        """
        if count is not None:
            self.count = count
        if block_size is not None:
            self.block_size = block_size
        if total_size is not None:
            self.total_size = total_size
        if self.auto_refresh:
            if threading.current_thread() is not self._thread:
                if not self._phases:
                    self.push_phase(self.label)
                return
        else:
            if not self._phases:
                self.push_phase(self.label)
                return
        if self._phase_depth != len(self._phases):
            self._draw_phase_labels()
        if not self._phases:
            return
        label, tstart, _ = self._phases[-1]
        tdelta = (datetime.now() - tstart).total_seconds()
        self._line_reset()
        if label =="":
            self._line_append("%0.1f seconds %s" % (tdelta, next(self._spinner)))
        else:
            self._line_append("%s: %0.1f seconds %s" % (label, tdelta, next(self._spinner)))
        show_bar = self.total_size > 0
        if self.show_cpu and self._line_remaining > 40:
            cpu_load = min(load_average(), 1.0)
            self._line_append("[CPU: %0.1f " % (100*cpu_load))
            width = (self._line_remaining / 4) if show_bar else (self._line_remaining-2)
            self._draw_bar(cpu_load, width, '|', 'white', 'on_white')
            self._line_append("]")
        if show_bar and self._line_remaining > 20:
            self._line_append(" ")
            completed = float(self.count*self.block_size)
            percent = max(min(completed / self.total_size, 1.0), 0.0)
            self._line_append("[%0.1f%% " % (100*percent))
            if completed == 0:
                eta = '(unknown)'
            else:
                time_remaining = (tdelta / completed) * (self.total_size - completed)
                eta = datetime.now() + timedelta(seconds=time_remaining)
                eta = '%s-%s-%s %02d:%02d' % (eta.year, eta.month, eta.day, eta.hour, eta.minute)
            width = self._line_remaining - 4 - len(eta)
            self._draw_bar(percent, width, '>', 'green', 'on_green')
            self._line_append("] %s" % eta)
        self._line_flush()


    def complete(self):
        active = len(self._phases)
        for _ in range(active):
            self.pop_phase()
        if self.auto_refresh:
            self._exiting.set()
            self._thread.join()
        else:
            self.update()
