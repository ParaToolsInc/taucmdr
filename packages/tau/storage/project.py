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

import os
from tau import logger, util
from tau import SYSTEM_PREFIX, USER_PREFIX, PROJECT_DIR
from tau.storage import StorageError
from tau.storage.local_file import LocalFileStorage

LOGGER = logger.get_logger(__name__)

class UninitializedProjectError(StorageError):
    """Indicates that the project storage has not been initialized."""

    message_fmt = ("%(value)s\n"
                   "\n"
                   "%(hints)s\n"
                   "Please contact %(contact)s for assistance.")

    def __init__(self, search_root):
        """Initialize the error object.
        
        Args:
            search_root (str): Directory in which the search for a project directory was initiated.
        """
        from tau.cli.commands.initialize import COMMAND as init_cmd
        value = "Project not found in '%s' or any of its parent directories." % search_root
        hints = ['Use `%s` to create a new project.' % init_cmd]
        super(UninitializedProjectError, self).__init__(value, *hints)
        self.search_root = search_root
        


class ProjectStorage(LocalFileStorage):
    """Handle the special case project storage.
    
    Each TAU Commander project has its own project storage that holds project-specific files
    (i.e. performance data) and the project configuration.
    """
    
    def __init__(self):
        super(ProjectStorage, self).__init__('project', None)
        
    def connect_filesystem(self, *args, **kwargs):
        """Prepares the store filesystem for reading and writing."""
        try:
            project_prefix = self.prefix
        except UninitializedProjectError:
            project_prefix = os.path.join(os.getcwd(), PROJECT_DIR)
            try:
                util.mkdirp(project_prefix)
            except Exception as err:
                raise StorageError("Failed to access %s filesystem prefix '%s': %s" % 
                                   (self.name, project_prefix, err))
            LOGGER.debug("Initialized %s filesystem prefix '%s'", self.name, project_prefix)

    @property
    def prefix(self):
        """Searches the current directory and its parents for a TAU Commander project directory.
        
        This method **does not** create or modify files.  If the project directory cannot be found
        then an error is raised.  It's up to the caller to determine how the error should be handled.
        
        Returns:
            str: The project directory, i.e. this storage container's filesystem prefix.
        
        Raises:
            UninitializedProjectError: Neither the current directory nor any of its parent directories contain
                                       a TAU Commander project directory.
        """
        if not self._prefix:
            cwd = os.getcwd()
            LOGGER.debug("Searching upwards from '%s' for '%s'", cwd, PROJECT_DIR)
            root = cwd
            lastroot = None
            while root and root != lastroot:
                project_prefix = os.path.join(root, PROJECT_DIR)
                if project_prefix not in [USER_PREFIX, SYSTEM_PREFIX] and os.path.isdir(project_prefix):
                    LOGGER.debug("Located project storage prefix '%s'", project_prefix)
                    self._prefix = project_prefix
                    break
                lastroot = root
                root = os.path.dirname(root)
            else:
                raise UninitializedProjectError(cwd)
        return self._prefix
