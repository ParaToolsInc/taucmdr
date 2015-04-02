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
import shutil
import platform

# TAU modules
import cf
import logger
import util
import error
import environment


LOGGER = logger.getLogger(__name__)

DEFAULT_SOURCE = {None: 'http://tau.uoregon.edu/pdt.tgz',
                  # Why isn't this called pdt-x86_64.tgz ?? "lite" tells me nothing
                  'x86_64': 'http://tau.uoregon.edu/pdt_lite.tgz'}

COMMANDS = [
    'cparse',
    'cxxparse',
    'edg33-upcparse',
    'edg44-c-roseparse',
    'edg44-cxx-roseparse',
    'edg44-upcparse',
    'edgcpfe',
    'f90fe',
    'f90parse',
    'f95parse',
    'gfparse',
    'pdbcomment',
    'pdbconv',
    'pdbhtml',
    'pdbmerge',
    'pdbstmt',
    'pdbtree',
    'pdtf90disp',
    'pdtflint',
    'pebil.static',
    'roseparse',
    'smaqao',
    'taucpdisp',
    'tau_instrumentor',
    'upcparse',
    'xmlgen'
]


class Pdt(object):
  """
  Encapsulates a PDT installation
  """
  def __init__(self, prefix, cxx, src, arch):
    if src.lower() == 'download':
      try:
        src = DEFAULT_SOURCE[arch]
      except KeyError:
        src = DEFAULT_SOURCE[None]
    self.prefix = prefix
    self.cxx = cxx
    self.src = src
    self.arch = arch
    compiler_prefix = str(cxx.eid) if cxx else 'unknown'
    self.src_prefix = os.path.join(prefix, 'src')
    self.pdt_prefix = os.path.join(prefix, 'pdt', compiler_prefix)
    self.include_path = os.path.join(self.pdt_prefix, 'include')
    self.arch_path = os.path.join(self.pdt_prefix, arch)
    self.bin_path = os.path.join(self.arch_path, 'bin')
    self.lib_path = os.path.join(self.arch_path, 'lib')

  def verify(self):
    """
    Returns true if if there is a working PDT installation at `prefix` with a
    directory named `arch` containing `bin` and `lib` directories or 
    raises a ConfigurationError describing why that installation is broken.
    """
    LOGGER.debug("Checking PDT installation at '%s' targeting arch '%s'" % (self.pdt_prefix, self.arch))    
    if not os.path.exists(self.pdt_prefix):
      raise error.ConfigurationError("'%s' does not exist" % self.pdt_prefix)
  
    # Check for all commands
    for cmd in COMMANDS:
      path = os.path.join(self.bin_path, cmd)
      if not os.path.exists(path):
        raise error.ConfigurationError("'%s' is missing" % path)
      if not os.access(path, os.X_OK):
        raise error.ConfigurationError("'%s' exists but is not executable" % path)
    
    LOGGER.debug("PDT installation at '%s' is valid" % self.pdt_prefix)
    return True

  def install(self, force_reinstall=False):
    """
    TODO: Docs
    """
    LOGGER.debug("Initializing PDT at '%s' from '%s' with arch=%s" % 
                 (self.pdt_prefix, self.src, self.arch))
    
    # Check if the installation is already initialized
    if not force_reinstall:
      try:
        return self.verify()
      except error.ConfigurationError, err:
        LOGGER.debug(err)
    
    # Control build output
    LOGGER.info('Starting PDT installation')
    with logger.logging_streams():
      # Download, unpack, or copy PDT source code
      dst = os.path.join(self.src_prefix, os.path.basename(self.src))
      try:
        util.download(self.src, dst)
        srcdir = util.extract(dst, self.src_prefix)
      except IOError:
        raise error.ConfigurationError("Cannot acquire source file '%s'" % self.src,
                                       "Check that the file is accessable")
      finally:
        try: os.remove(dst)
        except: pass

      if not self.cxx:
        compiler_flag = ''
      else:
        family_flags = {'system': '',
                        'GNU': '-GNU',
                        'Intel': '-icpc',
                        'PGI': '-pgCC'}
        try:
          compiler_flag = family_flags[self.cxx['family']]
        except KeyError:
          LOGGER.warning("PDT has no compiler flag for '%s'.  Using defaults." % self.cxx['family'])

      try:
        # Configure
        prefix_flag = '-prefix=%s' % self.pdt_prefix
        cmd = ['./configure', prefix_flag, compiler_flag]
        LOGGER.info("Configuring PDT...")
        if util.createSubprocess(cmd, cwd=srcdir):
          raise error.SoftwarePackageError('PDT configure failed')
  
        # Build
        cmd = ['make', '-j4']
        LOGGER.info("Compiling PDT...")
        if util.createSubprocess(cmd, cwd=srcdir):
          raise error.SoftwarePackageError('PDT compilation failed.')

        # Install
        cmd = ['make', 'install']
        LOGGER.info("Installing PDT...")
        if util.createSubprocess(cmd, cwd=srcdir):
          raise error.SoftwarePackageError('PDT installation failed.')
      except:
        LOGGER.info("PDT installation failed, cleaning up")
        shutil.rmtree(self.pdt_prefix, ignore_errors=True)
      finally:
        # Always clean up PDT source
        LOGGER.debug('Deleting %r' % srcdir)
        shutil.rmtree(srcdir, ignore_errors=True)
         
    # Verify the new installation and return
    LOGGER.info('PDT installation complete')
    return self.verify()

  def applyCompiletimeConfig(self, opts, env):
    """
    TODO: Docs
    """
    env['PATH'] = os.pathsep.join([self.bin_path, env.get('PATH')])

  def getRuntimeConfig(self, opts, env):
    """
    TODO: Docs
    """
    pass

    