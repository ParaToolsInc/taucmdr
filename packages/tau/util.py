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
import urllib
import tarfile

# TAU modules
from tau import EXIT_FAILURE
from environment import PATH
from logger import getLogger


LOGGER = getLogger(__name__)



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
  Searches environment.PATH and the current directory
  """
  def is_exec(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
  fpath, _ = os.path.split(program)
  if fpath:
    if is_exec(program):
      return program
  else:
    for path in PATH:
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exec(exe_file):
        return exe_file
  return None


def download(src, dest):
  """
  Downloads or copies 'dest' to 'src'
  """
  if src.startswith('file://'):
    try:
      shutil.copy(src, dst)
    except:
      raise IOError("Failed to download '%s'" % src)
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
        ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        if ret != 0:
          LOGGER.warning("%s failed to download '%s'" % (cmd[0], src))
        else:
          return ret
    # Fallback: this is usually **much** slower than curl or wget
    def _dlProgress(count, blockSize, totalSize):
      sys.stdout.write("% 3.1f%% of %d bytes\r" % (min(100, float(count * blockSize) / totalSize * 100), totalSize))
    try:
      urllib.urlretrieve(src, dest, reporthook=_dlProgress)
    except:
      LOGGER.warning("urllib failed to download '%s'" % src)
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


def pformatDict(d, title=None, empty_msg='No items.', indent=0):
  """
  Pretty formater for dictionaries
  """
  if title:
    line = '{:=<75}\n'.format('== %s ==' % title)
  else:
    line = '' 
  if len(d):
    longest = max(map(len, d.keys()))
    space = ' '*indent
    items = '\n'.join(['{}{:<{width}} : {}'.format(space, key, repr(val), width=longest)
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
  if len(d):
    space = ' '*indent
    items = '\n'.join(['%s%s' % (space, val) for val in sorted(d)])
  else:
    items = empty_msg
  return '%(line)s%(items)s' % {'line': line, 'items': items}
    