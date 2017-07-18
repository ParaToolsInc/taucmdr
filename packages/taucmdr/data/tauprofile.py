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

import os
import re
import xml.etree.ElementTree as ElementTree
import pandas
from taucmdr import logger
from taucmdr.error import InternalError


LOGGER = logger.get_logger(__name__)


class TauProfile(object):
    
    _interval_header_re = re.compile(r'(\d+) templated_functions_MULTI_(.+)')
    
    _interval_re = re.compile(r'"(.*)" (\d+) (\d+) ((?:\d+)(?:\.\d+)?(?:E\d+)?) ((?:\d+)(?:\.\d+)?(?:E\d+)?) (\d+) GROUP="(.*)"')
    
    _atomic_header_re = re.compile(r'(\d+) userevents')
    
    _atomic_re = re.compile(r'"(.*)" ((?:\d+)(?:\.\d+)?(?:E\d+)?) ((?:\d+)(?:\.\d+)?(?:E\d+)?) ((?:\d+)(?:\.\d+)?(?:E\d+)?) ((?:\d+)(?:\.\d+)?(?:E\d+)?) ((?:\d+)(?:\.\d+)?(?:E\d+)?)')
    
    def __init__(self, trial, node, context, thread, metric, metadata, interval_events, atomic_events):
        self.trial = trial
        self.node = node
        self.context = context
        self.thread = thread
        self.metric = metric
        self.metadata = metadata
        self.interval_events = interval_events
        self.atomic_events = atomic_events
        
    def interval_data(self):
        df = pandas.DataFrame.from_dict({(self.trial, self.node, self.context, self.thread, region): self.interval_events[region] for region in self.interval_events.keys()}, orient='index')
        return df
    
    def atomic_data(self):
        index = ["Count", "Maximum", "Minimum", "Mean", "SumSq"]
        df = pandas.DataFrame.from_dict(self.atomic_events, orient='index')
        df.columns = index
        return df
        
    @classmethod
    def _parse_header(cls, fin):
        match = cls._interval_header_re.match(fin.readline())
        interval_count, metric = match.groups()
        return int(interval_count), metric
    
    @classmethod
    def _parse_metadata(cls, fin):
        fields, xml_wanabe = fin.readline().split('<metadata>')
        xml_wanabe = '<metadata>'+xml_wanabe
        if fields != "# Name Calls Subrs Excl Incl ProfileCalls" and fields != '# Name Calls Subrs Excl Incl ProfileCalls # ':
            raise InternalError('Invalid profile file: %s' % fin.name)
        try:
            metadata_tree = ElementTree.fromstring(xml_wanabe)
        except ElementTree.ParseError as err:
            raise InternalError('Invalid profile file: %s' % err)
        metadata = {}
        for attribute in metadata_tree.iter('attribute'):
            name = attribute.find('name').text
            value = attribute.find('value').text
            metadata[name] = value
        return metadata
    
    @classmethod
    def _parse_interval_data(cls, fin, count):
        interval_data = {}
        i = 0
        while i < count:
            line = fin.readline()
            match = cls._interval_re.match(line)
            values = {}
            values['Call'] = int(match.group(2))
            values['Subcalls'] = int(match.group(3))
            values['Exclusive'] = float(match.group(4))
            values['Inclusive'] = float(match.group(5))
            values['ProfileCalls'] = int(match.group(6))
            values['Group'] = match.group(7)
            interval_data[match.group(1)] = values 
            i += 1
        return interval_data
            
    @classmethod
    def _parse_atomic_data(cls, fin):
        aggregates = fin.readline().split(' aggregates')[0]
        if aggregates != '0':
            LOGGER.warning("aggregates != 0")
        match = cls._atomic_header_re.match(fin.readline())
        try:
            count = int(match.group(1))
            if fin.readline() != "# eventname numevents max min mean sumsqr\n":
                raise InternalError('Invalid profile file: %s' % fin.name)
        except AttributeError:
            count = 0
        atomic_data = {}
        i = 0
        while i < count:
            line = fin.readline()
            match = cls._atomic_re.match(line)
            values = [float(x) for x in match.group(2, 3, 4, 5, 6)]
            atomic_data[match.group(1)] = values
            i += 1
        return atomic_data

    @classmethod
    def parse(cls, path, trial):
        location = os.path.basename(path).replace('profile.', '')
        node, context, thread = (int(x) for x in location.split('.'))
        with open(path) as fin:
            interval_count, metric = cls._parse_header(fin)
            metadata = cls._parse_metadata(fin)
            interval_data = cls._parse_interval_data(fin, interval_count)
            atomic_data = cls._parse_atomic_data(fin)
            return cls(trial, node, context, thread, metric, metadata, interval_data, atomic_data)
        
        
