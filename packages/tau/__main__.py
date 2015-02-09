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
from docopt import docopt

# TAU modules
from tau import MINIMUM_PYTHON_VERSION, EXIT_FAILURE
from logger import getLogger, setLogLevel, LOG_LEVEL
from registry import getRegistry
from commands import getCommands, executeCommand
from commands import build, run, show
from error import UnknownCommandError


USAGE = """
The Tau Performance System
http://tau.uoregon.edu/

Usage:
  tau [options] <command> [<args>...]
  tau -h | --help
  tau --version

Options:
  --project=<name> Use the specified project instead of the default for this run only.
  --log=<level>    Output level, one of CRITICAL, ERRROR, WARNING, INFO, or DEBUG.
  --verbose        Same as --log=DEBUG

Commands:
%(command_descr)s

Aliases:
  <compiler>       A compiler command, e.g. gcc, mpif90, upcc, nvcc, etc. 
                   An alias for 'tau build <compiler>'
  <executable>     A program executable, e.g. ./a.out
                   An alias for 'tau execute <executable>'
  <profile>        View profile data (*.ppk, *.xml, profile.*, etc.) in ParaProf
                   An alias for 'tau show <profile>'
  <trace>          View trace data (*.otf *.slog2, etc.) in Jumpshot
                   An alias for 'tau show <trace>' 

See 'tau <command> --help' for more information on <command>.
"""

LOGGER = getLogger(__name__)


def main():
    """
    Program entry point
    """

    # Check Python version
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        version = '.'.join(map(str, sys.version_info[0:3]))
        expected = '.'.join(map(str, MINIMUM_PYTHON_VERSION))
        LOGGER.error("Your Python version is %s, but %r expects Python %s or later. Please update Python." % 
                     (version, sys.argv[0], expected))
   
    # Parse command line arguments
    usage = USAGE % {'log_default': LOG_LEVEL,
                     'command_descr': getCommands()}
    args = docopt(usage, options_first=True)

    # Set log level
    verbose = args['--verbose']
    log = args['--log']
    if sum([verbose, bool(log)]) > 1:
        LOGGER.error("Please specify either --verbose or --log")
        return EXIT_FAILURE
    if verbose:
        level = 'DEBUG'
    elif log:
        level = log
    else:
        level = 'INFO'
    try:
        setLogLevel(level)
    except ValueError:
        LOGGER.error("Invalid output level: %s" % level)
        return EXIT_FAILURE
    LOGGER.debug('Arguments: %s' % args)
    LOGGER.debug('Verbosity level: %s' % LOG_LEVEL)
    
    # Set selected project
    selected = args['--project']
    if selected:
        if selected in getRegistry():
            getRegistry()._selected_name = selected
        else:
            LOGGER.error("There is no project named %r.  See 'tau project list' for available projects." % selected)
            return EXIT_FAILURE

    # Try to execute as a TAU command
    cmd = args['<command>']
    cmd_args = args['<args>']
    try:
        LOGGER.debug('Executing %r %r' % (cmd, cmd_args))
        return executeCommand([cmd], cmd_args)
    except UnknownCommandError:
        # Not a TAU command, but that's OK
        pass

    # Check shortcuts
    shortcut = None
    if build.isKnownCompiler(cmd):
        shortcut = 'build'
    elif show.isKnownFileFormat(cmd):
        shortcut = 'show'
    elif run.isExecutable(cmd):
        shortcut = 'run'
    if shortcut:
        LOGGER.debug('Trying shortcut %r' % shortcut)
        return executeCommand([shortcut], [cmd] + cmd_args)
    else:
        LOGGER.debug('No shortcut found for %r' % cmd)

    # Not sure what to do at this point, so advise the user and exit
    LOGGER.info("Unknown command.  Calling 'tau help %s' to get advice." % cmd)
    return executeCommand(['help'], [cmd])
    
# Command line execution
if __name__ == "__main__":
    exit(main())
