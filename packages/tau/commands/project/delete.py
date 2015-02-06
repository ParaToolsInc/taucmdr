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
from docopt import docopt

# TAU modules
from tau import getLogger, EXIT_FAILURE
from error import ProjectNameError, InternalError
from registry import getRegistry


LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Delete a TAU project configuration."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s [options] <name>
  %(command)s -h | --help
  
Subcommand Options:
  --system                   Delete project from TAU installation at %(system_path)r.
  
See 'tau project list' for project names.
"""

HELP = """
%(command)r help page to be written.
"""

def getUsage():
    return USAGE % {'command': COMMAND,
                    'system_path': getRegistry().system.prefix}

def getHelp():
    return HELP % {'command': COMMAND}

def main(argv):
    """
    Program entry point
    """
    # Parse command line arguments
    usage = getUsage()
    args = docopt(usage, argv=argv)
    LOGGER.debug('Arguments: %s' % args)

    system = args['--system']    
    proj_name = args['<name>']
    
    try:
        getRegistry().deleteProject(proj_name, system)
    except ProjectNameError:
        if system and getRegistry().isUserProject(proj_name):
            LOGGER.error("Project %r is a user project.  Try '%s %s'" % 
                         (proj_name, COMMAND, proj_name))
        elif not system and getRegistry().isSystemProject(proj_name):
            LOGGER.error("Project %r is a system project.  Try '%s --system %s'" % 
                         (proj_name, COMMAND, proj_name))
        else:
            LOGGER.error("There is no project named %r. See 'tau project list' for project names." % proj_name)
        return EXIT_FAILURE
    LOGGER.info("Project %r deleted." % proj_name)
    return 0