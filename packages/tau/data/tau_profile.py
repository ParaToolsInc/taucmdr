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
"""TAU's default profile file format.

TODO: Docs
"""

import os
import re
from tau.data.error import DataFormatError


class TauProfile(object):
    """TODO: Docs"""

    def __init__(self, path):
        if not os.path.exists(path):
            raise DataFormatError(path, "File not found")
        self.path = path
        self.metric = None
        self.metadata = {}
        self.interval_events = {}
        self.aggregates = {}
        self.user_events = {}
        with open(self.path) as fp:
            self._parse_header(fp)
            self._parse_metadata(fp)
            self._parse_interval_events(fp)
            self._parse_aggregates(fp)
            self._parse_user_events(fp)

    def _parse_header(self, fp):
        """Parse a TAU profile file's header.

        The first line of a TAU profile is formatted as <COUNT><SPACE><METRIC> where <COUNT> is an integer count of
        the interval events in the profile, <SPACE> is whitespace, and <METRIC> is the name of the profiled metric
        prepended with the garbage string "templated_functions_MULTI_".

        Args:
            fp (file): An open profile file handle.

        Raises:
            DataFormatError: The profile file's header is invalid."
        """
        try:
            interval_count, metric = fp.readline().split()
            self.interval_count = int(interval_count)
            self.metric = metric.replace('templated_functions_MULTI_', '').strip()
        except ValueError:
            raise DataFormatError(self.path, "Invalid profile file header")

    def _parse_metadata(self, fp):
        """Parse a TAU profile file's metadata.

        Profile metadata appears on the second line of the file, which is formatted as <LABELS><SPACE><METADATA>.
        <LABELS> is the garbage string "# Name Calls Subrs Excl Incl ProfileCalls #". <SPACE> is whitespace.
        <METADATA> is structured data of the form <metadata>[<attribute><name>NAME</name><value>VALUE</value>
        </attribute>...]</metadata> where NAME and VALUE are the name and value of the metadata attribute.

        Args:
            fp (file): An open profile file handle.

        Raises:
            DataFormatError: The profile file's metadata is invalid."
        """
        metadata_start = "# Name Calls Subrs Excl Incl ProfileCalls #"
        line = fp.readline()
        if not line.startswith(metadata_start):
            raise DataFormatError(self.path, "Invalid metadata: line did not begin in the expected way")
        self.metadata = dict(re.findall('<attribute><name>(.+?)</name><value>(.*?)</value></attribute>', line))
        if not self.metadata:
            raise DataFormatError(self.path, "Invalid metadata line: can't parse metadata")

    def _parse_interval_events(self, fp):
        """Parse a TAU profile file's interval events.

        There is one interval event per line.  Each event line is formatted as:
        "<NAME>" <CALLS> <SUBCALLS> <EXCLUSIVE> <INCLUSIVE> <PROFILECALLS> GROUP="<GROUPS>"
        The units of <EXCLUSIVE> and <INCLUSIVE> depend on the metric.  Time is probably in microseconds.

        Args:
            fp (file): An open profile file handle.
        """
        pattern = re.compile('^"([^"]+)"\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+GROUP="([^"]+)"\s*$')
        for i in xrange(self.interval_count):
            match = pattern.match(fp.readline())
            name = match.group(1).strip()
            groups = match.group(7).split('|')
            self.interval_events[name] = {'calls': int(match.group(2)),
                                          'subcalls': int(match.group(3)),
                                          'exclusive': int(match.group(4)),
                                          'inclusive': int(match.group(5)),
                                          'profile_calls': int(match.group(6)),
                                          'groups': groups}

    def _parse_aggregates(self, fp):
        """Parse a TAU profile file's aggregate events.

        There are no aggregates, this function just consumes one line of the profile file.

        Args:
            fp (file): An open profile file handle.
        """
        # No aggregates at the moment
        fp.readline()

    def _parse_user_events(self, fp):
        """Parse a TAU profile file's atomic user events.

        There is one atomic user event per line.  Each event line is formatted as:
        "<NAME>" <COUNT> <MAX> <MIN> <MEAN> <SUMSQUARE>
        <NAME> is a string, <COUNT> is an integer, all others are real numbers.

        Args:
            fp (file): An open profile file handle.
        """
        user_event_count, title = fp.readline().split()
        self.user_event_count = int(user_event_count)
        if title != 'userevents':
            #error
            pass
        user_events_start = "# eventname numevents max min mean sumsqr"
        if fp.readline() != user_events_start:
            # error
            pass
        pattern = re.compile('^"([^"]+)"\s+(\d+)\s+(.+)\s+(.+)\s+(.+)\s+(.+)\s*$')
        for i in xrange(self.user_event_count):
            match = pattern.match(fp.readline())
            name = match.group(1).strip()
            self.user_events[name] = {'count': int(match.group(2)),
                                      'max': float(match.group(3)),
                                      'min': float(match.group(4)),
                                      'mean': float(match.group(5)),
                                      'sumsqr': float(match.group(6))}

