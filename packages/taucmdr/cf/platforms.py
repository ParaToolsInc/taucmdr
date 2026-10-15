#
# Copyright (c) 2015-2026, ParaTools, Inc.
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

    @classmethod
    def detect(cls):
        """Detect the processor architecture we are currently executing on.

        Asks Python's platform module.  The detected value is cached.

        Returns:
            Architecture: The matching architecture description.

        Raises:
            ConfigurationError: Host architecture not supported.
        """
        try:
            return cls._detect
        except AttributeError:
            import platform
            python_arch = platform.machine()
            try:
                inst = Architecture.find(python_arch)
            except KeyError as err:
                raise ConfigurationError("Host architecture '%s' is not yet supported" % python_arch) from err
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
            else:
                import platform
                python_os = platform.system()
                try:
                    inst = OperatingSystem.find(python_os)
                except KeyError as err:
                    raise ConfigurationError("Host operating system '%s' is not yet supported" % python_os) from err
            cls._detect = inst
            return cls._detect


class TauMagic(KeyedRecord):
    """Maps (architecture, operating system) tuples to TAU's magic words.

    The key is a (Architecture, OperatingSystem) tuple since TAU's architecture mapping is not one-to-one.
    For example, TAU uses the magic word 'craycnl' for every Cray system, whatever its CPU.  TAU Commander needs to
    know the "real" CPU architecture and operating system so it can chose the right compilers and dependencies for TAU.

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
            except KeyError as err:
                raise ConfigurationError(f"{HOST_OS} on {HOST_ARCH} is not supported.") from err
            cls._detect = inst
            return cls._detect



X86_64 = Architecture('x86_64', 'x86_64')
PPC64LE = Architecture('ppc64le', 'IBM 64-bit PowerPC (Little Endian)')
ARM64 = Architecture('aarch64', '64-bit ARM')

DARWIN = OperatingSystem('Darwin', 'Darwin')
LINUX = OperatingSystem('Linux', 'Linux')
# HPE Cray EX and older Cray systems.  TAU calls all of them 'craycnl'.
CRAY_CNL = OperatingSystem('CNL', 'Compute Node Linux')


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

TAU_PPC64LE_LINUX = TauMagic((PPC64LE, LINUX), 'ibm64linux',
                             {HOST_COMPILERS: host.IBM,
                              MPI_COMPILERS: mpi.IBM,
                              SHMEM_COMPILERS: shmem.OPENSHMEM})

TAU_ARM64_LINUX = TauMagic((ARM64, LINUX), 'arm64_linux',
                           {HOST_COMPILERS: host.GNU,
                            MPI_COMPILERS: mpi.SYSTEM,
                            SHMEM_COMPILERS: shmem.OPENSHMEM})

HOST_ARCH = Architecture.detect()
HOST_OS = OperatingSystem.detect()
HOST_TAU_MAGIC = TauMagic.detect()
