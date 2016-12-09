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
"""Score-P software installation management.

Score-P is a tool suite for profiling, event tracing, and online analysis of HPC applications.
"""

import os
import hashlib
import subprocess
from tau import logger
from tau.cf.software import SoftwarePackageError
from tau.cf.software.installation import AutotoolsInstallation
from tau.cf.compiler import host, mpi, shmem
from tau.cf.target import X86_64_ARCH, IBM64_ARCH


LOGGER = logger.get_logger(__name__)

REPOS = {None: 'http://www.cs.uoregon.edu/research/tau/scorep.tgz'}

COMMANDS = {None:
            ['cube3to4',
             'cube4to3',
             'cube_calltree',
             'cube_canonize',
             'cube_clean',
             'cube_cmp',
             'cube_commoncalltree',
             'cube-config',
             'cube-config-backend',
             'cube-config-frontend',
             'cube_cut',
             'cube_derive',
             'cube_diff',
             'cube_dump',
             'cube_exclusify',
             'cube_inclusify',
             'cube_info',
             'cube_is_empty',
             'cube_mean',
             'cube_merge',
             'cube_nodeview',
             'cube_part',
             'cube_rank',
             'cube_regioninfo',
             'cube_remap2',
             'cube_sanity',
             'cube_score',
             'cube_stat',
             'cube_test',
             'cube_topoassist',
             'opari2',
             'opari2-config',
             'otf2-config',
             'otf2-estimator',
             'otf2-marker',
             'otf2-print',
             'otf2-snapshots',
             'otf2-template',
             'scorep',
             'scorep-backend-info',
             'scorep-config',
             'scorep-score',
             'scorep-wrapper',
             'tau2cube']}

HEADERS = {None: ['otf2/otf2.h']}


LIBRARIES = {None: ['libcube4.a']}


class ScorepInstallation(AutotoolsInstallation):
    """Downloads ScoreP."""
    # Settle down pylint.  Score-P is complex so we need a few extra arguments.
    # pylint: disable=too-many-arguments

    def __init__(self, sources, target_arch, target_os, compilers, 
                 use_mpi, use_shmem, use_binutils, use_libunwind, use_papi, use_pdt):
        super(ScorepInstallation, self).__init__('scorep', 'Score-P', sources, target_arch, target_os, 
                                                 compilers, REPOS, COMMANDS, LIBRARIES, HEADERS)
        self.use_mpi = use_mpi
        self.use_shmem = use_shmem
        for pkg, used in (('binutils', use_binutils), ('libunwind', use_libunwind), 
                          ('papi', use_papi), ('pdt', use_pdt)):
            if used:
                self.add_dependency(pkg, sources)

    def _calculate_uid(self):
        # Score-P installations have different symbols depending on what flags were used.
        uid = hashlib.md5()
        uid.update(self.src)
        uid.update(self.target_arch.name)
        uid.update(self.target_os.name)
        for compiler_uid in sorted(comp.uid for comp in self.compilers.itervalues()):
            uid.update(compiler_uid)
        uid.update(str(self._get_flags()))
        return uid.hexdigest()

    def _get_flags(self):
        flags = ['--enable-shared', '--without-otf2', '--without-opari2', '--without-cube', 
                 '--without-gui', '--disable-gcc-plugin', '--disable-dependency-tracking']
        if self.target_arch in (X86_64_ARCH, IBM64_ARCH):
            suites = {host.INTEL: 'intel', host.IBM: 'ibm', host.PGI: 'pgi', host.GNU: 'gcc'}
            suite = suites.get(self.compilers[host.CC].unwrap().info.family)
            flags.append('--with-nocross-compiler-suite' + ('='+suite if suite else ''))
        if self.use_mpi:
            suites = {mpi.INTEL: 'intel2'}
            suite = suites.get(self.compilers[mpi.MPI_CC].info.family)
            flags.append('--with-mpi' + ('='+suite if suite else ''))
        else:
            flags.append('--without-mpi')
        if self.use_shmem:
            suites = {shmem.OPENSHMEM: 'openshmem'}
            suite = suites.get(self.compilers[shmem.SHMEM_CC].info.family)
            flags.append('--with-shmem' + ('='+suite if suite else ''))
        else:
            flags.append('--without-shmem')
        binutils = self.dependencies.get('binutils')
        libunwind = self.dependencies.get('libunwind')
        papi = self.dependencies.get('papi')
        pdt = self.dependencies.get('pdt')
        if binutils:
            flags.append('--with-libbfd=%s' % binutils.install_prefix)
        if libunwind:
            flags.append('--with-libunwind=%s' % libunwind.install_prefix)
        if papi:       
            flags.append('--with-papi=%s' % papi.install_prefix)
            flags.append('--with-papi-header=%s' % papi.include_path)
            flags.append('--with-papi-lib=%s' % papi.lib_path)
        if pdt:
            flags.append('--with-pdt=%s' % pdt.bin_path)
        return flags

    def verify(self):
        super(ScorepInstallation, self).verify()
        # Use Score-P's `scorep-info` command to check if this Score-P installation
        # was configured with the flags we need.
        scorep_info = [os.path.join(self.bin_path, 'scorep-info'), 'config-summary']
        try:
            stdout = subprocess.check_output(scorep_info, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            raise SoftwarePackageError("%s failed with return code %d: %s", cmd, err.returncode, err.output)
        flags = self._get_flags()
        found_flags = set()
        extra_flags = set()
        in_section = False
        for line in stdout.splitlines():
            if line.startswith('Configure command:'):
                in_section = True
                continue
            elif in_section:
                line = line.replace('./configure', '')
                if not line.startswith(' '):
                    break
                for flag in flags:
                    if ("'%s'" % flag) in line:
                        found_flags.add(flag)
                        break
                else:
                    extra_flags.add(line.replace('\\', '').strip())
        # Some extra flags are harmless
        for flag in list(extra_flags):
            if flag.startswith("'--prefix="):
                extra_flags.remove(flag)
        if found_flags != set(flags):
            raise SoftwarePackageError("Score-P installation at '%s' was not configured with flags %s" % 
                                       (self.install_prefix, ' '.join(flags)))
        if extra_flags:
            raise SoftwarePackageError("Score-P installation at '%s' was configured with extra flags %s" % 
                                       (self.install_prefix, ' '.join(extra_flags)))

    def configure(self, flags, env):
        flags.extend(self._get_flags())
        # Score-P does strange things when PYTHON is set in the environment.
        # From vendor/otf2/configure --help:
        #   PYTHON      The python interpreter to use. Not a build requirement, only
        #               needed when developing. Python version 2.5 or above, but no
        #               support for python 3. Use PYTHON=: to disable python support.
        env['PYTHON'] = ':'
        return super(ScorepInstallation, self).configure(flags, env)

