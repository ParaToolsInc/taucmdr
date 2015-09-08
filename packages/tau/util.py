# -*- coding: utf-8 -*-
#
# Copyright (c) 2015, ParaTools, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# (1) Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
# (2) Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
# (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
"""Utility functions.

Handles system manipulation and status tasks, e.g. subprocess management or file creation.
"""

import os
import sys
import subprocess
import errno
import shutil
import urllib
import tarfile
import urlparse
from tau import logger


LOGGER = logger.get_logger(__name__)


def mkdirp(*args):
    """Creates a directory and all its parents.
    
    Works just like ``mkdir -p``.
    
    Args:
        *args: Paths to create
    """
    for path in args:
        try:
            os.makedirs(path)
            LOGGER.debug('Created directory %r', path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


def which(program):
    """Returns the full path to a program command.
    
    Program must exist and be executable.
    Searches the system PATH and the current directory.
    
    Args:
        program (str): program to find.
        
    Returns:
        str: Full path to program or None if program can't be found.
    """
    if not program:
        return None
    def is_exec(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, _ = os.path.split(program)
    if fpath:
        abs_program = os.path.abspath(program)
        if is_exec(abs_program):
            LOGGER.debug("which(%s) = '%s'", program, abs_program)
            return abs_program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exec(exe_file):
                LOGGER.debug("which(%s) = '%s'", program, exe_file)
                return exe_file
    LOGGER.debug("which(%s): command not found", program)
    return None


def download(src, dest):
    """Downloads or copies files.
    
    `src` may be a file path or URL.  The destination folder will be created 
    if it doesn't exist.  Download is via curl, wget, or Python's urllib as appropriate.
    
    Args:
        src (str): Path or URL to source file.
        dest (str): Path to file copy or download destination.
        
    Raises:
        IOError: File copy or download failed.
    """
    if src.startswith('file://'):
        src = src[6:]
    if os.path.isfile(src):
        LOGGER.debug("Copying '%s' to '%s'", src, dest)
        mkdirp(os.path.dirname(dest))
        shutil.copy(src, dest)
    else:
        LOGGER.debug("Downloading '%s' to '%s'", src, dest)
        LOGGER.info("Downloading '%s'",  src)
        mkdirp(os.path.dirname(dest))
        curl = which('curl')
        wget = which('wget')
        curl_cmd = [curl, '-L', src, '-o', dest] if curl else None
        wget_cmd = [wget, src, '-O', dest] if wget else None
        for cmd in [curl_cmd, wget_cmd]:
            if cmd:
                if create_subprocess(cmd, stdout=False) == 0:
                    return
                LOGGER.warning("%s failed to download '%s'. Retrying with a different method...", cmd[0], src)                    
        # Fallback: this is usually **much** slower than curl or wget
        def _dl_progress(count, block_size, total_size):
            sys.stdout.write("% 3.1f%% of %d bytes\r" % (
                min(100, float(count * block_size) / total_size * 100), total_size))
        try:
            urllib.urlretrieve(src, dest, reporthook=_dl_progress)
        except Exception as err:
            LOGGER.warning("urllib failed to download '%s': %s", src, err)
            raise IOError("Failed to download '%s'" % src)


def archive_toplevel(archive):
    """Returns the name of the top-level directory in an archive.
    
    Assumes that the archive file is rooted in a single top-level directory::
        foo
            /bar
            /baz
    
    The top-level directory here is "foo"
    This routine will return stupid results for archives with multiple top-level elements.
    
    Args:
        archive (str): Path to archive file.
        
    Returns:
        str: Directory name.
    """
    LOGGER.debug("Determining top-level directory name in '%s'", archive)
    with tarfile.open(archive) as fin:
        dirs = [d.name for d in fin.getmembers() if d.type == tarfile.DIRTYPE]
    topdir = min(dirs, key=len)
    LOGGER.debug("Top-level directory in '%s' is '%s'", archive, topdir)
    return topdir


def extract(archive, dest):
    """Extracts archive file to dest.
    
    Supports compressed and uncompressed tar archives. Destination folder will
    be created if it doesn't exist.
    
    Args:
        archive (str): Path to archive file to extract.
        dest (str): Destination folder.
    
    Returns:
        str: Full path to extracted files.
        
    Raises:
        IOError: Failed to extract archive.
    """
    topdir = archive_toplevel(archive)
    full_dest = os.path.join(dest, topdir)
    LOGGER.debug("Extracting '%s' to create '%s'", archive, full_dest)
    LOGGER.info("Extracting '%s'", archive)
    mkdirp(dest)
    with tarfile.open(archive) as fin:
        fin.extractall(dest)
    if not os.path.isdir(full_dest):
        raise IOError("Failed to create '%s' by extracting '%s'" % (full_dest, archive))
    LOGGER.debug("Created '%s'", full_dest)
    return full_dest


def file_accessible(filepath, mode='r'):
    """Check if a file is accessable.
    
    Args:
        filepath (str): Path to file to check.
        mode (str): File access mode to test, e.g. 'r' or 'rw'
    
    Returns:
        True if the file exists and can be opened in the specified mode, False otherwise.
    """
    handle = None
    try:
        handle = open(filepath, mode)
    except:
        return False
    else:
        return True
    finally:
        if handle:
            handle.close()
    return False


def create_subprocess(cmd, cwd=None, env=None, stdout=True, log=True):
    """Create a subprocess.
    
    See :any:`subprocess.Popen`.
    
    Args:
        cmd (list): Command and its command line arguments.
        cwd (str): Change directory to `cwd` if given, otherwise use :any:`os.getcwd`.
        env (dict): Environment variables to set before launching cmd.
        stdout (bool): If True send subprocess stdout and stderr to this processes' stdout.
        log (bool): If True send subprocess stdout and stderr to the debug log.
        
    Returns:
        int: Subprocess return code.
    """
    if not cwd:
        cwd = os.getcwd()
    if not env:
        # Don't accidentally unset all environment variables with an empty dict
        subproc_env = None
    else:
        subproc_env = dict(os.environ)
        for key, val in env.iteritems():
            subproc_env[key] = val
            LOGGER.debug("%s=%s", key, val)
    LOGGER.debug("Creating subprocess: cmd=%s, cwd='%s'\n", cmd, cwd)
    proc = subprocess.Popen(cmd, cwd=cwd, env=subproc_env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            bufsize=1)
    with proc.stdout:
        # Use iter to avoid hidden read-ahead buffer bug in named pipes:
        # http://bugs.python.org/issue3907
        for line in iter(proc.stdout.readline, b''):
            if log:
                LOGGER.debug(line[:-1])
            if stdout:
                print line,
    proc.wait()
    retval = proc.returncode
    LOGGER.debug("%s returned %d", cmd, retval)
    return retval


def human_size(num, suffix='B'):
    """Converts a byte count to human readable units.
    
    Args:
        num (int): Number to convert.
        suffix (str): Unit suffix, e.g. 'B' for bytes.
        
    Returns: 
        str: `num` as a human readable string. 
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def parse_bool(value, additional_true=None, additional_false=None):
    """Parses a value to a boolean value.
    
    If `value` is a string try to interpret it as a bool:
    * ['1', 't', 'y', 'true', 'yes', 'on'] ==> True
    * ['0', 'f', 'n', 'false', 'no', 'off'] ==> False
    Otherwise raise TypeError.
    
    Args:
        value: value to parse to a boolean.
        additional_true (list): optional additional string values that stand for True.
        additional_false (list): optional additional string values that stand for False.
        
    Returns:
        bool: True if  `value` is true, False if `value` is false.
        
    Raises:
        ValueError: `value` does not parse.
    """
    true_values = ['1', 't', 'y', 'true', 'yes', 'on']
    false_values = ['0', 'f', 'n', 'false', 'no', 'off', 'none']
    if additional_true:
        true_values.extend(additional_true)
    if additional_false:
        false_values.extend(additional_false)
    if isinstance(value, basestring):
        value = value.lower()
        if value in true_values:
            return True
        elif value in false_values:
            return False
        else:
            raise TypeError
    return bool(value)

def is_url(url):
    """Check if `url` is a URL.
    
    Args:
        url (str): String to check
        
    Returns:
        bool: True if `url` is a URL, False otherwise.
    """
    return bool(len(urlparse.urlparse(url).scheme))

def camelcase(name):
    """Converts a string to CamelCase.
    
    Args:
        name (str): String to convert.
        
    Returns:
        str: `name` in CamelCase.
    """
    return ''.join(x.capitalize() for x in name.split('_'))
    
