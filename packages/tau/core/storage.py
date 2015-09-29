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

import os
from abc import ABCMeta, abstractmethod
from tau import logger, util
from tau import SYSTEM_PREFIX, USER_PREFIX, PROJECT_DIR
from tau.error import Error, ConfigurationError
from tau.core.database import JsonDatabase


LOGGER = logger.get_logger(__name__)


class StorageError(Error):
    """Indicates a failure in the storage system."""

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "Please send '%(logfile)s' to %(contact)s for assistance.")


class ProjectStorageError(StorageError):
    """Indicates that the project storage could not be found."""

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "Please contact %(contact)s for assistance.")

    def __init__(self, search_root):
        """Initialize the error object.
        
        Args:
            search_root (str): Directory in which the search for a project directory was initiated.
        """
        value = "Project not found in '%s' or any of its parent directories." % search_root
        super(ProjectStorageError, self).__init__(value)
        self.search_root = search_root

class AbstractStorageContainer(object):
    """Abstract base class for storage containers.
    
    A storage container pairs a persistent record storage system with a persistent filesystem.
    The database may be any record storage system that implements :any:`AbstractDatabase`.
    The filesystem is accessed via its filesystem prefix, e.g. ``/usr/local/packages``.
    
    Attributes:
        name (str): The storage container's name, e.g. "system" or "user".
        prefix (str): Absolute path to the top-level directory of the container's filesystem.
        database (str): Database object implementing :any:`AbstractDatabase`. 
    """
    
    __metaclass__ = ABCMeta
    
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def prefix(self):
        """Get the filesystem prefix for file storage.
        
        The filesystem must be persistent and provide the usual POSIX filesystem calls.
        In particular, GNU software packages should be installable in the filesystem.
        
        Returns:
            str: Absolute path in the filesystem.
        """

    @abstractmethod
    def database(self):
        """Get the record storage system.
        
        Returns:
            AbstractDatabase: The database object.
        """


class JsonStorageContainer(AbstractStorageContainer):
    """Implements a storage container that uses :any:`JsonDatabase` for record storage.
    
    The JSON file containing all records will be kept in :any:`prefix`.
    """
    
    def __init__(self, name, prefix):
        super(JsonStorageContainer, self).__init__(name)
        self._prefix = prefix
        
    @property
    def prefix(self):
        """Initializes filesystem storage on first access.
        
        If the path does not exist then this function will attempt to create it.
        
        Returns:
            str: The filesystem prefix.
        """
        if not os.path.isdir(self._prefix):
            try:
                util.mkdirp(self._prefix)
            except Exception as err:
                raise StorageError("Failed to access %s filesystem prefix '%s': %s" % (self.name, self._prefix, err))
            LOGGER.debug("Initialized %s filesystem prefix '%s'", self.name, self._prefix)
        return self._prefix
        
    @property
    def database(self):
        """Initializes persistent record storage on first access.
        
        If the database does not exist then this function will attempt to create it.
        
        Returns:
            AbstractDatabase: The database object.
        
        Raises:
            StorageError: The database could not be created or accessed.
        """
        # pylint: disable=no-member,attribute-defined-outside-init
        try:
            return self._database
        except AttributeError:
            dbfile = os.path.join(self.prefix, self.name + '.json')
            try:
                self._database = JsonDatabase(dbfile)
            except ConfigurationError as err:
                raise StorageError("Failed to access %s database '%s': %s" % (self.name, dbfile, err))
            LOGGER.debug("Initialized %s database '%s'", self.name, dbfile)
            return self._database


class ProjectStorageContainer(JsonStorageContainer):
    """Handle the special case project storage container.
    
    Each TAU Commander project has its own project storage container that holds project-specific files
    (i.e. performance data) and the project configuration.
    """
    
    def __init__(self):
        super(ProjectStorageContainer, self).__init__('project', None)
        
    def exists(self):
        try:
            return bool(self.prefix)
        except StorageError:
            return False
        
    def verify(self, *hints, **kwargs):
        try:
            self.prefix
        except ProjectStorageError as err:
            default_message = "Project not found in '%s' or any of its parent directories." % err.search_root
            message = kwargs.get('message', default_message)
            raise ConfigurationError(message, *hints)
    
    def create(self, root=None):
        """Create the project container prefix and JSON database file."""
        root = root or os.getcwd()
        project_prefix = os.path.join(root, PROJECT_DIR)
        project_dbfile = os.path.join(project_prefix, self.name + '.json')
        util.mkdirp(project_prefix)
        JsonDatabase(project_dbfile)
    
    @property
    def prefix(self):
        """Searches the current directory and its parents for a TAU Commander project directory.
        
        This method **does not** create or modify files.  If the project directory cannot be found
        then an error is raised.  It's up to the caller to determine how the error should be handled.
        
        Returns:
            str: The project directory, i.e. this storage container's filesystem prefix.
        
        Raises:
            StorageError: Neither the current directory nor any of its parent directories contain
                          a TAU Commander project directory.
        """
        if not self._prefix:
            cwd = os.getcwd()
            root = cwd
            lastroot = None
            while root and root != lastroot:
                project_prefix = os.path.join(root, PROJECT_DIR)
                project_dbfile = os.path.join(project_prefix, self.name + '.json')
                if project_prefix not in [USER_PREFIX, SYSTEM_PREFIX] and util.file_accessible(project_dbfile):
                    LOGGER.debug("Located project storage prefix '%s'", project_prefix)
                    self._prefix = project_prefix
                    break
                lastroot = root
                root = os.path.dirname(root)
            else:
                raise ProjectStorageError(cwd)
        return self._prefix


SYSTEM_STORAGE = JsonStorageContainer('system', SYSTEM_PREFIX)
"""System-level data storage."""

USER_STORAGE = JsonStorageContainer('user', USER_PREFIX)
"""User-level data storage."""

PROJECT_STORAGE = ProjectStorageContainer()
"""Project-level data storage."""

ORDERED_CONTAINERS = (PROJECT_STORAGE, USER_STORAGE, SYSTEM_STORAGE)
"""All storage containers in their preferred order."""

CONTAINERS = {container.name: container for container in ORDERED_CONTAINERS}
"""All storage containers indexed by their names."""
