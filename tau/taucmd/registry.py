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
from taucmd.error import ConfigurationError, InternalError, ProjectNameError

LOGGER = taucmd.getLogger(__name__)

USER_REGISTRY_DIR = taucmd.USER_TAU_DIR

SYSTEM_REGISTRY_DIR = taucmd.SYSTEM_TAU_DIR

class Items(object):
    def __init__(self, path):
        self.path = path
        self.default_name = None
        self.defaults = {}
        self.projects = {}

    def load(self):
        file_path = os.path.join(self.path, 'registry')
        try:
            with open(file_path, 'rb') as fp:
                self.__dict__.update(pickle.load(fp))
        except IOError:
            LOGGER.debug('Registry file %r missing, inaccessable, or corrupt.' % file_path)
        else:
            LOGGER.debug('Registry items loaded from %r' % file_path)
            
    def save(self):
        util.mkdirp(self.path)
        file_path = os.path.join(self.path, 'registry')
        with open(file_path, 'wb') as fp:
            pickle.dump(self.__dict__, fp)
        LOGGER.debug('Registry items written to %r' % file_path)


    
class Registry(object):
    """
    TODO: Docs
    """
    def __init__(self):
        self._tau_version = util.getTauVersion()
        self._populated = False
        self._selected_name = None
        self.user = Items(USER_REGISTRY_DIR)
        self.system = Items(SYSTEM_REGISTRY_DIR)
        self.load()
        
    def __len__(self):
        """The number of projects in the registry"""
        return len(self.user.projects) + len(self.system.projects)

    def __iter__(self):
        """Iterate over projects"""
        for projects in [self.user.projects, self.system.projects]:
            for proj in projects.itervalues():
                yield proj
              
    def __getitem__(self, key):
        """Get projects"""
        try:
            return self.user.projects[key]
        except KeyError:
            return self.system.projects[key]
        
    def load(self):
        """Load the registry from file"""
        if self._populated:
            LOGGER.debug('Registry already loaded.')
        else:
            self.user.load()
            self.system.load()
            self._populated = True

    def save(self):
        """Save the registry to file"""
        if not self._populated:
            LOGGER.debug('Not saving empty registry')
        else:
            self.user.save()
            try:
                self.system.save()
            except OSError as e:
                if e.errno in [errno.EACCESS, errno.EPERM]:
                    LOGGER.info("You don't have permissions write to %r. System-level changes not saved." % self.system.path)
                else:
                    raise

    def getSelectedProject(self):
        """
        Return the selected project
        
        The selected project is chosen in this order: 
        1) The the project specified by the user for this invocation
        2) The user's default project
        3) The system's default project
        4) None
        """
        name = self._selected_name
        if not name:
            name = self.user.default_name
        if not name:
            name = self.system.default_name
        if not name:
            LOGGER.debug('No selected project')
            if not (len(self.system.projects) or len(self.user.projects)):
                hint = "See 'tau project create --help' for help creating a new project."
            else:
                hint="Use 'tau project default <name>' to set a default project, or use the '--project' option."
            raise ConfigurationError("A TAU project has not been selected.  \n%s" % 
                                     self.getProjectListing(), hint)
        LOGGER.debug("Project %r is selected" % name)
        try:
            LOGGER.debug("User projects: %r" % '\n'.join(self.user.projects.keys()))
            proj = self.user.projects[name]
        except KeyError:
            try:
                LOGGER.debug("System projects: %r" % '\n'.join(self.system.projects.keys()))
                proj = self.system.projects[name]
            except:
                raise InternalError("%r is the selected project, but it doesn't exist." % name)
        LOGGER.info('Using TAU project %r' % proj.getName())
        return proj


    def setDefaultProject(self, proj_name, system=False):
        items = self.system if system else self.user
        if not (proj_name in items.projects):
            raise KeyError
        items.default_name = proj_name
        self.save()

    def isUserProject(self, name):
        return name in self.user.projects
    
    def isSystemProject(self, name):
        return name in self.system.projects
        
    def addProject(self, config, default=False, system=False):
        """
        Create the project object and update the registry
        """
        LOGGER.debug('Adding project: %s' % config)
        proj = taucmd.project.Project(config)
        proj_name = proj.getName()
        items = self.system if system else self.user
        if proj_name in items.projects:
            raise ProjectNameError("A project named %r already exists at %r." % (proj_name, items.path))
        if not len(items.projects):
            default = True
        items.projects[proj_name] = proj
        if default:
            items.default_name = proj_name
        self.save()
        return proj

    def deleteProject(self, proj_name, system=False):
        items = self.system if system else self.user
        try:
            del items.projects[proj_name]
        except KeyError:
            raise ProjectNameError('No project named %r.' % proj_name)
        LOGGER.debug('Removed %r from registry' % proj_name)
        if items.default_name == proj_name:
            items.default_name = None
            LOGGER.info("There is no default project. Use 'tau project default <name>' set the default project.")
        self.save()
        # TODO: Delete project files
        
    def getProjectListing(self):
        """
        Return a string listing of all available projects
        """
        empty_msg = "No projects. See 'tau project create --help'"
        uproj = ['%s [default]' % name if name == self.user.default_name else name
                 for name in self.user.projects.iterkeys()]
        sproj = ['%s [default]' % name if name == self.system.default_name else name
                 for name in self.system.projects.iterkeys()]
        ulisting = util.pformatList(uproj, empty_msg=empty_msg, 
                                    title='User Projects (%s)' % self.user.path)
        slisting = util.pformatList(sproj, empty_msg=empty_msg, 
                                    title='System Projects (%s)' % self.system.path)
        return '\n'.join(['', slisting, '', ulisting, ''])
    
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
                                    title="New Project User Defaults (%r)" % self.user.path, 
                                    empty_msg=empty_msg)
        slisting = util.pformatDict(self.system.defaults, 
                                    title="New Project System Defaults (%r)" % self.system.path, 
                                    empty_msg=empty_msg)
        elisting = util.pformatDict(defaults,
                                    title="New Project Effective Defaults",
                                    empty_msg=empty_msg)
        return '\n'.join([slisting, ulisting, elisting])

REGISTRY = Registry()