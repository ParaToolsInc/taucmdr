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
from datetime import datetime
from taucmd import util, project
from taucmd.registry import Registry
from taucmd.docopt import docopt

LOGGER = taucmd.getLogger(__name__)

SHORT_DESCRIPTION = "Create a new named TAU project configuration."

COMMAND = 'tau project create'

USAGE = """
Usage:
  %(command)s [options]
  %(command)s -h | --help
  
Project Options:
  --name=<name>                Set the project name.     
%(project_options)s
"""

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

def getUsage():
    return USAGE % {'command': COMMAND,
                    'project_options': project.getProjectOptions()}

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
    #print usage
    args = docopt(usage, argv=argv)
    LOGGER.debug('Arguments: %s' % args)
    config = project.getConfigFromOptions(args)
    LOGGER.debug('Project config: %s' % pprint.pformat(config))
    
    
    # Get project name
    proj_name = config['name']
    if proj_name and not isValidProjectName(proj_name):
        LOGGER.error('%r is not a valid project name.  Use only letters, numbers, dot (.), dash (-), and underscore (_).' % proj_name)
        return 1
    while not proj_name:
        print 'Enter project name:'
        proj_name = sys.stdin.readline().strip()
        if not isValidProjectName(proj_name):
            print 'ERROR: %r is not a valid project name.  Use only letters, numbers, dot (.), dash (-), and underscore (_).' % proj_name
            proj_name = None
    config['name'] = proj_name
    
    # Set additional project config flags
    config.update({'refresh': True,
                   'tau-version': util.getTauVersion(),
                   'modified': datetime.now()})

    registry = Registry()
    try:
        proj = registry.addProject(config)
    except project.ProjectNameError:
        LOGGER.error("Project %r already exists.  See 'tau project create --help' and maybe use the --name option." % proj_name)
        return 1

    proj_name = proj.getName()
    msg = """
Created a new project named %(proj_name)r
Selected %(proj_name)r as the new default project.  
Use 'tau project select' to select a different project.

Next steps:
Apply TAU to your application to gather performance data.  You can recompile
your application with TAU and/or execute your application with TAU.

To compile with TAU:
  - Use the 'make' command.  For example, if you normally build your application
    by typing 'make', instead type 'tau make'.  This works for any make target.
  - Change your compiler command to 'tau <your_compiler>'.  For example, if your
    compiler command is 'mpicc', compile your code with 'tau mpicc'.

To execute with TAU:
  - Change your application launch command to 'tau <your_application>'.
    For example, if you launch your application with 'mpirun -np 4 ./foo' instead
    launch with 'tau mpirun -np 4 ./foo'.
""" % {'proj_name': proj_name}
    LOGGER.info(msg)
    return 0
