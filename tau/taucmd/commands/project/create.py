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
import subprocess
import string
import taucmd
import pprint
from textwrap import dedent
from datetime import datetime
from taucmd import util, project, TauConfigurationError, TauError
from taucmd.registry import REGISTRY, SYSTEM_REGISTRY_DIR
from taucmd.project import ProjectNameError
from taucmd.docopt import docopt

LOGGER = taucmd.getLogger(__name__)

SHORT_DESCRIPTION = "Create a new TAU project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s [options]
  %(command)s -h | --help
  
Subcommand Options:
  --name=<name>              Set the project name.
  --makedefault              After creating the project, make it as the default project.
  --system                   Create project in TAU installation at %(global_path)r. 
%(project_options)s
"""

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

def getUsage():
    return USAGE % {'command': COMMAND,
                    'global_path': SYSTEM_REGISTRY_DIR,
                    'project_options': project.getProjectOptions(show_defaults=True)}

def getHelp():
    return HELP


def isValidProjectName(name):
    valid = set(string.digits + string.letters + '-_.')
    return set(name) <= valid


def main(argv):
    """
    Program entry point
    """
    # Parse command line arguments
    usage = getUsage()
    args = docopt(usage, argv=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    system = args['--system']    
    makedefault = args['--makedefault']
    proj_name = args['--name']

    if proj_name and not isValidProjectName(proj_name):
        LOGGER.error('%r is not a valid project name.\n'
                     'Use only letters, numbers, dot (.), dash (-), and underscore (_).' % proj_name)
        return 1
    while not proj_name:
        print 'TAU: Enter project name> ',
        proj_name = sys.stdin.readline().strip()
        if not isValidProjectName(proj_name):
            LOGGER.error('%r is not a valid project name.\n'
                         'Use only letters, numbers, dot (.), dash (-), and underscore (_).' % proj_name)
            proj_name = None
    args['--name'] = proj_name

    config = project.getConfigFromOptions(args)
    LOGGER.debug('Project config: %s' % pprint.pformat(config))
    
    # Show new project settings
    LOGGER.info(util.pformatDict(config, title='New project settings'))
    
    try:
        proj = REGISTRY.addProject(config, system)
    except ProjectNameError:
        raise TauConfigurationError("Project %r already exists. See 'tau project create --help'." % proj_name)
#     except:
#         raise TauError('Failed to create project %r' % proj_name)
#         return 1
    LOGGER.info('Created new project %r.' % proj_name)
    
    if makedefault or not REGISTRY.default_project:
        REGISTRY.setDefaultProject(proj_name)
        LOGGER.info("Project %r set as default.  Use 'tau project default <name>' to choose a different default project." % proj_name)

#     LOGGER.info("""
# Next steps:
# Apply TAU to your application to gather performance data.  You can recompile
# your application with TAU and/or execute your application with TAU.
# 
# To compile with TAU:
#   - Use the 'make' command.  For example, if you normally build your application
#     by typing 'make', instead type 'tau make'.  This works for any make target.
#   - Change your compiler command to 'tau <your_compiler>'.  For example, if your
#     compiler command is 'mpicc', compile your code with 'tau mpicc'.
# 
# To execute with TAU:
#   - Change your application launch command to 'tau <your_application>'.
#     For example, if you launch your application with 'mpirun -np 4 ./foo' instead
#     launch with 'tau mpirun -np 4 ./foo'.
# """ % {'proj_name': proj_name, 'reg_dir': registry.registry_dir})
    return 0
