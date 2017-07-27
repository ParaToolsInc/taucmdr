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
"""TAU trace data class.

Parses a OTF2 trace and generates a TauTrace class containing
trace data and other relavent information.
"""

import os
import sys
import collections
from taucmdr.error import InternalError
from taucmdr.cf.software.libotf2_installation import Libotf2Installation


class TauTrace(object):
    """Tau trace class."""
    
    def __init__(self, trial, trace_data):
        self.trial = trial
        self.trace_data = trace_data
        
    @classmethod
    def parse(cls, path, trial):
        otf2_installation = Libotf2Installation.minimal()
        sys.path.insert(0, os.path.join(otf2_installation.install_prefix, 'lib/python2.7/site-packages'))
        try:
            import otf2
            from otf2.events import Enter, Leave
        except ImportError:
            raise InternalError('Cannot import LibOTF2 python bindings.')
        else:
            trace_data = collections.defaultdict(list)
            with otf2.reader.open(path) as trace:
                for location, event in trace.events:
                    if isinstance(event, Enter) or isinstance(event, Leave):
                        trace_data[(location.name, event.region.name)].append(event.time)
            return cls(trial, trace_data)
        
