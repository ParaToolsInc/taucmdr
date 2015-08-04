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

import subprocess
from tau import logger
from tau.error import InternalError
from tau.cf.compiler.installed import InstalledCompiler

LOGGER = logger.getLogger(__name__)


class MpiInstalledCompiler(InstalledCompiler):
    """
    TODO: Docs
    """   
    def __init__(self, compiler_cmd):
        """
        Discovers information about the compiler wrapped by this MPI compiler
        """ 
        super(MpiInstalledCompiler,self).__init__(compiler_cmd)
        LOGGER.debug("Probing MPI compiler '%s' to discover wrapped compiler" % self.command)
        cmd = [self.absolute_path, '-show']
        LOGGER.debug("Creating subprocess: cmd=%s" % cmd)
        try:
            stdout = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            raise InternalError("%s failed with return code %d: %s" % 
                                (cmd, err.returncode, err.output))
        else:
            LOGGER.debug(stdout)
            LOGGER.debug("%s returned 0" % cmd)

        parts = stdout.split()
        try:
            self.wrapped = InstalledCompiler(parts[0])
        except IndexError:
            raise InternalError("Unexpected output from %s: %s" % (cmd, stdout))
        LOGGER.info("Determined %s is wrapping %s (%s)" % 
                    (self.absolute_path, self.wrapped.short_descr, self.wrapped.absolute_path))

        self.include_path = []
        self.library_path = []
        self.libraries = []
        for part in parts[1:]:
            if part.startswith('-I'):
                self.include_path.append(part[2:])
            elif part.startswith('-L'):
                self.library_path.append(part[2:])
            elif part.startswith('-l'):
                self.libraries.append(part)

        LOGGER.debug("MPI include path: %s" % self.include_path)
        LOGGER.debug("MPI library path: %s" % self.library_path)
        LOGGER.debug("MPI libraries: %s" % self.libraries)
