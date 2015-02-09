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

# System modules
import sys
import string
import pprint
from docopt import docopt

# TAU modules
from tau import EXIT_SUCCESS
from logger import getLogger
from util import pformatDict
from project import getProjectOptions, getConfigFromOptions
from error import ProjectNameError
from registry import getRegistry


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Create a new TAU project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s --name=<name> [options]
  %(command)s -h | --help
  
Subcommand Options:
  --default         After creating the project, make it the default project.
  --system          Create project in TAU installation at %(system_path)r. 
%(project_options)s
"""

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

def getUsage():
    return USAGE % {'command': COMMAND,
                    'system_path': getRegistry().system.prefix,
                    'project_options': getProjectOptions(show_defaults=True)}

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
    args = docopt(usage, argv=argv, enable_no_option=True)
    LOGGER.debug('Arguments: %s' % args)
    
    system = args['--system'] 
    default = args['--default']
    name = args['--name']

    if name and not isValidProjectName(name):
        raise ProjectNameError('%r is not a valid project name.' % name,
                               'Use only letters, numbers, dot (.), dash (-), and underscore (_).')

    config = getConfigFromOptions(args, exclude=['--help', '-h', '--system', '--default'])
    config['name'] = name
    LOGGER.info(pformatDict(dict([i for i in config.items() if i[1]]), title='New project settings'))
    LOGGER.debug('Project config: %s' % pprint.pformat(config))
    
    getRegistry().addProject(config, default, system)
    LOGGER.info('Created a new project named %r.' % name)
    return EXIT_SUCCESS
