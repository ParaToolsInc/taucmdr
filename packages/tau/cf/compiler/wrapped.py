#"""
#@file
#@author John C. Linford (jlinford@paratools.com)
#@version 1.0
#
#@brief
#
# This file is part of TAU Commander
#
#@section COPYRIGHT
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
#"""

import os
import subprocess
from tau import logger, util
from tau.cf.compiler import MPI_FAMILY_NAME, SYSTEM_FAMILY_NAME
from tau.cf.compiler.installed import InstalledCompiler

LOGGER = logger.getLogger(__name__)

class WrappedCompiler(InstalledCompiler):
    """Information on a compiler wrapped by another compiler.
    
    Attributes:
        wrapper: InstalledCompiler object for the compiler command wrapping this compiler
        include_path: List of paths to search for header files
        library_path: List of paths to search for library files
        compiler_flags: List of additional compiler flags
        linker_flags: List of additional linker flags
    """   
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.include_path = []
        self.library_path = []
        self.compiler_flags = []
        self.linker_flags = []
        if wrapper.family == MPI_FAMILY_NAME:
            wrapped_cmd = self._mpi_identify_wrapped()
        else:
            raise NotImplementedError
        super(WrappedCompiler,self).__init__(wrapped_cmd)
        
    def _parse_args(self, args):
        wrapped_cmd = args[0]
        for arg in args:
            if arg.startswith('-I'):
                self.include_path.append(arg[2:])
            elif arg.startswith('-L'):
                self.library_path.append(arg[2:])
            elif arg.startswith('-l'):
                self.linker_flags.append(arg)
            else:
                self.compiler_flags.append(arg)
        LOGGER.debug("Wrapped include path: %s" % self.include_path)
        LOGGER.debug("Wrapped library path: %s" % self.library_path)
        LOGGER.debug("Wrapped linker flags: %s" % self.linker_flags)
        return wrapped_cmd

    def _mpi_identify_wrapped(self):
        """
        Discovers information about an MPI compiler command wrapping another compiler.
        """ 
        LOGGER.debug("Probing MPI compiler '%s' to discover wrapped compiler" % self.wrapper.command)
        cmd = [self.wrapper.absolute_path, '-show']
        LOGGER.debug("Creating subprocess: cmd=%s" % cmd)
        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            raise RuntimeError("%s failed with return code %d: %s" % 
                               (cmd, err.returncode, err.output))
        LOGGER.debug(stdout)
        LOGGER.debug("%s returned 0" % cmd)
        try:
            return self._parse_args(stdout.split())
        except IndexError:
            raise RuntimeError("Unexpected output from %s: %s" % (cmd, stdout))
