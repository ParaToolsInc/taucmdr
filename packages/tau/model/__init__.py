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
"""TODO: Describe T-A-M model here."""


def require_compiler_family(family, *hints):
    """Creates a compatibility callback to check a compiler family.
    
    Args:
        family (CompilerFamily): The required compiler family.
        *hints: String hints to show the user when the check fails.
        
    Returns:
        callable: a compatibility checking callback for use with data models.
    """
    def callback(lhs, lhs_attr, lhs_value, rhs, rhs_attr):
        """Compatibility checking callback for use with data models.

        Requires ``rhs[rhs_attr]`` to be a compiler in a certain compiler family.
        
        Args:
            lhs (Model): The model invoking `check_compatibility`.
            lhs_attr (str): Name of the attribute that defines the 'compat' property.
            lhs_value: Value of the attribute that defines the 'compat' property.
            rhs (Model): Model we are checking against (argument to `check_compatibility`).
            rhs_attr (str): The right-hand side attribute we are checking for compatibility.
            
        Raises:
            ConfigurationError: Invalid compiler family specified in target configuration.
        """
        from tau.error import ConfigurationError

        lhs_name = lhs.name.lower()
        rhs_name = rhs.name.lower()
        msg = "%s = %s in %s requires %s in %s to be a %s compiler" % (lhs_attr, lhs_value, lhs_name, 
                                                                       rhs_attr, rhs_name, family)
        try:
            compiler_record = rhs.populate(rhs_attr)
        except KeyError:
            raise ConfigurationError("%s but it is undefined" % msg)
        given_family = compiler_record['family']
        if given_family is not family:
            raise ConfigurationError("%s but it is a %s compiler" % (msg, given_family), *hints)
    return callback

