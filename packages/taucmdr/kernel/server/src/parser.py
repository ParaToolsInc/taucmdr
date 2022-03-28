#
# Copyright (c) 2022, ParaTools, Inc.
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
#!/usr/bin/env python3
"""TAU trial data for TAU Profile.x.y.z format profiles

Parses a set of TAU profile files and yields multi-indexed Pandas dataframes for the
interval and atomic events.
"""
from __future__ import print_function
import glob
import mmap
import os
import re
from xml.etree import ElementTree
from sys import stderr

import sys
import pandas


class TauProfileParser():
    """Parser for TAU's profile.* format."""

    _interval_header_re = re.compile(b'(\\d+) templated_functions_MULTI_(.+)')

    _atomic_header_re = re.compile(b'(\\d+) userevents')

    def __init__(self, trial, metric, metadata, indices, interval_data, atomic_events):
        self.trial = trial
        self.metric = metric
        self.metadata = metadata
        self.indices = indices
        self._interval_data = interval_data
        self._atomic_data = atomic_events

    def interval_data(self):
        return self._interval_data

    def atomic_data(self):
        return self._atomic_data

    def get_value_types(self):
        return [key for key in dict(self._interval_data.dtypes)
                if dict(self._interval_data.dtypes)[key] in ['float64', 'int64']]

    def summarize_samples(self, across_threads=False, callpaths=True):
        groups = 'Timer Name' if across_threads else ['Node', 'Context', 'Thread', 'Timer Name']
        if callpaths:
            base_data = self._interval_data.loc[self._interval_data['Group'].str.contains("TAU_SAMPLE")]
        else:
            base_data = self._interval_data.loc[self._interval_data['Timer Type'] == 'SAMPLE']
        summary = base_data.groupby(groups).sum()
        summary.index = summary.index.map(
            lambda x: '[SUMMARY] ' + x if across_threads else (x[0], x[1], x[2], '[SUMMARY] ' + x[3]))
        return summary

    def summarize_allocations(self):
        sums = self.atomic_data().groupby('Timer').agg({'Count': 'sum', 'Mean': 'mean'})
        allocs = sums[sums.index.to_series().str.contains('alloc')][['Count', 'Mean']]
        allocs['Total'] = allocs['Count'] * allocs['Mean']
        return allocs


    @classmethod
    def _parse_header(cls, fin):
        match = cls._interval_header_re.match(fin.readline())
        interval_count, metric = match.groups()
        return int(interval_count), metric

    @classmethod
    def _parse_metadata(cls, fin):
        fields, xml_wanabe = fin.readline().split(b'<metadata>')
        xml_wanabe = b'<metadata>' + xml_wanabe
        if (fields != b"# Name Calls Subrs Excl Incl ProfileCalls" and
                    fields != b'# Name Calls Subrs Excl Incl ProfileCalls # '):
            raise RuntimeError('Invalid profile file: %s' % fin.name)
        try:
            metadata_tree = ElementTree.fromstring(xml_wanabe)
        except ElementTree.ParseError as err:
            raise RuntimeError('Invalid profile file: %s' % err) from err
        metadata = {}
        for attribute in metadata_tree.iter('attribute'):
            name = attribute.find('name').text
            value = attribute.find('value').text
            metadata[name] = value
        return metadata

    @classmethod
    def _parse_interval_data(cls, fin, count):
        pass

    @classmethod
    def _parse_atomic_header(cls, fin):
        aggregates = fin.readline().split(b' aggregates')[0]
        if aggregates != b'0':
            print("aggregates != 0, is '%s'" % aggregates, file=stderr)
        match = cls._atomic_header_re.match(fin.readline())
        try:
            count = int(match.group(1))
            if fin.readline() != b"# eventname numevents max min mean sumsqr\n":
                raise RuntimeError('Invalid profile file: %s' % fin.name)
        except AttributeError:
            count = 0
        return count

    @staticmethod
    def extract_from_timer_name(name):
        tag_search = re.search(r'^\[(\w+)\]\s+(.*)', name)
        timer_type, rest = tag_search.groups() if tag_search else (None, name)
        name_search = re.search(r'(.+)\[({.*)\]', rest)
        func_name, location = name_search.groups() if name_search else (rest, None)
        return func_name, location, timer_type

    @classmethod
    def parse(cls, dir_path, filenames=None, trial=None, multi=False):
        """ This method is used to parse both profile and multis"""
        # default behavior is to run the profile* files first,
        # if multi=true then it will look for MULTI__ folders
        if multi:
            return cls.multi_parse(dir_path,filenames,trial)

        if not os.path.isdir(dir_path):
            print("Error: %s is not a directory." % dir_path, file=stderr)
            sys.exit(1)

        if filenames is None:
            filenames = [os.path.basename(x) for x in glob.glob(os.path.join(dir_path, 'profile.*'))]
        if not filenames:
            multi_dir = list(glob.glob(dir_path+'/MULTI*'))

        if filenames:
            return cls.profile_parse(dir_path, filenames, trial)

        if multi_dir:
            return cls.multi_parse(dir_path, filenames, trial)

        print("Error: No Profile or MULTI__ to parse.")
        sys.exit(1)


    @classmethod
    def profile_parse(cls, dir_path, filenames=None, trial=None):
        """This method is used for parsing profiles"""
        intervals = []
        atomics = []
        indices = []
        trial_data_metric = None
        trial_data_metadata = None
        if filenames is None or filenames==[]:
            filenames = [os.path.basename(x) for x in glob.glob(os.path.join(dir_path, 'profile.*'))]
        if not filenames:
            print("Error: No profile files found.")
            sys.exit(1)
        for filename in sorted(filenames,
                               key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]):
            location = os.path.basename(filename).replace('profile.', '')
            node, context, thread = (int(x) for x in location.split('.'))
            file_path = os.path.join(dir_path, filename)
            with open(file_path, 'r+b') as fin:
                mem_map = mmap.mmap(fin.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)
                interval_count, metric = cls._parse_header(mem_map)
                if not trial_data_metric:
                    trial_data_metric = metric
                metadata = cls._parse_metadata(mem_map)
                if not trial_data_metadata:
                    trial_data_metadata = metadata
                interval = pandas.read_csv(mem_map, nrows=interval_count, delim_whitespace=True,
                                             names=['Calls', 'Subcalls', 'Exclusive',
                                                    'Inclusive', 'ProfileCalls', 'Group'],
                                             engine='c')
                split_index = interval.reset_index()['index'].apply(cls.extract_from_timer_name)
                for idx, col in enumerate(['Timer Name', 'Timer Location', 'Timer Type']):
                    interval[col] = split_index.apply(lambda l: l[idx]).values # # pylint: disable=unsupported-assignment-operation
                mem_map.seek(0)
                for _ in range(0, interval_count + 2):
                    mem_map.readline()
                cls._parse_atomic_header(mem_map)
                atomic = pandas.read_csv(mem_map, names=['Count', 'Maximum', 'Minimum', 'Mean', 'SumSq'],
                                           delim_whitespace=True, engine='c')
                mem_map.close()
                intervals.append(interval)
                atomics.append(atomic)
                indices.append((node, context, thread))

        interval_df = pandas.concat(intervals, keys=indices)
        interval_df.index.rename(['Node', 'Context', 'Thread', 'Timer'], inplace=True)
        atomic_df = pandas.concat(atomics, keys=indices)
        atomic_df.index.rename(['Node', 'Context', 'Thread', 'Timer'], inplace=True)
        return cls(trial, trial_data_metric, trial_data_metadata, indices, interval_df, atomic_df)


    @classmethod
    def multi_parse(cls, path_to_multis,filenames=None, trial=None):
        """ This method is used for multi parsing """
        multi_dir = list(glob.glob(path_to_multis+'/MULTI*'))
        tau_objs = [cls.profile_parse(folder,filenames,trial) for folder in multi_dir]
        combined_metric = b', '.join([tau_obj.metric for tau_obj in tau_objs])
        combined_metadata = tau_objs[0].metadata
        if 'Metric Name' in combined_metadata:
            combined_metadata['Metric Name'] = ', '.join([
                tau_obj.metadata['Metric Name'] for tau_obj in tau_objs])
        else:
            combined_metadata['Metric Name'] = combined_metric.decode("utf-8")

        combined_indices = tau_objs[0].indices
        combined_atomic_df = tau_objs[0].atomic_data()

        combined_intervals = pandas.concat(
            {"": tau_objs[0].interval_data().drop(['Exclusive', 'Inclusive'], axis=1)},
            axis=1, names=['Metric','Intervals']).swaplevel('Metric','Intervals',axis=1)

        exclusive_df = pandas.concat({'Exclusive': pandas.concat([
            tau_obj.interval_data()['Exclusive'].to_frame().rename(
                columns={'Exclusive':combined_metadata['Metric Name'].split(', ')[tau_objs.index(tau_obj)]}
                ) for tau_obj in tau_objs], axis=1)}, axis=1, names=['Intervals', 'Metric'])

        inclusive_df = pandas.concat({'Inclusive': pandas.concat([
            tau_obj.interval_data()['Inclusive'].to_frame().rename(
                columns={'Inclusive':combined_metadata['Metric Name'].split(', ')[tau_objs.index(tau_obj)]}
            ) for tau_obj in tau_objs], axis=1)}, axis=1, names=['Intervals', 'Metric'])

        combined_intervals = pandas.concat([combined_intervals,exclusive_df,inclusive_df], axis=1)

        return cls(trial, combined_metric, combined_metadata, combined_indices, combined_intervals, combined_atomic_df)
