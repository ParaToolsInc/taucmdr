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
"""Supported computing platforms.

I'd rather call this module "taucmdr.cf.platform" but that would conflict with :any:`platform`.
"""

import os
from taucmdr import logger, util
from taucmdr.error import ConfigurationError
from taucmdr.cf.objects import KeyedRecord
from taucmdr.cf.compiler import host, mpi, shmem
from taucmdr.cf.compiler.host import HOST_COMPILERS
from taucmdr.cf.compiler.mpi import MPI_COMPILERS
from taucmdr.cf.compiler.shmem import SHMEM_COMPILERS

LOGGER = logger.get_logger(__name__)


class Architecture(KeyedRecord):
    """Information about a processor architecture.

    Attributes:
        name (str): Short string identifying this architecture.
        description (str): Description of the architecture.
    """

    __key__ = 'name'

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def is_bluegene(self):
        return self in (IBM_BGP, IBM_BGQ)

    def is_mic(self):
        return self in (INTEL_KNC, INTEL_KNL)

    def is_ibm(self):
        return self in (IBM_BGP, IBM_BGQ, IBM64, PPC64, PPC64LE)

    def is_arm(self):
        return self in (ARM32, ARM64)

    @classmethod
    def _parse_proc_cpuinfo(cls):
        try:
            return cls._cpuinfo
        except AttributeError:
            cpuinfo = []
            core = {}
            with open("/proc/cpuinfo") as fin:
                for line in fin:
                    if line.startswith('processor'):
                        core = {}
                        continue
                    elif core and not line.strip():
                        cpuinfo.append(core)
                    else:
                        key, val = line.split(':')
                        core[key.strip()] = val.strip()
            LOGGER.debug("Detected %d processors", len(cpuinfo))
            cls._cpuinfo = cpuinfo
            return cls._cpuinfo


    @classmethod
    def detect(cls):
        """Detect the processor architecture we are currently executing on.

        Mostly relies on Python's platform module but may also probe
        environment variables and file systems in cases where the arch
        isn't immediately known to Python.  These tests may be expensive
        so the detected value is cached to improve performance.

        Returns:
            Architecture: The matching architecture description.

        Raises:
            ConfigurationError: Host architecture not supported.
        """
        try:
            return cls._detect
        except AttributeError:
            inst = None
            if os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc-bgp-linux-gcc"):
                inst = IBM_BGP
            elif os.path.exists("/bgsys/drivers/ppcfloor/gnu-linux/bin/powerpc64-bgq-linux-gcc"):
                inst = IBM_BGQ
            elif os.path.exists("/proc/cpuinfo"):
                core0 = cls._parse_proc_cpuinfo()[0]
                if 'GenuineIntel' in core0.get('vendor_id', ''):
                    model_name = core0.get('model name', '')
                    if 'CoCPU' in model_name:
                        inst = INTEL_KNC
                    elif 'Xeon Phi' in model_name:
                        inst = INTEL_KNL
            # If all else fails ask Python
            if inst is None:
                import platform
                python_arch = platform.machine()
                try:
                    inst = Architecture.find(python_arch)
                except KeyError:
                    raise ConfigurationError("Host architecture '%s' is not yet supported" % python_arch)
            cls._detect = inst
            return cls._detect


class OperatingSystem(KeyedRecord):
    """Information about an operating system.

    Attributes:
        name (str): Short string identifying this operating system.
        description (str): Description of the operating system.
    """

    __key__ = 'name'

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def is_cray_login(self):
        if self is CRAY_CNL:
            if util.which('aprun'):
                return False
            return True
        return False

    @classmethod
    def detect(cls):
        """Detect the operating system we are currently running on.

        Mostly relies on Python's platform module but may also probe
        environment variables and file systems in cases where the arch
        isn't immediately known to Python.  These tests may be expensive
        so the detected value is cached to improve performance.

        Returns:
            OperatingSystem: The matching operating system description.

        Raises:
            ConfigurationError: Host operating system not supported.
        """
        try:
            return cls._detect
        except AttributeError:
            if 'CRAYOS_VERSION' in os.environ or 'PE_ENV' in os.environ:
                inst = CRAY_CNL
            elif HOST_ARCH.is_bluegene():
                inst = IBM_CNK
            else:
                import platform
                python_os = platform.system()
                try:
                    inst = OperatingSystem.find(python_os)
                except KeyError:
                    raise ConfigurationError("Host operating system '%s' is not yet supported" % python_os)
            cls._detect = inst
            return cls._detect


class TauMagic(KeyedRecord):
    """Maps (architecture, operating system) tuples to TAU's magic words.

    The key is a (Architecture, OperatingSystem) tuple since TAU's architecture mapping is not one-to-one.
    The magic word 'ibm64linux' corresponds to several different architectures and operating systems and
    TAU's magic 'x86_64' could be a tradional CPU or a KNL.  TAU Commander needs to know the "real" CPU
    architecture and operating system so it can chose the right compilers and dependencies for TAU.

    Attributes:
        name (str): Name of the TAU architecture (the magic word)
        architecture (Architecture): Architecture object for this TAU architecture.
        operating_system (OperatingSystem): OperatingSystem object for this TAU architecture.
        preferred_families (dict): Preferred compiler families indexed by :any:`Knowledgebase`.
    """

    __key__ = '_arch_os'

    def __init__(self, arch_os, name, preferred_families):
        self._arch_os = arch_os
        self.name = name
        self.architecture = arch_os[0]
        self.operating_system = arch_os[1]
        self.preferred_families = preferred_families

    @classmethod
    def detect(cls):
        """Detect TAU magic for the target we are currently executing on.

        Mostly relies on Python's platform module but may also probe
        environment variables and file systems in cases where the arch
        isn't immediately known to Python.  These tests may be expensive
        so the detected value is cached to improve performance.

        Returns:
            TauMagic: The matching taucmdr architecture description.

        Raises:
            ConfigurationError: Host architecture or operating system not supported.
        """
        try:
            return cls._detect
        except AttributeError:
            try:
                inst = TauMagic.find((HOST_ARCH, HOST_OS))
            except KeyError:
                raise ConfigurationError("%s on %s is not supported." % (HOST_OS, HOST_ARCH))
            cls._detect = inst
            return cls._detect



