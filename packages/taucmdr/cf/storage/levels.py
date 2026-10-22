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
"""TAU Commander hierarchical file and record storage system.

System-level records are globally readable and writable, depending on the user's
system access level.  System-level is a good place for software package installations
and some system-specific configurations, e.g. target or compiler configurations.
The system level exists only when :any:`SYSTEM_PREFIX` is set.  A system prefix that doesn't
exist is treated as an empty, read-only level until it is created.

User-level records are readable and writable by (at least) the user.  User-level is also
where software is installed when there is no system level or the user doesn't have write access to it.
It's a good place for user-specific records, i.e. preferences or encrypted login credentials.

Project-level records define the project and its member components.  The user may also
want to install software packages at the project level to avoid quotas or in situations
where :any:`USER_PREFIX` is not accessible from cluster compute nodes.
"""


import os
from taucmdr import SYSTEM_PREFIX, USER_PREFIX
from taucmdr.error import ConfigurationError
from taucmdr.cf.storage import StorageError
from taucmdr.cf.storage.storage_dispatch import StorageDispatch, ProjectStorageDispatch

SYSTEM_STORAGE = StorageDispatch('system', SYSTEM_PREFIX, create_prefix=False) if SYSTEM_PREFIX else None
"""System-level data storage, or None if there is no system level."""

USER_STORAGE = StorageDispatch('user', USER_PREFIX)
"""User-level data storage."""

PROJECT_STORAGE = ProjectStorageDispatch()
"""Project-level data storage."""

ORDERED_LEVELS = tuple(level for level in (PROJECT_STORAGE, USER_STORAGE, SYSTEM_STORAGE) if level is not None)
"""All storage levels in their preferred order."""

STORAGE_LEVELS = {level.name: level for level in ORDERED_LEVELS}
"""All storage levels indexed by their names."""


def require_system_storage():
    """Return the system storage level.

    Raises:
        ConfigurationError: No system level exists.
    """
    if SYSTEM_STORAGE is None:
        raise ConfigurationError(
            "No system-level storage is configured.",
            "Set the environment variable TAUCMDR_SYSTEM_PREFIX to a directory for shared TAU builds.")
    return SYSTEM_STORAGE


def highest_writable_storage():
    """Return the highest-priority writable storage level, caching the result.

    Searches :data:`ORDERED_LEVELS` in reverse (system, user, project) and returns
    the first writable level found.

    Raises:
        StorageError: No writable storage levels are available.
    """
    try:
        return highest_writable_storage.value
    except AttributeError as err:
        for storage in reversed(ORDERED_LEVELS):
            if storage.is_writable():
                highest_writable_storage.value = storage
                break
        else:
            raise StorageError("No writable storage levels") from err
        return highest_writable_storage.value
