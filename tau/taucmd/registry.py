"""
@file
@author John C. Linford (jlinford@paratools.com)
@version 1.0

@brief

This file is part of the TAU Performance System

@section COPYRIGHT

Copyright (c) 2013, ParaTools, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:
 (1) Redistributions of source code must retain the above copyright notice, 
     this list of conditions and the following disclaimer.
 (2) Redistributions in binary form must reproduce the above copyright notice, 
     this list of conditions and the following disclaimer in the documentation 
     and/or other materials provided with the distribution.
 (3) Neither the name of ParaTools, Inc. nor the names of its contributors may 
     be used to endorse or promote products derived from this software without 
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import taucmd
import pickle
import pprint
from taucmd import util
from taucmd.project import Project


LOGGER = taucmd.getLogger(__name__)

USER_REGISTRY_DIR = taucmd.USER_TAU_DIR

SYSTEM_REGISTRY_DIR = taucmd.SYSTEM_TAU_DIR


class Registry(object):
    """
    TODO: Docs
    """
    def __init__(self, registry_dir=USER_REGISTRY_DIR):
        self.registry_dir = registry_dir
        self.defaults = {}
        self.projects = {}
        self.selected = None
        self.load()

#     def __str__(self):
#         return 'Selected: %s\nProjects:\n%s' % (self.selected, pprint.pformat(self.projects))
#     
#     def __len__(self):
#         return len(self.projects)
#     
#     def __iter__(self):
#         for config in self.projects.itervalues():
#             yield Project(self, config)
#             
#     def __getitem__(self, key):
#         return Project(self, self.projects[key])
    
    def load(self):
        if self.projects:
            LOGGER.debug('Registry already loaded.')
        else:
            file_path = os.path.join(self.registry_dir, 'registry')
            try:
                with open(file_path, 'rb') as fp:
                    self.selected, self.projects, self.defaults = pickle.load(fp)
                LOGGER.debug('Registry loaded from %r' % file_path)
            except:
                LOGGER.debug('Registry file %r does not exist.' % file_path)
        return self

    def save(self):
        if not self.projects:
            LOGGER.debug('Saving empty registry')
        util.mkdirp(self.registry_dir)
        file_path = os.path.join(self.registry_dir, 'registry')
        with open(file_path, 'wb') as fp:
            pickle.dump((self.selected, self.projects, self.defaults), fp)
        LOGGER.debug('Registry written to %r' % file_path)
        return self

    def getSelectedProject(self):
        try:
            return Project(self, self.projects[self.selected])
        except:
            return None

    def setSelectedProject(self, proj_name):
        # Set a project as selected
        if not proj_name in self.projects:
            raise KeyError
        self.selected = proj_name
        self.save()

    def addProject(self, config, select=True):
        # Create the project object and update the registry
        LOGGER.debug('Adding project: %r' % config)
        proj = Project(self, config)
        proj_name = proj.getName()
        projects = self.projects
        if proj_name in projects:
            raise ProjectNameError('Project %r already exists.')
        projects[proj_name] = proj.config
        if select or not self.selected:
            self.selected = proj_name
        self.save()
        return proj

    def deleteProject(self, proj_name):
        projects = self.projects
        try:
            del projects[proj_name]
            LOGGER.debug('Removed %r from project registry' % proj_name)
        except KeyError:
            raise ProjectNameError('No project named %r.' % proj_name)
        # Update selected if necessary
        if self.selected == proj_name:
            self.selected = None
            for next_name in projects.iterkeys():
                if next_name != proj_name:
                    self.selected = next_name
                    break
        # Save registry
        self.save()
        # TODO: Delete project files
        


def getUserRegistry():
    return Registry(USER_REGISTRY_DIR).load()

def getSystemRegistry():
    return Registry(SYSTEM_REGISTRY_DIR).load()


