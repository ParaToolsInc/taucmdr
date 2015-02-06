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
import sys
import errno
import pickle
import tau
from tau import util
from tau import HELP_CONTACT, USER_PREFIX, SYSTEM_PREFIX
from tau.error import ConfigurationError, InternalError
from tau.error import ProjectNameError, RegistryError

LOGGER = tau.getLogger(__name__)


class Registry(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.default_name = None
        self.locked = False
        self.defaults = {}
        self.projects = {}
        self._registry_file = os.path.join(prefix, 'registry')
        
    def load(self):
        if not os.path.exists(self._registry_file):
            LOGGER.debug("Registry file %r doesn't exist yet." % self._registry_file)
        else:
            try:
                with open(self._registry_file, 'rb') as fp:
                    self.__dict__.update(pickle.load(fp))
            except IOError:
                raise RegistryError('Registry file %r inaccessable or corrupt.' % self._registry_file)
            except:
                raise RegistryError('%r raised while loading registry file %r.' % (sys.exc_info()[1], self._registry_file),
                                    'The registry may be corrupt.  Contact %s for help.' % HELP_CONTACT)
            else:
                LOGGER.debug('Registry loaded from %r' % self._registry_file)
            
    def save(self):
        util.mkdirp(self.prefix)
        file_path = os.path.join(self.prefix, 'registry')
        with open(file_path, 'wb') as fp:
            pickle.dump(self.__dict__, fp)
        LOGGER.debug('Registry written to %r' % file_path)
    
    def isReadable(self):
        test_file = os.path.join(self.prefix, 'test')
        try:
            with open(test_file, 'r') as fp:
                fp.readline()
            os.remove(test_file)
        except IOError:
            return False
        except:
            raise InternalError('Unexpected %r in isReadable' % (sys.exc_info(),))
        else:
            return True
        
        
    def isWritable(self):
        test_file = os.path.join(self.prefix, 'test')
        try:
            with open(test_file, 'w') as fp:
                fp.write('x')
            os.remove(test_file)
        except IOError:
            return False
        except:
            raise InternalError('Unexpected %r in isWritable' % (sys.exc_info(),))
        else:
            return True
        


class GlobalRegistry(object):
    """
    TODO: Docs
    """
    def __init__(self):
        self._populated = False
        self._selected_name = None
        self.user = Registry(USER_PREFIX)
        self.system = Registry(SYSTEM_PREFIX)
        self.load()
        
    def __len__(self):
        """The number of projects in the registry"""
        return len(self.user.projects) + len(self.system.projects)

    def __iter__(self):
        """Iterate over projects"""
        for projects in [self.user.projects, self.system.projects]:
            for i in projects.iteritems():
                yield i
                
    def __contains__(self, item):
        return item in self.user.projects or item in self.system.projects
              
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
                if e.errno in [errno.EACCES, errno.EPERM]:
                    LOGGER.info("You don't have permissions write to %r. System-level changes not saved." % self.system.prefix)
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
            raise ConfigurationError("A TAU project has not been selected.\n%s" % 
                                     self.getProjectListing(), hint)
        LOGGER.debug("Project %r is selected" % name)
        try:
            LOGGER.debug("User projects: %s" % ', '.join(self.user.projects.keys()))
            proj = self.user.projects[name]
        except KeyError:
            try:
                LOGGER.debug("System projects: %s" % ', '.join(self.system.projects.keys()))
                proj = self.system.projects[name]
            except:
                raise InternalError("%r is the selected project, but it doesn't exist." % name)
        LOGGER.info('Using TAU project %r' % proj.getName())
        return proj

    def setDefaultProject(self, proj_name, system=False):
        reg = self.system if system else self.user
        if not (proj_name in reg.projects):
            raise KeyError
        reg.default_name = proj_name
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
        reg = self.system if system else self.user
        proj = tau.project.Project(config, reg)
        proj_name = proj.getName()
        
        if proj_name in reg.projects:
            raise ProjectNameError("A project named %r already exists at %r." % (proj_name, reg.prefix))
        if not len(reg.projects):
            default = True
        reg.projects[proj_name] = proj
        if default:
            reg.default_name = proj_name
            LOGGER.info("%r is now the new %s default project" % (proj_name, "system" if system else "user"))
        else:
            LOGGER.info("Use 'tau project default %s' to select a default project." % proj_name)
        self.save()
        return proj

    def deleteProject(self, proj_name, system=False):
        reg = self.system if system else self.user
        try:
            del reg.projects[proj_name]
        except KeyError:
            raise ProjectNameError('No project named %r.' % proj_name)
        else:
            LOGGER.debug('Removed %r from registry' % proj_name)
        if reg.default_name == proj_name:
            LOGGER.info("Default project deleted.")
            if len(reg.projects):
                reg.default_name = reg.projects.itervalues().next().config['name']
                LOGGER.info("Selected %r to be the new default project" % reg.default_name)
            else:
                reg.default_name = None
                LOGGER.info("There is no default project. See 'tau project default'.")
        self.save()
        # TODO: Delete project files?
        
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
                                    title='User Projects (%s)' % self.user.prefix)
        slisting = util.pformatList(sproj, empty_msg=empty_msg, 
                                    title='System Projects (%s)' % self.system.prefix)
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
                                    title="New Project User Defaults (%r)" % self.user.prefix, 
                                    empty_msg=empty_msg)
        slisting = util.pformatDict(self.system.defaults, 
                                    title="New Project System Defaults (%r)" % self.system.prefix, 
                                    empty_msg=empty_msg)
        elisting = util.pformatDict(defaults,
                                    title="New Project Effective Defaults",
                                    empty_msg=empty_msg)
        return '\n'.join([slisting, ulisting, elisting])

# Instantiate the global registry
REGISTRY = GlobalRegistry()