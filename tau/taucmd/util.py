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
import re
import subprocess
import errno
import taucmd
import urllib
import tarfile


LOGGER = taucmd.getLogger(__name__)


def mkdirp(path):
    """
    Creates a directory and all its parents.
    """
    try:
        os.makedirs(path)
        LOGGER.debug('Created directory %r' % path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path): pass
        else: raise

        
def which(program):
    def is_exec(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, _ = os.path.split(program)
    if fpath:
        if is_exec(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exec(exe_file):
                return exe_file
    return None


def download(src, dest, stdout=sys.stdout, stderr=sys.stderr):
    LOGGER.debug('Downloading %r to %r' % (src, dest))
    LOGGER.info('Downloading %r' % src)
    mkdirp(os.path.dirname(dest))
    curl = which('curl')
    LOGGER.debug('which curl: %r' % curl)
    wget = which('wget')
    LOGGER.debug('which wget: %r' % wget)
    if curl:
        if subprocess.call([curl, '-L', src, '-o', dest], stdout=stdout, stderr=stderr) != 0:
            LOGGER.debug('curl failed to download %r.' % src)
            raise IOError
    elif wget:
        if subprocess.call([wget, src, '-O', dest], stdout=stdout, stderr=stderr) != 0:
            LOGGER.debug('wget failed to download %r' % src)
            raise IOError
    else:
        # This is usually **much** slower than curl or wget
        def dlProgress(count, blockSize, totalSize):
            stdout.write("% 3.1f%% of %d bytes\r" % (min(100, float(count * blockSize) / totalSize * 100), totalSize))
        urllib.urlretrieve(src, dest, reporthook=dlProgress)

        
    
def extract(tgz, dest):
    with tarfile.open(tgz) as fp:
        LOGGER.debug('Determining top-level directory name in %r' % tgz)
        dirs = [d.name for d in fp.getmembers() if d.type == tarfile.DIRTYPE]
        topdir = min(dirs, key=len)
        LOGGER.debug('Top-level directory in %r is %r' % (tgz, topdir))
        full_dest = os.path.join(dest, topdir)
        LOGGER.debug('Extracting %r to create %r' % (tgz, full_dest))
        LOGGER.info('Extracting %r' % tgz)
        mkdirp(dest)
        fp.extractall(dest)
    assert os.path.isdir(full_dest)
    LOGGER.debug('Created %r' % full_dest)
    return full_dest


_tauVersion = None
def getTauVersion():
    """
    Opens TAU header files to get the TAU version
    """
    def _parseHeadersForVersion(header_files):
        pattern = re.compile('#define\s+TAU_VERSION\s+"(.*)"')
        for hfile in header_files:
            try:
                with open('%s/include/%s' % (taucmd.TAU_MASTER_SRC_DIR, hfile), 'r') as tau_h:
                    for line in tau_h:
                        match = pattern.match(line) 
                        if match:
                            return match.group(1)
            except IOError:
                continue
        return None

    global _tauVersion
    if not _tauVersion:
        _tauVersion = _parseHeadersForVersion(['TAU.h', 'TAU.h.default'])
        if not _tauVersion:
            _tauVersion = '(unknown)'
    return _tauVersion
    

_detectedTarget = None
def detectDefaultTarget():
    """
    Use TAU's archfind script to detect the target architecture
    """
    global _detectedTarget
    if not _detectedTarget:
        cmd = os.path.join(taucmd.TAU_MASTER_SRC_DIR, 'utils', 'archfind')
        _detectedTarget = subprocess.check_output(cmd).strip()
    return _detectedTarget

def pformatDict(d, title=None, empty_msg='No items.', indent=0):
    if title:
        line = '{:=<75}\n'.format('== %s ==' % title)
    else:
        line = '' 
    if len(d):
        longest = max(map(len, d.keys()))
        space = ' '*indent
        items = '\n'.join(['{}{:<{width}} : {}'.format(space, key, val, width=longest)
                           for key, val in sorted(d.iteritems())])
    else:
        items = empty_msg
    return '%(line)s%(items)s' % {'line': line, 'items': items}
    
def pformatList(d, title=None, empty_msg='No items.', indent=0):
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
    
