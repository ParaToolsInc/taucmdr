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
"""TAU Commander hierarchical file and record storage system.

System-level records are globally readable and writable, depending on the user's 
system access level.  System-level is a good place for software package installations
and some system-specific configurations, e.g. target or compiler configurations.

User-level records are readable and writable by (at least) the user.  User-level is also
where software is installed when the user doesn't have write access to :any:`SYSTEM_PREFIX`.  
It's a good place for user-specific records, i.e. preferences or encrypted login credentials.

Project-level records define the project and its member components.  The user may also
want to install software packages at the project level to avoid quotas or in situations
where :any:`USER_PREFIX` is not accessible from cluster compute nodes.
"""

from tau import SYSTEM_PREFIX, USER_PREFIX
from tau.cf.storage.local_file import LocalFileStorage
from tau.cf.storage.project import ProjectStorage


SYSTEM_STORAGE = LocalFileStorage('system', SYSTEM_PREFIX)
"""System-level data storage."""

USER_STORAGE = LocalFileStorage('user', USER_PREFIX)
"""User-level data storage."""

PROJECT_STORAGE = ProjectStorage()
"""Project-level data storage."""

ORDERED_LEVELS = (PROJECT_STORAGE, USER_STORAGE, SYSTEM_STORAGE)
"""All storage levels in their preferred order."""

STORAGE_LEVELS = {level.name: level for level in ORDERED_LEVELS}
"""All storage levels indexed by their names."""
