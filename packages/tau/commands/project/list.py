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
from tau import getLogger
from util import pformatList
from error import ProjectNameError
from registry import getRegistry

LOGGER = getLogger(__name__)

SHORT_DESCRIPTION = "Show TAU project information."

COMMAND = ' '.join(['tau'] + (__name__.split('.')[2:]))

USAGE = """
Usage:
  %(command)s [options] [<name>]
  %(command)s -h | --help
  
Options:
  --system                     Apply change to TAU installation at %(system_path)r. 
""" 

HELP = """
Help page to be written.
"""

def getUsage():
    return USAGE % {'command': COMMAND,
                    'system_path': getRegistry().system.prefix}

def getHelp():
    return HELP

def main(argv):
    """
    Program entry point
    """

    # Parse command line arguments
    usage = getUsage()
    args = docopt(usage, argv=argv)
    LOGGER.debug('Arguments: %s' % args)
    
    system = args['--system']
    name = args['<name>']
    if name:
        projects = getRegistry().system.projects if system else getRegistry().user.projects
        flags = ' --system' if system else ''
        hint = "Try 'tau project list' to see all projects or\n"\
               "'tau project create%(flags)s --name=%(name)s' to create a "\
               "new project named %(name)r" % {'flags': flags, 'name': name}
        try:
            LOGGER.info(projects[name])
        except KeyError:
            raise ProjectNameError('There is no project named %r' % name, hint)
    else:
        selected = getRegistry().getSelectedProject()
        sel_msg = pformatList([selected], empty_msg='No selected project', 
                                   title='Selected Project (%s)' % selected['name'])
        lst_msg = getRegistry().getProjectListing() 
        LOGGER.info('%s\n%s' % (lst_msg, sel_msg))

    return 0