X86_64 = Architecture('x86_64', 'x86_64')
INTEL_KNC = Architecture('KNC', 'Intel Knights Corner')
INTEL_KNL = Architecture('KNL', 'Intel Knights Landing')
IBM_BGL = Architecture('BGL', 'IBM BlueGene/L')
IBM_BGP = Architecture('BGP', 'IBM BlueGene/P')
IBM_BGQ = Architecture('BGQ', 'IBM BlueGene/Q')
IBM64 = Architecture('ibm64', 'IBM 64-bit Power')
PPC64 = Architecture('ppc64', 'IBM 64-bit PowerPC')
PPC64LE = Architecture('ppc64le', 'IBM 64-bit PowerPC (Little Endian)')
ARM32 = Architecture('aarch32', '32-bit ARM')
ARM64 = Architecture('aarch64', '64-bit ARM')

DARWIN = OperatingSystem('Darwin', 'Darwin')
LINUX = OperatingSystem('Linux', 'Linux')
IBM_CNK = OperatingSystem('CNK', 'Compute Node Kernel')
CRAY_CNL = OperatingSystem('CNL', 'Compute Node Linux')
ANDROID = OperatingSystem('Android', 'Android')



TAU_APPLE = TauMagic((X86_64, DARWIN), 'apple',
                     {HOST_COMPILERS: host.APPLE_LLVM,
                      MPI_COMPILERS: mpi.SYSTEM,
                      SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_X86_64 = TauMagic((X86_64, LINUX), 'x86_64',
                      {HOST_COMPILERS: host.GNU,
                       MPI_COMPILERS: mpi.SYSTEM,
                       SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_CRAYCNL = TauMagic((X86_64, CRAY_CNL), 'craycnl',
                       {HOST_COMPILERS: host.CRAY,
                        MPI_COMPILERS: mpi.CRAY,
                        SHMEM_COMPILERS: shmem.CRAY_SHMEM})

TAU_MIC_LINUX = TauMagic((INTEL_KNC, LINUX), 'mic_linux',
                         {HOST_COMPILERS: host.INTEL,
                          MPI_COMPILERS: mpi.INTEL,
                          SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_KNL = TauMagic((INTEL_KNL, LINUX), 'x86_64',
                   {HOST_COMPILERS: host.INTEL,
                    MPI_COMPILERS: mpi.INTEL,
                    SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_CRAY_KNL = TauMagic((INTEL_KNL, CRAY_CNL), 'craycnl',
                        {HOST_COMPILERS: host.CRAY,
                         MPI_COMPILERS: mpi.CRAY,
                         SHMEM_COMPILERS: shmem.CRAY_SHMEM})

TAU_BGP = TauMagic((IBM_BGP, IBM_CNK), 'bgp',
                   {HOST_COMPILERS: host.IBM_BG,
                    MPI_COMPILERS: mpi.IBM,
                    SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_BGQ = TauMagic((IBM_BGQ, IBM_CNK), 'bgq',
                   {HOST_COMPILERS: host.IBM_BG,
                    MPI_COMPILERS: mpi.IBM,
                    SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_IBM64_LINUX = TauMagic((IBM64, LINUX), 'ibm64linux',
                           {HOST_COMPILERS: host.IBM,
                            MPI_COMPILERS: mpi.IBM,
                            SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_PPC64_LINUX = TauMagic((PPC64, LINUX), 'ibm64linux',
                           {HOST_COMPILERS: host.IBM,
                            MPI_COMPILERS: mpi.IBM,
                            SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_PPC64LE_LINUX = TauMagic((PPC64LE, LINUX), 'ibm64linux',
                             {HOST_COMPILERS: host.IBM,
                              MPI_COMPILERS: mpi.IBM,
                              SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_ARM32_LINUX = TauMagic((ARM32, LINUX), 'arm_linux',
                           {HOST_COMPILERS: host.GNU,
                            MPI_COMPILERS: mpi.SYSTEM,
                            SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_ARM64_LINUX = TauMagic((ARM64, LINUX), 'arm64_linux',
                           {HOST_COMPILERS: host.GNU,
                            MPI_COMPILERS: mpi.SYSTEM,
                            SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_ARM32_ANDROID = TauMagic((ARM32, ANDROID), 'arm_android',
                             {HOST_COMPILERS: host.GNU,
                              MPI_COMPILERS: mpi.SYSTEM,
                              SHMEM_COMPILERS: shmem.OPENSHMEM})

HOST_ARCH = Architecture.detect()
HOST_OS = OperatingSystem.detect()
HOST_TAU_MAGIC = TauMagic.detect()
