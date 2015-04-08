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
import os
import sys
import re
import subprocess
import errno
import shutil
import urllib
import tarfile
import pprint
import tempfile
import urlparse
from StringIO import StringIO

# TAU modules
import logger
import environment
from tau.logger import LINE_WIDTH


LOGGER = logger.getLogger(__name__)


def mkdirp(*args):
  """
  Creates a directory and all its parents.
  """
  for path in args:
    try:
      os.makedirs(path)
      LOGGER.debug('Created directory %r' % path)
    except OSError as exc:
      if exc.errno == errno.EEXIST and os.path.isdir(path): pass
      else: raise


def which(program):
  """
  Returns the full path to 'program'
  Searches the system PATH and the current directory
  """
  def is_exec(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
  fpath, _ = os.path.split(program)
  if fpath:
    abs_program = os.path.abspath(program)
    if is_exec(abs_program):
      LOGGER.debug("which(%s) = '%s'" % (program, abs_program))
      return abs_program
  else:
    # System path
    for path in environment.getEnv('PATH').split(os.pathsep):
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exec(exe_file):
        LOGGER.debug("which(%s) = '%s'" % (program, exe_file))
        return exe_file
  LOGGER.debug("which(%s): command not found" % program)
  return None


def download(src, dest):
  """
  Downloads or copies 'src' to 'dest'
  """
  if src.startswith('file://'):
    src = src[6:]
  if os.path.isfile(src):
    LOGGER.debug("Copying '%s' to '%s'" % (src, dest))
    mkdirp(os.path.dirname(dest))
    shutil.copy(src, dest)
    return 0
  else:
    LOGGER.debug("Downloading '%s' to '%s'" % (src, dest))
    LOGGER.info("Downloading '%s'" % src)
    mkdirp(os.path.dirname(dest))
    curl = which('curl')
    LOGGER.debug("which curl: '%s'" % curl)
    wget = which('wget')
    LOGGER.debug("which wget: '%s'" % wget)
    curl_cmd = [curl, '-L', src, '-o', dest] if curl else None
    wget_cmd = [wget, src, '-O', dest] if wget else None
    for cmd in [curl_cmd, wget_cmd]:
      if cmd:
        ret = createSubprocess(cmd, stdout=False)
        if ret != 0:
          LOGGER.warning("%s failed to download '%s'.  Retrying with a different method..." % (cmd[0], src))
        else:
          return ret
    # Fallback: this is usually **much** slower than curl or wget
    def _dlProgress(count, blockSize, totalSize):
      sys.stdout.write("% 3.1f%% of %d bytes\r" % (min(100, float(count * blockSize) / totalSize * 100), totalSize))
    try:
      urllib.urlretrieve(src, dest, reporthook=_dlProgress)
    except Exception as err:
      LOGGER.warning("urllib failed to download '%s': %s" % (src, err))
      raise IOError("Failed to download '%s'" % src)

    
def extract(archive, dest):
  """
  Extracts archive file 'archive' to dest
  """
  with tarfile.open(archive) as fp:
    LOGGER.debug("Determining top-level directory name in '%s'" % archive)
    dirs = [d.name for d in fp.getmembers() if d.type == tarfile.DIRTYPE]
    topdir = min(dirs, key=len)
    LOGGER.debug("Top-level directory in '%s' is '%s'" % (archive, topdir))
    full_dest = os.path.join(dest, topdir)
    LOGGER.debug("Extracting '%s' to create '%s'" % (archive, full_dest))
    LOGGER.info("Extracting '%s'" % archive)
    mkdirp(dest)
    fp.extractall(dest)
  assert os.path.isdir(full_dest)
  LOGGER.debug("Created '%s'" % full_dest)
  return full_dest


def file_accessible(filepath, mode='r'):
   """
   Check if a file exists and is accessible.
   """
   with open(filepath, mode) as _:
     return True
   return False

  
def pformatDict(d, title=None, empty_msg='No items.', indent=0, truncate=False):
  """
  Pretty formater for dictionaries
  """
  if title:
    line = '{:=<75}\n'.format('== %s ==' % title)
  else:
    line = '' 
  if d and len(d):
    longest = max(map(len, d.keys()))
    line_width = logger.LINE_WIDTH - longest - 15
    space = ' '*indent
    def pf(x):
      if truncate and (len(x) > line_width):
        return x[0:line_width] + ' [...]'
      else:
        return str(x)
    items = '\n'.join(['{}{:<{width}} : {}'.format(space, key, pf(val), width=longest)
                       for key, val in sorted(d.iteritems())])
  else:
    items = empty_msg
  return '%(line)s%(items)s' % {'line': line, 'items': items}
    

def pformatList(d, title=None, empty_msg='No items.', indent=0):
  """
  Pretty formatter for lists
  """
  if title:
    line = '{:=<75}\n'.format('== %s ==' % title)
  else:
    line = ''
  if d and len(d):
    space = ' '*indent
    items = '\n'.join(['%s%s' % (space, val) for val in sorted(d)])
  else:
    items = empty_msg
  return '%(line)s%(items)s' % {'line': line, 'items': items}


def createSubprocess(cmd, cwd=None, env=None, fork=False, stdout=True, log=True):
  """
  """
  if not cwd:
    cwd = os.getcwd()
  LOGGER.debug("Creating subprocess: cmd=%s, cwd='%s'\n" % (cmd, cwd))
  # Show what's different in the environment
  if env:
    changed = {}
    for key, val in env.iteritems():
      LOGGER.debug("%s=%s" % (key, ''.join([c for c in val if ord(c) < 128 and ord(c) > 31])))
      try:
        orig = os.environ[key]
      except KeyError:
        changed[key] = val
      else:
        if val != orig:
          changed[key] = val
    LOGGER.info(pformatDict(changed, truncate=True))
  # Show what will be executed
  LOGGER.info(' '.join(cmd))
  pid = os.fork() if fork else 0
  if pid == 0:
    proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.STDOUT)
    stdout, stderr = proc.communicate()
    if log:
      LOGGER.debug(stdout)
    if stdout and (logger.LOG_LEVEL != 'DEBUG'):
      sys.stdout.write(stdout)
    retval = proc.returncode
    LOGGER.debug("%s returned %d" % (cmd, retval))
    return retval
  else:
    return 0
  
def humanReadableSize(num, suffix='B'):
  """
  Returns `num` bytes in human readable format
  """
  for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
    if abs(num) < 1024.0:
      return "%3.1f%s%s" % (num, unit, suffix)
    num /= 1024.0
  return "%.1f%s%s" % (num, 'Yi', suffix)

def parseBoolean(value):
  """
  Parses a value to a literal True/False boolean
  """
  if isinstance(value, bool):
    return value
  elif isinstance(value, int):
    return bool(value)
  elif isinstance(value, str):
    value = value.lower()
    if value in ['1', 't', 'y', 'true', 'yes', 'on']:
      return True
    elif value in ['0', 'f', 'n', 'false', 'no', 'off']:
      return False
  else:
    return None

def isURL(url):
  return bool(len(urlparse.urlparse(url).scheme))

