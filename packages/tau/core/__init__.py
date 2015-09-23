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
"""TAU Commander core software architecture.

TAU Commander follows the `Model-View-Controller (MVC)`_ design pattern. 
See :any:`tau.core.mvc` for implementation details.

This module notifies each data controller to construct relationships between its
model and related models.

.. _Model-View-Controller (MVC): https://en.wikipedia.org/wiki/Model-view-controller
"""

import sys
from pkgutil import walk_packages
from tau.error import InternalError
from tau.core.mvc import Controller


for _, module_name, ispkg in walk_packages(__path__, __name__ + '.'):
    if ispkg:
        controller_module_name = module_name + '.controller'
        __import__(controller_module_name)
        for cls in vars(sys.modules[controller_module_name]).itervalues():
            try:
                found_subclass = cls is not Controller and issubclass(cls, Controller)
            except TypeError:
                # Raised by issubclass when cls isn't actually a class
                continue
            if found_subclass:
                cls.__construct_relationships__()
                break
        else:
            raise InternalError("Module '%s' does not define a subclass of Controller" % controller_module_name)
