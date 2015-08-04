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
#pylint: disable=too-many-instance-attributes
#pylint: disable=too-few-public-methods
#pylint: disable=too-many-arguments

import os
import hashlib
from tau import logger, util
from tau.error import ConfigurationError
from tau.cf.compiler import Compiler, KNOWN_FAMILIES
from tau.cf.compiler.role import CC_ROLE, CXX_ROLE, FC_ROLE, REQUIRED_ROLES

LOGGER = logger.getLogger(__name__)


class InstalledCompiler(Compiler):
    """Information about an installed compiler command.
    
    Attributes:
        path: Absolute path to folder containing the compiler command
        absolute_path: Absolute path to the compiler command
        md5sum: The md5 checksum of the compiler binary
    """
    
    def __init__(self, compiler_cmd):
        """Probes the system to initialize the InstalledCompiler object.
        
        Checks PATH and file permissions to see that compiler command is
        present and executable.  Calculates the md5 checksum of the compiler
        binary file so we can recognize if it changes.
        """
        LOGGER.debug("Identifying compiler: %s" % compiler_cmd)
        abspath = util.which(compiler_cmd)
        if not abspath:
            raise ConfigurationError("'%s' missing or not executable." % compiler_cmd,
                                     "Check spelling, loaded modules, PATH environment variable, and file permissions")
        if not util.file_accessible(abspath):
            raise ConfigurationError("Compiler '%s' not readable." % abspath, 
                                     "Check file permissions on '%s'" % abspath)
        md5sum = hashlib.md5()
        with open(abspath, 'r') as compiler_file:
            md5sum.update(compiler_file.read())
        # Executable found, initialize this object
        super(InstalledCompiler,self).__init__(os.path.basename(compiler_cmd))
        self.path = os.path.dirname(abspath)
        self.absolute_path = os.path.join(self.path, self.command)
        self.md5sum = md5sum.hexdigest()
        from tau.cf.compiler.wrapped import WrappedCompiler
        try:
            self.wrapped = WrappedCompiler(self)
        except NotImplementedError:
            self.wrapped = None

    def get_siblings(self):
        """Gets all compilers in this compiler's family.
        
        Compiler commands in the same directory as this compiler's command are preferred
        over other commands found in $PATH.
        
        Returns:
            List of InstalledCompiler objects for the given family
            The returned list will have at least one item for all roles in REQUIRED_ROLES.
    
        Raises:
            ConfigurationError: Some required roles couldn't be filled.
        """
        LOGGER.debug("Identifying siblings of %s" % self.absolute_path)
        missing_roles = list(set([role.keyword for role in REQUIRED_ROLES]) - set(self.role.keyword))
        family = KNOWN_FAMILIES[self.family]
        found = [self]
        for comp in family:
            if comp.role != self.role:
                try:
                    sibling = InstalledCompiler(os.path.join(self.path, comp.command))
                except ConfigurationError as err:
                    LOGGER.debug(err)
                else:
                    found.append(sibling)
                    missing_roles.remove(sibling.role.keyword)
        if missing_roles:
            family = InstalledCompiler.get_family(self.family)
            found.extend([comp for comp in family if comp.role != self.role])
        return found

    @staticmethod
    def get_default(role):
        """Gets the default compiler for the specified role.
        
        Args:
            role: CompilerRole identifying compiler role to be filled.
            
        Returns:
            InstalledCompiler object for the default compiler.
            
        Raises:
            ConfigurationError: Default compiler cannot be found.
        """
        LOGGER.debug("'Getting default %s compiler for role '%s'" % (role.language, role.keyword))
        # TODO: Check PATH, loaded modules, etc to determine default
        # TORO: instead of just falling back to GNU all the time
        defaults = {CC_ROLE.keyword: 'gcc',
                    CXX_ROLE.keyword: 'g++',
                    FC_ROLE.keyword: 'gfortran'}
        try:
            default_cmd = defaults[role.keyword]
        except KeyError:
            raise ConfigurationError("No default compiler %s compiler identified." % role.language)
        return InstalledCompiler(default_cmd)
    
    @staticmethod
    def get_family(family):
        """Gets all installed compilers in a compiler family.
    
        Args:
            family: A family name, e.g. 'Intel'
             
        Returns:
            List of InstalledCompiler objects for the given family
            The returned list will have at least one item for all roles in REQUIRED_ROLES.
    
        Raises:
            ConfigurationError: Invalid compiler family or some required roles couldn't be filled.
        """
        LOGGER.debug("Discovering installed %s compilers" % family)
        try:
            family = KNOWN_FAMILIES[family]
        except KeyError:
            raise ConfigurationError("Invalid compiler family: %s" % family,
                                     "Known families: " % KNOWN_FAMILIES.keys())
        missing_roles = list(REQUIRED_ROLES)
        missing_err = {}
        found = []
        for comp in family:
            try:
                installed = InstalledCompiler(comp.command)
            except ConfigurationError as err:
                # A compiler wasn't found in PATH, but that's OK because 
                # another compiler may provide the missing role
                LOGGER.debug("Skipping '%s': %s" % (comp.command, err))
                missing_err[comp.role] = err
                continue
            else:
                found.append(installed)
                try: missing_roles.remove(comp.role)
                except ValueError: pass
        if missing_roles:
            raise ConfigurationError("One or more compiler roles could not be filled:\n%s" %
                                     util.pformat_dict(missing_err, indent=2),
                                     "Update your PATH, load environment modules, or install missing compilers.")
        return found
