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

# TAU modules
import cf
import logger
import settings
import error
import controller
import util
import environment
from model.project import Project
from model.target import Target
from model.compiler import Compiler

LOGGER = logger.getLogger(__name__)


class Experiment(controller.Controller):
  """
  Experiment data model controller
  """
  
  attributes = {
    'selection': {
      'model': 'Selection',
      'required': True
    },
    'CC': {
      'model': 'Compiler',
      'required': True
    },
    'CXX': {
      'model': 'Compiler',
      'required': True
    },
    'FC': {
      'model': 'Compiler',
      'required': True
    },
    'tau_path': {
      'type': 'string',
    },
    'tau_makefile': {
      'type': 'string',
    },
    'tau_build_env': {
      'type': 'string',
    },
    'tau_run_env': {
      'type': 'string',
    },
    'trials': {
      'collection': 'Trial',
      'via': 'experiment'
    },
  }

  @classmethod
  def configure(cls, selected, compiler_cmd):
    """
    Installs all software required to perform the experiment and configures
    environment variables
    """
    selected.populate()
    target = selected['target']
    application = selected['application']
    measurement = selected['measurement']
    compiler = Compiler.identify(target, compiler_cmd)
    
    # See if we've already configured this experiment
    found = cls.one(keys={'selection': selected.eid, compiler['role']: compiler.eid})
    if found:
      LOGGER.debug("Found experiment: %s" % found)
      return found
    
    LOGGER.debug("Experiment not found, creating new experiment")
    fields = {'selection': selected.eid}
    
    # Discover and configure compilers
    compilers = {compiler['role']: compiler}
    for info in cf.compiler.getCompilerFamily(compiler['command']):
      if info.role != compiler['role']:
        try:
          other = Compiler.identify(target, info.command)
        except error.ConfigurationError:
          continue
        if os.path.dirname(other['path']) == os.path.dirname(compiler['path']):
          compilers[other['role']] = other
    try:
      cc = compilers['CC']
    except KeyError:
      raise error.ConfigurationError("C compiler matching '%s' not found" % compiler_cmd)
    try:
      cxx = compilers['CXX']
    except KeyError:
      raise error.ConfigurationError("C++ compiler matching '%s' not found" % compiler_cmd)
    try:
      fc = compilers['FC']
    except KeyError:
      raise error.ConfigurationError("Fortran compiler matching '%s' not found" % compiler_cmd)
    
    fields['CC'] = cc.eid
    fields['CXX'] = cxx.eid
    fields['FC'] = fc.eid

    # Create a place to store project files and settings
    prefix = selected['project']['prefix']
    try:
      util.mkdirp(prefix)
    except:
      raise error.ConfigurationError('Cannot create directory %r' % prefix, 
                                     'Check that you have `write` access')

    # Configure/build/install TAU if not already done
    tau_config = cf.tau.initialize(prefix, target['tau'], arch=target['host_arch'], 
                                   cc=cc, cxx=cxx, fc=fc)
    tau_path, tau_makefile = tau_config
    fields['tau_path'] = tau_path
    fields['tau_makefile'] = tau_makefile
    
    # Configure TAU compiler options
    tau_options = ['-optRevert']
    if logger.LOG_LEVEL == 'DEBUG':
        tau_options.append('-optVerbose')
    else:
        tau_options.append('-optQuiet')
    if measurement['source_inst']:
      tau_options.append('-optPDTInst')
    comp_inst_options = {'always': '-optCompInst',
                         'fallback': '-optRevert',
                         'never': '-optNoCompInst'}
    tau_options.append(comp_inst_options[measurement['compiler_inst']])
 
    # Configure TAU build environment
    tau_build_env = {}
    tau_build_env['TAU_OPTIONS'] = ' '.join(tau_options)
    tau_build_env['TAU_MAKEFILE'] = tau_makefile
    fields['tau_build_env'] = tau_build_env
    
    # Configure TAU runtime environment
    tau_run_env = {}
    if measurement['profile']:
      tau_run_env['TAU_PROFILE'] = '1'
    if measurement['trace']:
      tau_run_env['TAU_TRACE'] = '1'
    if measurement['sample']:
      tau_run_env['TAU_SAMPLE'] = '1'
    if measurement['callpath'] > 0:
      tau_run_env['TAU_CALLPATH'] = '1'
      tau_run_env['TAU_CALLPATH_DEPTH'] = str(measurement['callpath'])
    if measurement['memory_usage']:
      tau_run_env['TAU_TRACK_HEAP'] = '1'
    fields['tau_run_env'] = tau_run_env
    
    return Experiment.create(fields)
