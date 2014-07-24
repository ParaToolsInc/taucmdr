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

import sys
import taucmd
import traceback
from pkgutil import walk_packages
from taucmd import commands
from taucmd import util
from taucmd.commands import build, run, show
from taucmd.docopt import docopt

USAGE = """
The Tau Performance System (%(tau_version)s)
http://tau.uoregon.edu/

Usage:
  tau [options] <command> [<args>...]
  tau -h | --help
  tau --version

Options:
  --log=<level>    Output level.  [default: %(log_default)s]
                   <level> can be CRITICAL, ERRROR, WARNING, INFO, or DEBUG

Commands:
%(command_descr)s

Shortcuts:  
  <compiler>       A compiler command, e.g. gcc, mpif90, upcc, nvcc, etc. 
                   An alias for 'tau build <compiler>'
  <executable>     A program executable, e.g. ./a.out
                   An alias for 'tau execute <executable>'
  <profile>        View profile data (*.ppk, *.xml, profile.*, etc.) in ParaProf
                   An alias for 'tau show <profile>'
  <trace>          View trace data (*.otf *.slog2, etc.) in Jumpshot
                   An alias for 'tau show <trace>' 

See 'tau <command> --help' for more information on a specific command.
"""

LOGGER = taucmd.getLogger(__name__)



def getCommands():
    """
    Builds listing of command names with short description
    """
    parts = []
    mod_names = [n for _, n, _ in walk_packages(commands.__path__, commands.__name__+'.') if n.count('.') == 2]
    for module in mod_names:
        __import__(module)
        descr = sys.modules[module].SHORT_DESCRIPTION
        name = '{0:<15}'.format(module.split('.')[-1])
        parts.append('  %s  %s' % (name, descr))
    return '\n'.join(parts)


def executeCommand(cmd, cmd_args):
    cmd_module = 'taucmd.commands.%s' % cmd
    try:
        __import__(cmd_module)
        LOGGER.debug('Recognized %r as tau subcommand' % cmd)
    except ImportError:
        # It wasn't a tau command, but that's OK
        LOGGER.debug('%r not recognized as a TAU command' % cmd)
        return None
    return sys.modules[cmd_module].main([cmd] + cmd_args)

def main():
    """
    Program entry point
    """

    # Set the default exception handler
    sys.excepthook = taucmd.excepthook

    # Check Python version
    if sys.version_info < taucmd.EXPECT_PYTHON_VERSION:
        version = '.'.join(map(str, sys.version_info[0:3]))
        expected = '.'.join(map(str, taucmd.EXPECT_PYTHON_VERSION))
        LOGGER.warning("Your Python version is %s, but 'tau' expects Python %s or later.  Please update Python." % (version, expected))

    # Get tau version
    tau_version = util.getTauVersion()

    # Parse command line arguments
    usage = USAGE % {'tau_version': tau_version,
                     'log_default': taucmd.LOG_LEVEL,
                     'command_descr': getCommands()}
    args = docopt(usage, version=tau_version, options_first=True)

    # Set log level
    taucmd.setLogLevel(args['--log'])
    LOGGER.debug('Arguments: %s' % args)
    LOGGER.debug('Verbosity level: %s' % taucmd.LOG_LEVEL)

    # Try to execute as a tau command
    cmd = args['<command>']
    cmd_args = args['<args>']
    retval = executeCommand(cmd, cmd_args)
    if retval != None:
        return retval

    # Check shortcuts
    shortcut = None
    if build.isKnownCompiler(cmd):
        shortcut = 'build'
    elif show.isKnownFileFormat(cmd):
        shortcut = 'show'
    elif run.isExecutable(cmd):
        shortcut = 'run'
    if shortcut:
        retval = executeCommand(shortcut, [cmd] + cmd_args)
        if retval != None:
            return retval

    # Not sure what to do at this point, so advise the user and exit
    LOGGER.debug("Can't classify %r.  Calling 'tau help' to get advice." % cmd)
    return executeCommand('help', [cmd]) 

# Command line execution
if __name__ == "__main__":
    exit(main())
