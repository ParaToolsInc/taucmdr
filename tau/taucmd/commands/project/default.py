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
import pprint
import taucmd
from textwrap import dedent
from datetime import datetime
from taucmd import util, project, TauConfigurationError
from taucmd.registry import REGISTRY, SYSTEM_REGISTRY_DIR
from taucmd.util import pformatDict
from taucmd.docopt import docopt


LOGGER = taucmd.getLogger(__name__)

SHORT_DESCRIPTION = "Set default project and configure defaults for new TAU projects."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s [<name>] 
  %(command)s [options]
  %(command)s -h | --help
  
Subcommand Options:
  --system                     Apply change to TAU installation at %(global_path)r.
%(project_options)s
Use '%(command)s' to see currently configured defaults.
Use '%(command)s <name>' to set <name> as the default project.
Use '%(command)s --opt0 --opt1 ...' to set defaults for new projects.
"""

HELP = """
'%(command)s' page to be written.
""" % {'command': COMMAND}

def getUsage():
    return USAGE % {'command': COMMAND,
                    'global_path': SYSTEM_REGISTRY_DIR,
                    'project_options': project.getProjectOptions(show_defaults=False)}

def getHelp():
    return HELP


def main(argv):
    """
    Program entry point
    """
    # Parse command line arguments
    args = docopt(getUsage(), argv=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    system = args['--system']
    name = args['<name>']
    if name:
        # Set default project
        try:
            REGISTRY.setDefaultProject(name)
        except KeyError:
            LOGGER.error("No project named %r exists.  See 'tau project list' for project names." % name)
            return 1
        LOGGER.info(REGISTRY.getProjectListing())
    else:
        # Set new project defaults
        config = project.getConfigFromOptions(args, apply_defaults=False)
        if len(config):
            LOGGER.debug('Project config: %s' % config)
            REGISTRY.updateDefaultValues(config, system)
            REGISTRY.save()
        LOGGER.info(REGISTRY.getDefaultValueListing())
    return 0
