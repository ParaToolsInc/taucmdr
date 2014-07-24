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
import pickle
import pprint
import taucmd
from taucmd import util

LOGGER = taucmd.getLogger(__name__)

USER_REGISTRY_DIR = taucmd.USER_TAU_DIR

SYSTEM_REGISTRY_DIR = taucmd.SYSTEM_TAU_DIR

class Items(object):
    def __init__(self):
        self.defaults = {}
        self.projects = {}
    
class Registry(object):
    """
    TODO: Docs
    """
    def __init__(self):
        self._tau_version = util.getTauVersion()
        self._populated = False
        self.default_project = None
        self.user = Items()
        self.system = Items()
        self.load()
        
    def __len__(self):
        return len(self.user.projects) + len(self.system.projects)

    def __iter__(self):
        for projects in [self.user.projects, self.system.projects]:
            for proj in projects.itervalues():
                yield proj
              
    def __getitem__(self, key):
        try:
            return self.user.projects[key]
        except KeyError:
            return self.system.projects[key]
        
    def _loadUserItems(self):
        file_path = os.path.join(USER_REGISTRY_DIR, 'registry')
        try:
            with open(file_path, 'rb') as fp:
                self.default_project, self.user = pickle.load(fp)
        except IOError:
            LOGGER.debug('Registry file %r missing, inaccessable, or corrupt.' % file_path)
        else:
            LOGGER.debug('User items loaded from %r' % file_path)
            
    def _saveUserItems(self):
        util.mkdirp(USER_REGISTRY_DIR)
        file_path = os.path.join(USER_REGISTRY_DIR, 'registry')
        with open(file_path, 'wb') as fp:
            pickle.dump((self.default_project, self.user), fp)
        LOGGER.debug('User items written to %r' % file_path)

    def _loadSystemItems(self):
        file_path = os.path.join(SYSTEM_REGISTRY_DIR, 'registry')
        try:
            with open(file_path, 'rb') as fp:
                self.system = pickle.load(fp)
        except IOError:
            LOGGER.debug('Registry file %r missing, inaccessable, or corrupt.' % file_path)
        else:
            LOGGER.debug('System items loaded from %r' % file_path)

    def _saveSystemItems(self):
        try:
            util.mkdirp(SYSTEM_REGISTRY_DIR)
        except OSError as e:
            if e.errno in [errno.EACCESS, errno.EPERM]:
                LOGGER.info("You don't have permissions to create directory %r. System-level changes not saved." % SYSTEM_REGISTRY_DIR)
                return
            else: 
                raise
        file_path = os.path.join(SYSTEM_REGISTRY_DIR, 'registry')
        try:
            with open(file_path, 'wb') as fp:
                pickle.dump(self.system, fp)
        except OSError as e:
            if e.errno in [errno.EACCESS, errno.EPERM]:
                LOGGER.info("You don't have permissions write to %r. System-level changes not saved." % file_path)
        LOGGER.debug('System items written to %r' % file_path)

    def load(self):
        if self._populated:
            LOGGER.debug('Registry already loaded.')
        else:
            self._loadSystemItems()
            self._loadUserItems()
            self._populated = True
        return self

    def save(self):
        if not self._populated:
            LOGGER.debug('Not saving empty registry')
        else:
            self._saveSystemItems()
            self._saveUserItems()
        return self

    def getDefaultProject(self):
        try:
            return self.user.projects[self.default_project]
        except KeyError:
            try:
                return self.system.projects[self.default_project]
            except KeyError:
                return None

    def setDefaultProject(self, proj_name):
        if not (proj_name in self.user.projects or 
                proj_name in self.system.projects):
            raise KeyError
        self.default_project = proj_name
        self.save()
        
    def isUserProject(self, name):
        return name in self.user.projects
    
    def isSystemProject(self, name):
        return name in self.system.projects
        
    def addProject(self, config, system=False):
        """
        Create the project object and update the registry
        """
        LOGGER.debug('Adding project: %s' % config)
        proj = taucmd.project.Project(config)
        proj_name = proj.getName()
        projects = self.system.projects if system else self.user.projects
        if proj_name in projects:
            raise taucmd.project.ProjectNameError('Project %r already exists.' % proj_name)
        projects[proj_name] = proj
        self.save()
        return proj

    def deleteProject(self, proj_name, system=False):
        projects = self.system.projects if system else self.user.projects
        try:
            del projects[proj_name]
        except KeyError:
            raise taucmd.project.ProjectNameError('No project named %r.' % proj_name)
        LOGGER.debug('Removed %r from registry' % proj_name)
        if self.default_project == proj_name:
            self.default_project = None
            LOGGER.info("There is no default project. Use 'tau project default <name>' set the default project.")
        self.save()
        # TODO: Delete project files
        
    def getProjectListing(self):
        empty_msg = "No projects. See 'tau project create'"
        uproj = ['%s [default]' % name if name == self.default_project else name
                     for name in self.user.projects.iterkeys()]
        sproj = ['%s [default]' % name if name == self.default_project else name
                     for name in self.system.projects.iterkeys()]
        ulisting = util.pformatList(uproj, empty_msg=empty_msg, 
                                    title='User Projects (%s)' % USER_REGISTRY_DIR)
        slisting = util.pformatList(sproj, empty_msg=empty_msg, 
                                    title='System Projects (%s)' % SYSTEM_REGISTRY_DIR)
        return '\n'.join([slisting, ulisting])
    
    def setDefaultValue(self, key, val, system=False):
        if system:
            self.system.defaults[key] = val
        else:
            self.user.defaults[key] = val
            
    def getDefaultValue(self, key):
        try:
            return self.user.defaults[key]
        except KeyError:
            return self.system.defaults[key]
        
    def updateDefaultValues(self, d, system=False):
        if system:
            self.system.defaults.update(d)
        else:
            self.user.defaults.update(d)
    
    def getDefaultValueListing(self):
        empty_msg = "No defaults. See 'tau project default'"
        defaults = self.system.defaults.copy()
        defaults.update(self.user.defaults)
        ulisting = util.pformatDict(self.user.defaults, 
                                    title="New Project User Defaults (%r)" % USER_REGISTRY_DIR, 
                                    empty_msg=empty_msg)
        slisting = util.pformatDict(self.system.defaults, 
                                    title="New Project System Defaults (%r)" % SYSTEM_REGISTRY_DIR, 
                                    empty_msg=empty_msg)
        elisting = util.pformatDict(defaults,
                                    title="New Project Effective Defaults",
                                    empty_msg=empty_msg)
        default_proj = util.pformatList([REGISTRY.default_project],
                                        title="Default project")
        return '\n'.join([slisting, ulisting, elisting, default_proj])

REGISTRY = Registry()