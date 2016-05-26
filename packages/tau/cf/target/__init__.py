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
"""Target hardware and software detection and defaults."""

from tau.error import InternalError
from tau.cf import KeyedRecord


#TAU and PDT recognize these "magic word" architectures.
# Many of these haven't been tested in years and are probably broken.
MAGIC_ARCH_NAMES = {
    "apple":         "i386 or x86_64 running Darwin",
    "arm_linux":     "ARM running Linux",
    "mic_linux":     "Intel MIC running k1om Linux",
    "ppc64":         "PowerPC64 running POWER Linux",
    "bgl":           "BlueGene/L",
    "bgp":           "BlueGene/P",
    "bgq":           "BlueGene/Q",
    "ia64":          "No Description",
    "crayxmt":       "No Description",
    "xt3":           "No Description",
    "craycnl":       "Cray supercomputer running Compute Node Linux",
    "x86_64":        "No Description",
    "freebsd":       "No Description",
    "386BSD":        "Intel 386, running 386BSD",
    "VMS_POSIX":     "vax running VMS/POSIX",
    "aix370":        "IBM 370, running aix",
    "aixESA":        "IBM ESA, running aix",
    "alliant":       "Alliant FX series",
    "alliant_fx2800":"Alliant FX2800 (i860 based)",
    "alliant_fx80":  "Alliant FX80 (mc68000 based)",
    "alpha":         "DEC Alpha running OSF/1",
    "amdahl":        "Amdahl running uts 2.1",
    "amiga":         "amiga running amix 2.02",
    "apollo":        "Apollo running DomainOS",
    "att3b15":       "AT&T 3b15",
    "att3b2":        "AT&T 3b2",
    "att3b20":       "AT&T 3b20",
    "att3b5":        "AT&T 3b5",
    "balance":       "Sequent Balance (32000 based)",
    "bsd386":        "Intel 386, running BSDI's bsd386",
    "c90":           "Cray C90 running Unicos",
    "cm2":           "Thinking Machines Corperation CM-2",
    "cm5":           "Thinking Machines Corperation CM-5",
    "coh386":        "386 running Coherent 4.0",
    "coherent":      "Unknown machine running Coherent",
    "convex":        "Convex",
    "cray":          "Cray running Unicos",
    "decmips":       "No Description",
    "decstation":    "DecStation XXXX",
    "eta10":         "ETA 10 running SVR3",
    "gould_np1":     "Gould NP1",
    "gp1000":        "BBN GP1000 (Butterfly 1) running MACH",
    "hk68":          "Heurikon HK68 running Uniplus+ 5.0",
    "hp":            "HP, running hpux",
    "hp300":         "HP 9000, series 300, running mtXinu",
    "hp800":         "HP 9000, series 800, running mtXinu",
    "hp9000s300":    "HP 9000, series 300, running hpux",
    "hp9000s500":    "HP 9000, series 500, running hpux",
    "hp9000s700":    "HP 9000, series 700, running hpux",
    "hp9000s800":    "HP 9000, series 800, running hpux",
    "i386":          "Intel 386, generic",
    "i386_emx":      "Intel 386, running emx [unix emulation under OS/2]",
    "i386_linux":    "Intel 386, running Linux",
    "i386_mach":     "Intel 386, running mach",
    "i860":          "Intel i860 Hypercube",
    "intel386":      "Intel 386, running INTEL's SVR3",
    "sgi4k":         "Silicon Graphics R4K based machine",
    "sgi8k":         "Silicon Graphics R8K based machine",
    "isc386":        "Intel 386, running ISC",
    "ksr1":          "Kendall Square KSR1",
    "m68k":          "mc68000 CPU machine",
    "m88k":          "mc88000 CPU machine",
    "mac2":          "Apple Computer Macintosh II, running AUX",
    "masscomp":      "Concurrent (Masscomp), running RTU",
    "minix":         "mac or amiga running minix",
    "minix386":      "i386 running minix",
    "mips":          "another mips CPU",
    "multimax":      "Encore Computer Corp. Multimax (32000 based)",
    "nd500":         "Norsk Data ND 500/5000 running Ndix",
    "news":          "Sony NEWS 800 or 1700 workstation",
    "news_mips":     "NeWS machine with mips CPU",
    "next":          "NeXT computer",
    "ns32000":       "NS32000 CPU machine",
    "opus":          "No Description",
    "paragon":       "Intel paragon running OSF1/Mach",
    "pfa50":         "PFU/Fujitsu A-xx computer",
    "ps2":           "IBM PS/2, running aix",
    "ptx":           "Sequent Symmetry running DYNIX/ptx (386/486 based)",
    "pyramid":       "Pyramid Technology computer (of any flavor)",
    "rs6000":        "IBM RS6000, running aix",
    "rt":            "IBM PC/RT, running BSD (AOS 4.3) or mach",
    "rtpc":          "IBM PC/RT, running aix",
    "sco386":        "Intel 386, running SCO",
    "solaris2":      "Sun Workstation running SVR4 Solaris",
    "stellar":       "stellar running stellix",
    "sun":           "Sun workstation of none of the above types",
    "sun2":          "Sun Microsystems series 2 workstation (68010 based)",
    "sun3":          "Sun Microsystems series 3 workstation (68020 based)",
    "sun386i":       "Sun Microsystems 386i workstation (386 based)",
    "sun4":          "Sun Microsystems series 4 workstation (SPARC based)",
    "symmetry":      "Sequent Symmetry running DYNIX 3 (386/486 based)",
    "sysV68":        "No Description",
    "sysV88":        "Motorola MPC running System V/88 R32V2 (SVR3/88100 based)",
    "tahoe":         "tahoe running 4BSD",
    "tc2000":        "BBN TC2000 (Butterfly 2) running MACH",
    "tek4300":       "Tektronix 4300 running UTek (BSD 4.2 / 68020 based)",
    "tekXD88":       "Tektronix XD88/10 running UTekV 3.2e (SVR3/88100 based)",
    "titan":         "Stardent Titan",
    "unixpc":        "UNIX/PC running SVR1 att7300 aka att3b1",
    "unknown":       "machine type could not be determined",
    "vax":           "Digital Equipment Corp. Vax (of any flavor)",
    "vistra800":     "Stardent Vistra 800 running SVR4",
    }


