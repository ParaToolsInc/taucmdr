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
"""TAU Commander settings.

FIXME: settings needs a design review.
"""

from tau import logger
from tau.core.setting import Setting


LOGGER = logger.get_logger(__name__)

_DATA = {}


def _load():
    for record in Setting.all():
        key = record['key']
        val = record['value']
        _DATA[key] = val
    LOGGER.debug("Loaded settings: %r", _DATA)


def _save():
    LOGGER.debug("Saving settings: %r", _DATA)
    for key, val in _DATA.iteritems():
        if Setting.exists({'key': key}):
            Setting.update({'value': val}, {'key': key})
        else:
            Setting.create({'key': key, 'value': val})


def get(key):
    """
    Get the value of setting 'key' or None if not set
    """
    if not _DATA:
        _load()
    return _DATA.get(key, None)


def set(key, val):
    """
    Set setting 'key' to value 'val'
    """
    _DATA[key] = val
    _save()


def unset(key):
    """
    Remove setting 'key' from the list of settings
    """
    Setting.delete({'key': key})
