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
"""PAPI software installation management.

PAPI is used to measure hardware performance counters.
"""

from __future__ import absolute_import
import os
import re
import sys
import fileinput
from six.moves.html_parser import HTMLParser
from subprocess import CalledProcessError
from xml.etree import ElementTree
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.software import SoftwarePackageError
from taucmdr.cf.software.installation import AutotoolsInstallation
from taucmdr.cf.compiler.host import CC, CXX, IBM, GNU

LOGGER = logger.get_logger(__name__)

REPOS = {None: ['http://icl.utk.edu/projects/papi/downloads/papi-5.5.1.tar.gz',
         'http://fs.paratools.com/tau-mirror/papi-5.5.1.tar.gz']}

LIBRARIES = {None: ['libpapi.a']}


class PapiInstallation(AutotoolsInstallation):
    """Encapsulates a PAPI installation."""

    def __init__(self, sources, target_arch, target_os, compilers):
        # PAPI can't be built with IBM compilers so substitute GNU compilers instead
        if compilers[CC].unwrap().info.family is IBM:
            try:
                gnu_compilers = GNU.installation()
            except ConfigurationError:
                raise SoftwarePackageError("GNU compilers (required to build PAPI) could not be found.")
            compilers = compilers.modify(Host_CC=gnu_compilers[CC], Host_CXX=gnu_compilers[CXX])
        super(PapiInstallation, self).__init__('papi', 'PAPI', sources, target_arch, target_os,
                                               compilers, REPOS, None, LIBRARIES, None)
        self._xml_event_info = None

    def _prepare_src(self, *args, **kwargs):
        # PAPI's source lives in a 'src' directory instead of the usual top level location
        src_prefix = super(PapiInstallation, self)._prepare_src(*args, **kwargs)
        if os.path.basename(src_prefix) != 'src':
            src_prefix = os.path.join(src_prefix, 'src')
        return src_prefix

    def configure(self, flags):
        cc = self.compilers[CC].unwrap().absolute_path
        cxx = self.compilers[CXX].unwrap().absolute_path
        os.environ['CC'] = cc
        os.environ['CXX'] = cxx
        flags.extend(['CC='+cc, 'CXX='+cxx])
        return super(PapiInstallation, self).configure(flags)

    def make(self, flags):
        # PAPI's tests often fail to compile, so disable them.
        for line in fileinput.input(os.path.join(str(self._src_prefix), 'Makefile'), inplace=True):
            # fileinput.input with inplace=1 redirects stdout to the input file ... freaky
            sys.stdout.write(line.replace('TESTS =', '#TESTS ='))
        super(PapiInstallation, self).make(flags)

    def xml_event_info(self):
        if not self._xml_event_info:
            self.install()
            xml_event_info = util.get_command_output(os.path.join(self.bin_path, 'papi_xml_event_info'))
            self._xml_event_info = ElementTree.fromstring(xml_event_info)
        return self._xml_event_info

    def parse_metrics(self, metrics):
        """Extracts PAPI metrics from a list of metrics and strips TAU's metric prefixes."""
        return [re.sub('PAPI_NATIVE[:_]', '', metric) for metric in metrics if metric.startswith("PAPI")]

    def check_metrics(self, metrics):
        """Checks compatibility of PAPI metrics.

        Extracts all PAPI metrics from `metrics` and executes papi_event_chooser to check compatibility.

        Args:
            metrics (list): List of metrics.

        Raises:
            ConfigurationError: PAPI metrics are not compatible on the current host.
        """
        papi_metrics = self.parse_metrics(metrics)
        if not papi_metrics:
            return
        self.install()
        event_chooser_cmd = os.path.join(self.bin_path, 'papi_event_chooser')
        cmd = [event_chooser_cmd, 'PRESET'] + papi_metrics
        try:
            util.get_command_output(cmd)
        except CalledProcessError as err:
            for line in err.output.split('\n'):
                if "can't be counted with others" in line:
                    parts = line.split()
                    try:
                        event = parts[1]
                        code = int(parts[-1])
                    except (IndexError, ValueError):
                        continue
                    if code == -1:
                        why = ": %s is not compatible with other events" % event
                    elif code == -8:
                        why = ": %s cannot be counted due to resource limitations" % event
                    else:
                        why = ": %s is not supported on this host" % event
                    break
                elif "can't be found" in line:
                    parts = line.split()
                    try:
                        event = parts[1]
                    except IndexError:
                        continue
                    why = ": event %s is not available on the current host" % event
                    break
            else:
                why = ', and output from papi_event_chooser was not parsable.'
            raise ConfigurationError(("PAPI metrics [%s] are not compatible on the current host%s.") %
                                     (', '.join(papi_metrics), why),
                                     "Use papi_avail to check metric availability.",
                                     "Spread the desired metrics over multiple measurements.",
                                     "Choose fewer metrics.",
                                     "You may ignore this if you are cross-compiling.")

    def papi_metrics(self, event_type="PRESET", include_modifiers=False):
        """List PAPI available metrics.

        Returns a list of (name, description) tuples corresponding to the
        requested PAPI event type and possibly the event modifiers.

        Args:
            event_type (str): Either "PRESET" or "NATIVE".
            include_modifiers (bool): If True include event modifiers,
                                      e.g. BR_INST_EXEC:NONTAKEN_COND as well as BR_INST_EXEC.

        Returns:
            list: List of event name/description tuples.
        """
        assert event_type == "PRESET" or event_type == "NATIVE"
        metrics = []
        html_parser = HTMLParser()
        def _format(item):
            name = item.attrib['name']
            desc = html_parser.unescape(item.attrib['desc'])
            desc = desc[0].capitalize() + desc[1:] + "."
            return name, desc
        xml_event_info = self.xml_event_info()
        for eventset in xml_event_info.iter('eventset'):
            if eventset.attrib['type'] == event_type:
                for event in eventset.iter('event'):
                    if include_modifiers:
                        for modifier in event.iter('modifier'):
                            metrics.append(_format(modifier))
                    metrics.append(_format(event))
        return metrics