class OperatingSystem(KeyedRecord):
    """Information about a target operating system.
    
    Attributes:
        name (str): Short string identifying this operating system.
        description (str): Description of the operating system.
    """
    
    __key__ = 'name'
    
    def __init__(self, name, description):
        self.name = name
        self.description = description

        
class Architecture(KeyedRecord):
    """Information about a target architecture.
    
    Attributes:
        name (str): Short string identifying this architecture.
        description (str): Description of the architecture. 
    """
    
    __key__ = 'name'
    
    def __init__(self, name, description):
        self.name = name
        self.description = description


class TauArch(KeyedRecord):
    """Maps (operating system, architecture pairs) to TAU's magic words.
    
    Attributes:
        name (str): Name of the TAU architecture (the magic word)
        architecture (Architecture): Architecture object for this TAU architecture.
        operating_system (OperatingSystem): OperatingSystem object for this TAU architecture.
    """
    
    __key__ = 'name'
    
    def __init__(self, name, architecture, operating_system):
        self.name = name
        self.architecture = architecture
        self.operating_system = operating_system
        
    @classmethod
    def get(cls, targ_arch, targ_os):
        """Look up the TAU magic word matching an architecture and operating system.
        
        Args:
            targ_arch: :any:`Architecture` or string name identifying the target architecture.
            targ_os: :any:`OperatingSystem` or string name identifying the target operating system.
            
        Returns:
            str: The TAU magic word for the target.
        """
        if isinstance(targ_arch, basestring):
            targ_arch = Architecture.find(targ_arch)
        if isinstance(targ_os, basestring):
            targ_os = OperatingSystem.find(targ_os)
        for tau_arch in cls.all():
            if tau_arch.architecture == targ_arch and tau_arch.operating_system == targ_os:
                return tau_arch
        raise KeyError


DARWIN_OS = OperatingSystem('Darwin', 'Darwin')
LINUX_OS = OperatingSystem('Linux', 'Linux')
IBM_CNK_OS = OperatingSystem('CNK', 'Compute Node Kernel')
CRAY_CNL_OS = OperatingSystem('CNL', 'Compute Node Linux')
ANDROID_OS = OperatingSystem('Android', 'Android')

X86_64_ARCH = Architecture('x86_64', 'x86_64')
INTEL_KNC_ARCH = Architecture('knc', 'Intel Knights Corner')
#INTEL_KNL_ARCH = Architecture('knl', 'Intel Knights Landing')
IBM_BGP_ARCH = Architecture('BGP', 'IBM BlueGene/P')
IBM_BGQ_ARCH = Architecture('BGQ', 'IBM BlueGene/Q')
IBM64_ARCH = Architecture('ibm64', 'IBM 64-bit Power')
ARM32_ARCH = Architecture('arm32', '32-bit ARM')
ARM64_ARCH = Architecture('arm64', '64-bit ARM')

TAU_ARCH_APPLE = TauArch('apple', X86_64_ARCH, DARWIN_OS)
TAU_ARCH_X86_64 = TauArch('x86_64', X86_64_ARCH, LINUX_OS)
TAU_ARCH_CRAYCNL = TauArch('craycnl', X86_64_ARCH, CRAY_CNL_OS)
TAU_ARCH_MIC_LINUX = TauArch('mic_linux', INTEL_KNC_ARCH, LINUX_OS)
TAU_ARCH_BGP = TauArch('bgp', IBM_BGP_ARCH, IBM_CNK_OS)
TAU_ARCH_BGQ = TauArch('bgq', IBM_BGQ_ARCH, IBM_CNK_OS)
TAU_ARCH_IBM64_LINUX = TauArch('ibm64linux', IBM64_ARCH, LINUX_OS)
TAU_ARCH_ARM32_LINUX = TauArch('arm_linux', ARM32_ARCH, LINUX_OS)
TAU_ARCH_ARM64_LINUX = TauArch('arm64_linux', ARM64_ARCH, LINUX_OS)
TAU_ARCH_ARM_ANDROID = TauArch('arm_android', ARM32_ARCH, ANDROID_OS)
