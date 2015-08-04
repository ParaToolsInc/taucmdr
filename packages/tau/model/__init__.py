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

import sys
from pkgutil import walk_packages
from tau import logger, error, controller

ModelError = controller.ModelError

# List model classes


def _yieldModelClasses():
    def camelcase(name): 
        return ''.join(x.capitalize() for x in name.split('_'))
    
    for _, module_name, _ in walk_packages(__path__, __name__ + '.'):
        __import__(module_name)
        module_dict = sys.modules[module_name].__dict__
        model_class_name = camelcase(module_name.split('.')[-1])
        try:
            model_class = module_dict[model_class_name]
        except KeyError:
            raise error.InternalError("module '%s' does not define class '%s'" %
                                      (module_name, model_class_name))
        yield model_class
MODEL_CLASSES = list(_yieldModelClasses())

# Index model classes by name
MODELS = dict([(cls.__name__, cls) for cls in MODEL_CLASSES])


def _getPropsModelName(p):
    try:
        return p['model']
    except KeyError:
        return p['collection']

# Set cls.model_name
for cls_name, cls in MODELS.iteritems():
    cls.model_name = cls_name

# Set cls.associations
for cls_name, cls in MODELS.iteritems():
    if not hasattr(cls, 'associations'):
        cls.associations = {}
    if not hasattr(cls, 'references'):
        cls.references = set()

    for attr, props in cls.attributes.iteritems():
        via = props.get('via', None)
        try:
            foreign_name = _getPropsModelName(props)
        except KeyError:
            if via:
                raise ModelError(cls, "Attribute '%s' defines 'via' property "
                                 "but not 'model' or 'collection'" % attr)
            else:
                continue

        try:
            foreign_cls = MODELS[foreign_name]
        except KeyError:
            raise ModelError(
                cls, "Invalid model name in attribute '%s'" % attr)
        if not hasattr(foreign_cls, 'associations'):
            foreign_cls.associations = {}
        if not hasattr(foreign_cls, 'references'):
            foreign_cls.references = set()

        forward = (foreign_cls, via)
        reverse = (cls, attr)
        if not via:
            foreign_cls.references.add(reverse)
        else:
            foreign_cls.associations[via] = reverse
            try:
                via_props = foreign_cls.attributes[via]
            except KeyError:
                raise ModelError(cls, "Found 'via' on undefined attribute '%s.%s'" %
                                 (foreign_name, via))
            try:
                via_attr_model_name = _getPropsModelName(via_props)
            except KeyError:
                raise ModelError(cls, "Found 'via' on non-model attribute '%s.%s'" %
                                 (foreign_name, via))
            if via_attr_model_name != cls_name:
                raise ModelError(cls, "Attribute %s.%s referenced by 'via' in '%s' "
                                 "does not define 'collection' or 'model' of type '%s'" %
                                 (foreign_name, via, attr, cls_name))
            try:
                existing = cls.associations[attr]
            except KeyError:
                cls.associations[attr] = forward
            else:
                if existing != forward:
                    raise ModelError(cls,
                                     "Conflicting associations on attribute '%s': "
                                     "%r vs. %r" % (attr, existing, forward))

# Clean up
del _yieldModelClasses
del _getPropsModelName
